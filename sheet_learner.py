import gspread
from google.oauth2.service_account import Credentials
import json

# =========================
# CONFIG
# =========================
SPREADSHEET_NAME = "Budget Tracking Tool - V5 - KEVEN"
WORKSHEET_NAME = "Expenses"
LEARNED_FILE = "learned_categories.json"

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]

# =========================
# AUTH
# =========================
creds = Credentials.from_service_account_file(
    "credentials.json",
    scopes=SCOPES
)

client = gspread.authorize(creds)
sheet = client.open(SPREADSHEET_NAME).worksheet(WORKSHEET_NAME)

# =========================
# LOAD EXISTING LEARNING
# =========================
try:
    with open(LEARNED_FILE, "r", encoding="utf-8") as f:
        learned = json.load(f)
except:
    learned = {}

# =========================
# READ SHEET
# =========================
rows = sheet.get_all_values()

# skip header row (row 1)
data_rows = rows[1:]

new_learned = 0

for row in data_rows:
    if len(row) < 5:
        continue

    # IMPORTANT: correct mapping based on your sheet
    date = row[1]        # B
    merchant = row[2]    # C
    amount = row[3]      # D
    category = row[4]    # E

    if not merchant:
        continue

    category = category.strip() if category else ""

    # ignore empty / unhelpful labels
    if category in ["", "Other"]:
        continue

    merchant = merchant.strip()

    # learn only if new or updated
    if merchant not in learned or learned[merchant] != category:
        learned[merchant] = category
        new_learned += 1

# =========================
# SAVE
# =========================
with open(LEARNED_FILE, "w", encoding="utf-8") as f:
    json.dump(learned, f, indent=2)

print(f"Learned {new_learned} new mappings from Google Sheets")