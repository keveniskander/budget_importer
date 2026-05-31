# =========================
# PARSE TRANSACTIONS (ROBUST MULTI-BANK)
# =========================

lines = text.split("\n")

transactions = []

buffer = None

def is_date_line(line):
    return bool(re.match(r"^[A-Za-z]{3}\.\s*\d{1,2}", line))

for line in lines:
    line = line.strip()

    if not line:
        continue

    # skip headers
    if "DESCRIPTION" in line or "AMOUNT" in line or "Card number" in line:
        continue

    # skip noise lines
    if "TRANS POSTING" in line:
        continue

    # detect new transaction start
    if re.match(r"^[A-Za-z]{3}\.\s*\d{1,2}", line):

        # save previous transaction
        if buffer:
            transactions.append(buffer)

        buffer = {
            "raw": line
        }

    else:
        # continuation of previous line (merchant spills into next line)
        if buffer:
            buffer["raw"] += " " + line

# append last
if buffer:
    transactions.append(buffer)


# =========================
# EXTRACT FIELDS
# =========================

final_transactions = []

pattern = r"([A-Za-z]{3}\.\s*\d{1,2})\s+([A-Za-z]{3}\.\s*\d{1,2})\s+(.+?)\s+(\d+\.\d{2})"

for t in transactions:

    match = re.search(pattern, t["raw"])

    if not match:
        continue

    posted_date, transaction_date, description, amount = match.groups()

    merchant = clean_merchant(description)

    # handle credits (CR)
    is_credit = "CR" in t["raw"]
    amount = float(amount)

    if is_credit:
        amount = -amount

    category = categorize(merchant)

    final_transactions.append({
        "date": convert_date(transaction_date),
        "merchant": merchant,
        "category": category,
        "amount": amount
    })