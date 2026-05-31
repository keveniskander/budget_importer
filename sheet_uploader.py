import gspread
from google.oauth2.service_account import Credentials
import json

# =========================
# AUTH SETUP
# =========================
SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]

creds = Credentials.from_service_account_file(
    "credentials.json",
    scopes=SCOPES
)

client = gspread.authorize(creds)

# =========================
# CONNECT TO SHEET
# =========================
SPREADSHEET_NAME = "Budget Tracking Tool - V5 - KEVEN"
WORKSHEET_NAME = "Expenses"

spreadsheet = client.open(SPREADSHEET_NAME)
worksheet = spreadsheet.worksheet(WORKSHEET_NAME)

print(f"Connected to: {spreadsheet.title} → {worksheet.title}")

# =========================
# LOAD TRANSACTIONS
# =========================
transactions = []

with open("transactions.txt", "r", encoding="utf-8") as f:
    for line in f:
        date, merchant, category, amount = line.strip().split(" | ")

        transactions.append({
            "date": date,
            "merchant": merchant,
            "category": category,
            "amount": float(amount)
        })

# =========================
# GET EXISTING DATA (FOR DUPLICATES)
# =========================
existing_rows = worksheet.get_all_values()
existing_keys = set()

# IMPORTANT: skip header row only (row 1)
for row in existing_rows[1:]:
    if len(row) < 4:
        continue

    date = row[0]      # B
    merchant = row[1]  # C
    amount = row[2]    # D

    key = f"{date}_{merchant}_{amount}"
    existing_keys.add(key)

# =========================
# BUILD NEW ROWS
# =========================
new_rows = []

for t in transactions:
    key = f"{t['date']}_{t['merchant']}_{t['amount']}"

    if key in existing_keys:
        continue

    new_rows.append([
        t["date"],        # B
        t["merchant"],    # C
        t["amount"],      # D
        t["category"],    # E
        ""                # F Notes
    ])

# =========================
# APPEND TO SHEET
# =========================
if new_rows:
    worksheet.append_rows(new_rows, value_input_option="USER_ENTERED")
    print(f"Added {len(new_rows)} new transactions.")
else:
    print("No new transactions to add (all duplicates).")

# =========================
# 🧠 AUTO LEARNING FROM SHEET
# =========================
LEARNED_FILE = "learned_categories.json"

def sync_learning_from_sheet():
    try:
        with open(LEARNED_FILE, "r", encoding="utf-8") as f:
            learned = json.load(f)
    except:
        learned = {}

    rows = worksheet.get_all_values()
    data_rows = rows[1:]  # skip header

    new_learned = 0

    for row in data_rows:
        if len(row) < 5:
            continue

        merchant = row[1].strip()   # Column C
        category = row[3].strip()   # Column E

        if not merchant or category in ["", "Other"]:
            continue

        if merchant not in learned or learned[merchant] != category:
            learned[merchant] = category
            new_learned += 1

    with open(LEARNED_FILE, "w", encoding="utf-8") as f:
        json.dump(learned, f, indent=2)

    print(f"[LEARNING] Updated {new_learned} merchant rules from sheet")

# RUN LEARNING AFTER UPLOAD
sync_learning_from_sheet()