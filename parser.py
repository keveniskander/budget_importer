import pdfplumber
import re
import json
import os
import sys
from datetime import datetime

# =========================
# INPUT FILE
# =========================
if len(sys.argv) < 2:
    print("Usage: python parser.py <pdf_file_path>")
    sys.exit(1)

PDF_FILE = sys.argv[1]

if not os.path.exists(PDF_FILE):
    print(f"File not found: {PDF_FILE}")
    sys.exit(1)

LEARNED_FILE = "learned_categories.json"

# =========================
# CATEGORY RULES
# =========================
RULES = {
    "Groceries": ["SUPER C", "IGA", "METRO", "MAXI", "COSTCO", "MARCHE"],
    "Public transportation": ["STM", "COMMUNAUTO", "BIXI", "UBER"],
    "Restaurant": ["CAFE", "MOISSON", "RESTAURANT", "DUNYA", "BARRANCO"],
    "Entertainment": ["APPLE", "STEAM", "NETFLIX", "SPOTIFY"],
    "Gas": ["SHELL", "ESSO", "PETRO"],
    "Medical": ["PHARMAPRIX", "JEAN COUTU"],
}

# =========================
# LOAD LEARNED DATA
# =========================
if os.path.exists(LEARNED_FILE):
    with open(LEARNED_FILE, "r", encoding="utf-8") as f:
        LEARNED = json.load(f)
else:
    LEARNED = {}

def save_learned():
    with open(LEARNED_FILE, "w", encoding="utf-8") as f:
        json.dump(LEARNED, f, indent=2)

# =========================
# CATEGORY FUNCTION
# =========================
def categorize(merchant):
    m = merchant.upper()

    if merchant in LEARNED:
        return LEARNED[merchant]

    for category, keywords in RULES.items():
        for k in keywords:
            if k in m:
                LEARNED[merchant] = category
                return category

    LEARNED[merchant] = "Other"
    return "Other"

# =========================
# DATE CONVERTER (AMEX FORMAT)
# =========================
def convert_date(may_day):
    year = 2026

    # handles both "May2" and "Apr. 10"
    day = int(re.findall(r"\d+", may_day)[0])

    return datetime(year, 5, day).strftime("%Y-%m-%d")

# =========================
# CLEAN MERCHANT
# =========================
def clean_merchant(text):
    noise = ["MONTREAL", "QC", "QUEBEC", "ON", "TORONTO", "WA", "SWE"]
    parts = text.split()
    cleaned = [p for p in parts if p not in noise]
    return " ".join(cleaned).title()

# =========================
# EXTRACT PDF
# =========================
text = ""

with pdfplumber.open(PDF_FILE) as pdf:
    for page in pdf.pages:
        page_text = page.extract_text()
        if page_text:
            text += page_text + "\n"

with open("statement_raw.txt", "w", encoding="utf-8") as f:
    f.write(text)

print("Raw text saved")

# =========================
# SPLIT LINES (IMPORTANT FIX)
# =========================
lines = text.split("\n")

# =========================
# BUILD TRANSACTIONS (MULTI-LINE SAFE)
# =========================
transactions = []
buffer = None

for line in lines:
    line = line.strip()

    if not line:
        continue

    # skip headers
    if "DESCRIPTION" in line or "AMOUNT" in line or "Card number" in line:
        continue

    if "TRANS POSTING" in line:
        continue

    # detect new transaction start (Apr. 10, May. 2, etc.)
    if re.match(r"^[A-Za-z]{3}\.?\s*\d{1,2}", line):

        if buffer:
            transactions.append(buffer)

        buffer = {
            "raw": line
        }

    else:
        if buffer:
            buffer["raw"] += " " + line

if buffer:
    transactions.append(buffer)

# =========================
# EXTRACT FINAL FIELDS
# =========================
final_transactions = []

pattern = r"([A-Za-z]{3}\.?\s*\d{1,2})\s+([A-Za-z]{3}\.?\s*\d{1,2})\s+(.+?)\s+(\d+\.\d{2})"

for t in transactions:

    match = re.search(pattern, t["raw"])
    if not match:
        continue

    posted_date, transaction_date, description, amount = match.groups()

    merchant = clean_merchant(description)

    amount = float(amount)

    # handle credits (CR)
    if "CR" in t["raw"]:
        amount = -amount

    category = categorize(merchant)

    final_transactions.append({
        "date": convert_date(transaction_date),
        "merchant": merchant,
        "category": category,
        "amount": amount
    })

# =========================
# OUTPUT
# =========================
for t in final_transactions[:10]:
    print(t)

with open("transactions.txt", "w", encoding="utf-8") as f:
    for t in final_transactions:
        f.write(f"{t['date']} | {t['merchant']} | {t['category']} | {t['amount']}\n")

save_learned()

print("Transactions saved + learning updated")