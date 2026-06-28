import pandas as pd
import openpyxl
from io import BytesIO


# ─────────────────────────────────────────────────────────────────
# KEYWORDS
# ─────────────────────────────────────────────────────────────────
CATEGORY_KEYWORDS = [
    "office sales kerala", "office sales interstate",
    "company direct sales", "company direct",
    "ads", "exhibition sales", "exhibition",
    "e-commerce sales", "e-commerce", "ecommerce",
    "medical store / shops", "medical store", "shops",
]

SKIP_KEYWORDS = [
    "total sales", "net sales", "sales return", "cancellation",
    "total to month", "total year", "year to date",
    "gst", "transportation", "transporation",
    "bill amount", "bill count", "daily report",
    "agri sale", "aqua", "dairy", "general medicine",
    "met live stock", "pet", "poultry",
    "precription", "prescription",
    "discount", "coupon", "bank balance", "cash balance",
    "otc", "total coupon",
]

PERSON_CATEGORY_MAP = {
    "femina pa":         "Office Sales Kerala",
    "lincy":             "Office Sales Kerala",
    "mareena":           "Office Sales Kerala",
    "laya":              "Office Sales Kerala",
    "aswathy raju":      "Office Sales Kerala",
    "sajitha":           "Office Sales Kerala",
    "krishnapirya":      "Office Sales Kerala",
    "aparna":            "Office Sales Interstate",
    "sneha":             "Office Sales Interstate",
    "indrakumar":        "Office Sales Interstate",
    "ajaykumar":         "Company Direct Sales",
    "saju tr":           "Company Direct Sales",
    "follow up  golitha":"Company Direct Sales",
    "follow up golitha": "Company Direct Sales",
    "anwar":             "ADS",
    "anithakumar":       "ADS",
    "dr arun":           "ADS",
    "binoy":             "ADS",
    "gangadharan":       "ADS",
    "muneer":            "ADS",
    "nikhil":            "ADS",
    "nezia":             "ADS",
    "noby":              "ADS",
    "shylaja":           "ADS",
    "selvaraj":          "ADS",
    "satheesh":          "ADS",
    "amazon,":           "E-commerce",
    "amazon":            "E-commerce",
    "flipkart":          "E-commerce",
    "jio":               "E-commerce",
    "web":               "E-commerce",
    "medical store / shops": "Medical Store",
}

SUMMARY_KEYWORDS = [
    "total sales", "net sales", "sales return", "cancellation",
    "total to month", "total year", "year to date",
    "gst", "transportation", "transporation",
    "bill amount", "bill count", "daily report",
    "agri sale", "aqua", "dairy", "general medicine",
    "met live stock", "pet", "poultry",
    "precription", "prescription",
    "discount", "coupon", "bank balance", "cash balance",
    "otc",
]


def _is_category(val: str) -> bool:
    v = val.strip().lower()
    return any(kw in v for kw in CATEGORY_KEYWORDS)


def _is_skip(val: str) -> bool:
    v = val.strip().lower()
    if v in ("0", "", "nan", "none"):
        return True
    return any(kw in v for kw in SKIP_KEYWORDS)


def _is_person(val: str) -> bool:
    v = val.strip().lower()
    if v in ("0", "", "nan", "none"):
        return False
    if _is_category(v):
        return False
    if _is_skip(v):
        return False
    return True


def _find_date_row(df_raw: pd.DataFrame):
    """
    Scans the raw DataFrame to find which row index contains the date headers.
    Returns (row_index, list_of_date_strings).
    Tries to parse each cell as a date and picks the row with most valid dates.
    """
    best_row = 1
    best_count = 0

    for i in range(min(5, len(df_raw))):
        row = df_raw.iloc[i]
        count = 0
        for cell in row[1:]:
            if cell is None or str(cell).strip() in ("0", "", "nan", "None"):
                continue
            try:
                pd.to_datetime(str(cell))
                count += 1
            except Exception:
                pass
        if count > best_count:
            best_count = count
            best_row = i

    return best_row


def get_clean_dataframe(file) -> pd.DataFrame:
    """
    Smart loader:
    1. Reads raw Excel with no headers
    2. Finds the date row automatically
    3. Sets date strings as column headers
    4. Keeps only real salesperson rows
    5. Returns clean DataFrame with columns: [Name, date1, date2, ...]
    """
    file_bytes = file.read() if hasattr(file, "read") else file
    file_like  = BytesIO(file_bytes)

    # Read raw — no header, everything as-is
    df_raw = pd.read_excel(file_like, header=None, dtype=str)
    df_raw = df_raw.fillna("0")

    # Find the date row
    date_row_idx = _find_date_row(df_raw)
    date_row     = df_raw.iloc[date_row_idx]

    # Build column names: first col = "Name", rest = date strings
    col_names = ["Name"]
    for cell in date_row[1:]:
        cell_str = str(cell).strip()
        if cell_str in ("0", "", "nan", "None"):
            col_names.append(cell_str)
            continue
        try:
            dt = pd.to_datetime(cell_str)
            col_names.append(dt.strftime("%d %b %Y"))
        except Exception:
            col_names.append(cell_str)

    # Trim columns to match col_names length
    df_raw = df_raw.iloc[:, :len(col_names)]
    df_raw.columns = col_names

    # Skip rows up to and including the date row
    df_data = df_raw.iloc[date_row_idx + 1:].copy().reset_index(drop=True)

    # Keep only person rows
    person_rows = []
    for _, row in df_data.iterrows():
        name = str(row["Name"]).strip()
        if _is_person(name):
            person_rows.append(row)

    if not person_rows:
        # Fallback — return everything
        return df_raw

    df_clean = pd.DataFrame(person_rows).reset_index(drop=True)

    # Convert all date columns to numeric
    date_cols = [c for c in df_clean.columns if c != "Name"]
    for col in date_cols:
        df_clean[col] = pd.to_numeric(df_clean[col], errors="coerce").fillna(0)

    return df_clean


def get_raw_dataframe(file) -> pd.DataFrame:
    """
    Returns the completely raw DataFrame — all rows including summaries.
    Used for MTD, YTD, bank balance, cash balance lookups.
    """
    file_bytes = file.read() if hasattr(file, "read") else file
    file_like  = BytesIO(file_bytes)
    df_raw = pd.read_excel(file_like, header=None, dtype=str)
    df_raw = df_raw.fillna("0")
    return df_raw


def get_summary_value(raw_df: pd.DataFrame, keyword: str, col_idx: int = -1) -> float:
    """
    Searches the raw DataFrame for a row containing keyword,
    returns the numeric value at col_idx (default = last column).
    """
    for i, row in raw_df.iterrows():
        cell = str(row.iloc[0]).strip().lower()
        if keyword.lower() in cell:
            try:
                vals = pd.to_numeric(row.iloc[1:], errors="coerce").fillna(0)
                if col_idx == -1:
                    non_zero = vals[vals > 0]
                    return float(non_zero.iloc[-1]) if not non_zero.empty else 0.0
                return float(vals.iloc[col_idx])
            except Exception:
                return 0.0
    return 0.0


def get_category_for_person(name: str) -> str:
    return PERSON_CATEGORY_MAP.get(str(name).strip().lower(), "Other")