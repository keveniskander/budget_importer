import pdfplumber
import re
import json
import os
import sys
from datetime import datetime

# =========================
# INPUT
# =========================
if len(sys.argv) < 2:
    print("Usage: python parser.py <pdf_file_path>")
    sys.exit(1)

PDF_FILE = sys.argv[1]

if not os.path.exists(PDF_FILE):
    print("File not found:", PDF_FILE)
    sys.exit(1)

# =========================
# FILES
# =========================
LEARNED_FILE = "learned_categories.json"
OUTPUT_FILE = "transactions.txt"

# =========================
# RULES
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
# LOAD LEARNING
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
# CATEGORY ENGINE
# =========================
def categorize(merchant):
    m = merchant.upper()

    if merchant in LEARNED:
        return LEARNED[merchant]

    for cat, keywords in RULES.items():
        for k in keywords:
            if k in m:
                LEARNED[merchant] = cat
                return cat

    LEARNED[merchant] = "Other"
    return "Other"

# =========================
# DATE
# =========================
def convert_date(raw):
    if not raw:
        return None

    months = {
        "JAN": 1, "FEB": 2, "MAR": 3, "APR": 4,
        "MAY": 5, "JUN": 6, "JUL": 7, "AUG": 8,
        "SEP": 9, "OCT": 10, "NOV": 11, "DEC": 12
    }

    raw = raw.upper().replace(".", "").strip()

    match = re.match(r"([A-Z]{3})(\d{1,2})", raw)

    if match:
        mon, day = match.groups()
        month = months.get(mon[:3], None)

        if month is None:
            return None

        return datetime(2026, month, int(day)).strftime("%Y-%m-%d")

    # fallback: handle "May 2"
    parts = raw.split()

    if len(parts) >= 2:
        mon = parts[0][:3]
        day = re.findall(r"\d+", parts[1])[0]

        month = months.get(mon, None)

        if month is None:
            return None

        return datetime(2026, month, int(day)).strftime("%Y-%m-%d")

    return None

# =========================
# CLEAN MERCHANT
# =========================
def clean_merchant(text):
    noise = ["MONTREAL", "QC", "QUEBEC", "ON", "TORONTO", "WA", "SWE"]
    return " ".join([w for w in text.split() if w not in noise]).title()

# =========================
# EXTRACT TEXT
# =========================
def extract_text(pdf_path):
    text = ""
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            t = page.extract_text()
            if t:
                text += t + "\n"
    return text

# =========================
# AMEX PARSER (FIXED)
# =========================
def parse_amex(text):
    pattern = re.compile(
        r"^([A-Za-z]{3}\d{1,2})\s+([A-Za-z]{3}\d{1,2})\s+(.+)\s+(-?\d+\.\d{2})$"
    )

    results = []

    for line in text.split("\n"):
        match = pattern.search(line.strip())
        if not match:
            continue

        d1, d2, merchant, amount = match.groups()

        merchant = clean_merchant(merchant)

        results.append({
            "date": convert_date(d2),
            "merchant": merchant,
            "category": categorize(merchant),
            "amount": float(amount)
        })

    return results

# =========================
# BMO PARSER
# =========================
def parse_bmo(text):
    pattern = re.compile(
        r"^([A-Za-z]{3}\.?\s*\d{1,2})\s+([A-Za-z]{3}\.?\s*\d{1,2})\s+(.+?)\s+(-?\d+\.\d{2})"
    )

    results = []

    for line in text.split("\n"):
        match = pattern.search(line.strip())
        if not match:
            continue

        d1, d2, merchant, amount = match.groups()

        merchant = clean_merchant(merchant)

        results.append({
            "date": convert_date(d2),
            "merchant": merchant,
            "category": categorize(merchant),
            "amount": float(amount)
        })

    return results

# =========================
# BANK DETECTION
# =========================
def detect_bank(text):
    t = text.upper()

    if "AMERICAN EXPRESS" in t or "AMEX" in t:
        return "AMEX"

    if "TRANS POSTING" in t:
        return "BMO"

    return "AMEX"

# =========================
# MAIN
# =========================
text = extract_text(PDF_FILE)

bank = detect_bank(text)
print("Detected bank:", bank)

if bank == "AMEX":
    transactions = parse_amex(text)
else:
    transactions = parse_bmo(text)

# =========================
# SAVE
# =========================
with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
    for t in transactions:
        f.write(f"{t['date']} | {t['merchant']} | {t['category']} | {t['amount']}\n")

save_learned()

print(f"Done: {len(transactions)} transactions")