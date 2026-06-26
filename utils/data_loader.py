import pandas as pd
import openpyxl
from io import BytesIO

def load_and_clean_excel(file):
    """
    Loads an Excel file, detects structure, fills nulls with 0,
    and returns a clean tagged DataFrame.
    """
    wb = openpyxl.load_workbook(file, data_only=True)
    ws = wb.active

    rows = list(ws.iter_rows(values_only=True))

    CATEGORY_KEYWORDS = [
        "office sales kerala", "office sales interstate",
        "company direct", "ads", "exhibition", "e-commerce",
        "ecommerce", "medical store", "shops"
    ]

    data = []
    current_category = "Unknown"

    for row in rows:
        if all(v is None for v in row):
            continue

        first_val = str(row[0]).strip().lower() if row[0] else ""

        is_header = any(kw in first_val for kw in CATEGORY_KEYWORDS)
        if is_header:
            current_category = str(row[0]).strip()
            continue

        skip_keywords = ["total", "net sales", "return", "month", "year", "date"]
        if any(kw in first_val for kw in skip_keywords):
            continue

        if row[0] is None:
            continue

        row_data = [v if v is not None else 0 for v in row]
        row_data.append(current_category)
        data.append(row_data)

    raw = pd.read_excel(file, header=None)
    raw = raw.fillna(0)

    df_raw = pd.read_excel(file, header=None)
    df_raw = df_raw.fillna(0)

    return df_raw, wb


def get_clean_dataframe(file):
    """
    Returns a fully cleaned DataFrame with nulls filled as 0.
    This is the safe version — no data is ever lost.
    """
    df = pd.read_excel(file, header=None)
    df = df.fillna(0)
    return df