import pdfplumber
import re
import json
import os
import sys
from datetime import datetime

# =========================
# INPUT FILE (NO HARDCODING)
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
# CATEGORY RULES (FAST PATH)
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

# =========================
# SAVE LEARNING
# =========================
def save_learned():
    with open(LEARNED_FILE, "w", encoding="utf-8") as f:
        json.dump(LEARNED, f, indent=2)

# =========================
# CATEGORY FUNCTION
# =========================
def categorize(merchant):
    m = merchant.upper()

    # 1. MEMORY FIRST
    if merchant in LEARNED:
        return LEARNED[merchant]

    # 2. RULE MATCH
    for category, keywords in RULES.items():
        for k in keywords:
            if k in m:
                LEARNED[merchant] = category
                return category

    # 3. DEFAULT
    LEARNED[merchant] = "Other"
    return "Other"

# =========================
# DATE CONVERTER
# =========================
def convert_date(may_day):
    year = 2026
    month = 5
    day = int(re.findall(r"\d+", may_day)[0])
    return datetime(year, month, day).strftime("%Y-%m-%d")

# =========================
# CLEAN MERCHANT
# =========================
def clean_merchant(text):
    noise = ["MONTREAL", "QC", "QUEBEC"]
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
# PARSE TRANSACTIONS
# =========================
pattern = r"(May\d+)\s+(May\d+)\s+(.+?)\s+(\d+\.\d{2})"
matches = re.findall(pattern, text)

transactions = []

for posted_date, transaction_date, description, amount in matches:

    merchant = clean_merchant(description)
    category = categorize(merchant)

    transactions.append({
        "date": convert_date(transaction_date),
        "merchant": merchant,
        "category": category,
        "amount": float(amount)
    })

# =========================
# OUTPUT
# =========================
for t in transactions[:10]:
    print(t)

with open("transactions.txt", "w", encoding="utf-8") as f:
    for t in transactions:
        f.write(f"{t['date']} | {t['merchant']} | {t['category']} | {t['amount']}\n")

# SAVE LEARNING DATA
save_learned()

print("Transactions saved + learning updated")