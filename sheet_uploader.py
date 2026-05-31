import gspread
from google.oauth2.service_account import Credentials

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
# format:
# date | merchant | category | amount
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

# skip header rows (your data starts at row 8)
for row in existing_rows[7:]:
    if len(row) >= 4:
        date = row[0]
        merchant = row[1]
        amount = row[2]

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
        t["date"],        # Column B
        t["merchant"],    # Column C
        t["amount"],      # Column D
        t["category"],    # Column E
        ""                # Column F (Notes)
    ])


# =========================
# APPEND TO SHEET
# =========================
if new_rows:
    worksheet.append_rows(new_rows, value_input_option="USER_ENTERED")
    print(f"Added {len(new_rows)} new transactions.")
else:
    print("No new transactions to add (all duplicates).")