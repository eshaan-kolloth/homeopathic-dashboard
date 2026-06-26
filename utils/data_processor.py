import pandas as pd

# ──────────────────────────────────────────────────────────────────────────────
# ROW CLASSIFICATION
#
# A homeopathic company "Daily Report" sheet mixes three kinds of rows:
#   1. CATEGORY HEADERS  — e.g. "Office Sales Kerala", "ADS" — these are
#      section subtotals, not people.
#   2. PERSON / CHANNEL ROWS — e.g. "FEMINA PA", "AMAZON," — the actual
#      data we want to rank and analyse.
#   3. SUMMARY / FINANCIAL ROWS — e.g. "Total Sales", "GST Collected",
#      "Total To month" — these are never people and must never appear
#      in a leaderboard or zero-sales alert.
#
# Everything below works off explicit keyword sets so it's robust even if
# row positions shift between weekly exports.
# ──────────────────────────────────────────────────────────────────────────────

CATEGORY_HEADER_KEYWORDS = [
    "office sales kerala",
    "office sales interstate",
    "company direct sales",
    "ads",
    "exhibition sales",
    "e commerce sales",
    "e-commerce sales",
    "ecommerce sales",
    "medical store",
    "medical store / shops",
]

# Rows that are never people — totals, summaries, financial breakdown.
EXCLUDE_KEYWORDS = [
    "total sales",
    "sales return",
    "cancellation",
    "net sales",
    "total to month",
    "total year to date",
    "agri sale",
    "otc",
    "precription",
    "prescription",
    "total coupon",
    "discount",
    "gst collected",
    "transporation",
    "transportation",
    "total bill amount",
    "daily report",
]

CATEGORY_FOR_ROW = {
    "femina pa": "Office Sales Kerala", "lincy": "Office Sales Kerala",
    "mareena": "Office Sales Kerala", "laya": "Office Sales Kerala",
    "aswathy raju": "Office Sales Kerala", "sajitha": "Office Sales Kerala",
    "krishnapirya": "Office Sales Kerala",
    "aparna": "Office Sales Interstate", "sneha": "Office Sales Interstate",
    "indrakumar": "Office Sales Interstate",
    "ajaykumar": "Company Direct Sales", "saju tr": "Company Direct Sales",
    "follow up  golitha": "Company Direct Sales", "follow up golitha": "Company Direct Sales",
    "anwar": "ADS", "anithakumar": "ADS", "dr arun": "ADS", "binoy": "ADS",
    "gangadharan": "ADS", "muneer": "ADS", "nikhil": "ADS", "nezia": "ADS",
    "noby": "ADS", "shylaja": "ADS", "selvaraj": "ADS", "satheesh": "ADS",
    "amazon,": "E-commerce", "amazon": "E-commerce", "flipkart": "E-commerce",
    "jio": "E-commerce", "web": "E-commerce",
    "medical store / shops": "Medical Store",
}


def _is_category_header(label: str) -> bool:
    label_l = label.strip().lower()
    return any(kw in label_l for kw in CATEGORY_HEADER_KEYWORDS)


def _is_excluded(label: str) -> bool:
    label_l = label.strip().lower()
    if label_l in ("0", "", "nan"):
        return True
    return any(kw in label_l for kw in EXCLUDE_KEYWORDS)


def _is_person_row(label: str) -> bool:
    """A row counts as a person/channel row if it's not blank, not a
    category header, and not an excluded summary/financial row."""
    label_l = label.strip().lower()
    if label_l in ("0", "", "nan"):
        return False
    if _is_category_header(label_l):
        return False
    if _is_excluded(label_l):
        return False
    return True


def get_category_for_person(name: str) -> str:
    """Looks up which sales category a person/channel belongs to."""
    return CATEGORY_FOR_ROW.get(str(name).strip().lower(), "Other")


# ──────────────────────────────────────────────────────────────────────────────
# CORE EXTRACTORS
# ──────────────────────────────────────────────────────────────────────────────

def get_person_rows(df: pd.DataFrame) -> pd.DataFrame:
    """Returns only the rows that represent an actual salesperson or
    sales channel (e.g. AMAZON), with category headers and summary
    rows stripped out."""
    labels = df.iloc[:, 0].astype(str)
    mask = labels.apply(_is_person_row)
    return df[mask].copy()


def get_category_rows(df: pd.DataFrame) -> pd.DataFrame:
    """Returns only the category header / subtotal rows."""
    labels = df.iloc[:, 0].astype(str)
    mask = labels.apply(_is_category_header)
    return df[mask].copy()


def get_summary_row(df: pd.DataFrame, keyword: str) -> pd.Series:
    """Finds a specific summary row (e.g. 'total sales', 'gst collected')
    by keyword and returns its numeric values across all date columns.
    Returns an empty Series if not found."""
    labels = df.iloc[:, 0].astype(str).str.strip().str.lower()
    match = df[labels.str.contains(keyword, na=False)]
    if match.empty:
        return pd.Series(dtype=float)
    row = match.iloc[0, 1:]
    return pd.to_numeric(row, errors='coerce').fillna(0)


def extract_summary(df):
    """
    Extracts key summary statistics from the cleaned DataFrame,
    computed only from actual person/channel rows (category headers
    and summary rows excluded).
    """
    person_df = get_person_rows(df)
    numeric_df = person_df.iloc[:, 1:].apply(pd.to_numeric, errors='coerce').fillna(0)

    summary = {}
    summary['total_sales'] = numeric_df.sum().sum()
    summary['daily_totals'] = numeric_df.sum(axis=0).tolist()
    summary['row_totals'] = numeric_df.sum(axis=1).tolist()
    summary['max_value'] = numeric_df.max().max() if not numeric_df.empty else 0
    nonzero = numeric_df[numeric_df > 0]
    summary['min_nonzero'] = nonzero.min().min() if not nonzero.empty else 0
    return summary


def get_salesperson_totals(df: pd.DataFrame) -> pd.DataFrame:
    """
    Returns a DataFrame with columns ['Salesperson', 'Category', 'Total'],
    built only from real person/channel rows — category headers and
    summary rows (Total Sales, GST, MTD, YTD, etc.) are excluded.
    """
    person_df = get_person_rows(df)
    if person_df.empty:
        return pd.DataFrame(columns=['Salesperson', 'Category', 'Total'])

    numeric_cols = person_df.columns[1:]
    person_df = person_df.copy()
    person_df['Total'] = (
        person_df[numeric_cols]
        .apply(pd.to_numeric, errors='coerce')
        .fillna(0)
        .sum(axis=1)
    )

    result = person_df[[person_df.columns[0], 'Total']].copy()
    result.columns = ['Salesperson', 'Total']
    result['Category'] = result['Salesperson'].apply(get_category_for_person)
    result = result[result['Total'] > 0]
    result = result.sort_values('Total', ascending=False).reset_index(drop=True)
    return result[['Salesperson', 'Category', 'Total']]


def get_zero_sales(df: pd.DataFrame) -> list:
    """
    Returns list of salesperson/channel names who had zero sales on at
    least one day. Category headers and summary rows are excluded.
    """
    person_df = get_person_rows(df)
    zero_list = []
    for _, row in person_df.iterrows():
        name = str(row.iloc[0]).strip()
        values = pd.to_numeric(row.iloc[1:], errors='coerce').fillna(0)
        if (values == 0).any():
            zero_list.append(name)
    return zero_list


def get_daily_totals(df: pd.DataFrame) -> pd.Series:
    """
    Returns true daily totals (one value per date column), computed by
    summing only real person/channel rows. This is what should be
    plotted on the trend chart and used for MTD/YTD/today-vs-yesterday.
    """
    person_df = get_person_rows(df)
    numeric_df = person_df.iloc[:, 1:].apply(pd.to_numeric, errors='coerce').fillna(0)
    return numeric_df.sum(axis=0)


def get_category_totals(df: pd.DataFrame) -> pd.DataFrame:
    """
    Returns a DataFrame with columns ['Category', 'Total'] — total sales
    per category (Kerala, Interstate, ADS, E-commerce, etc.), computed
    from the real person/channel rows grouped by category.
    """
    totals = get_salesperson_totals(df)
    if totals.empty:
        return pd.DataFrame(columns=['Category', 'Total'])
    grouped = totals.groupby('Category', as_index=False)['Total'].sum()
    return grouped.sort_values('Total', ascending=False).reset_index(drop=True)


def get_mtd_total(df: pd.DataFrame) -> float:
    """Returns the latest 'Total To month' value if present, else falls
    back to the sum of daily totals."""
    row = get_summary_row(df, "total to month")
    if not row.empty:
        return float(row.iloc[-1])
    return float(get_daily_totals(df).sum())


def get_ytd_total(df: pd.DataFrame) -> float:
    """Returns the latest 'Total Year To Date' value if present, else 0."""
    row = get_summary_row(df, "total year to date")
    if not row.empty:
        return float(row.iloc[-1])
    return 0.0


def get_data_summary_for_ai(df: pd.DataFrame) -> str:
    """
    Creates a text summary of the data to send to Groq AI as context.
    Only real salesperson/channel totals are included — category
    headers and financial summary rows are described separately so
    the AI doesn't confuse a subtotal with a person.
    """
    salesperson_totals = get_salesperson_totals(df)
    category_totals = get_category_totals(df)
    daily_totals = get_daily_totals(df)
    mtd = get_mtd_total(df)
    ytd = get_ytd_total(df)

    lines = []
    lines.append("=== SALES DATA SUMMARY ===")
    lines.append(f"Total rows of data: {len(df)}")
    lines.append(f"Total columns: {len(df.columns)}")
    lines.append(f"Total Sales (sum of all days): ₹{daily_totals.sum():,.0f}")
    lines.append(f"Month To Date (MTD): ₹{mtd:,.0f}")
    lines.append(f"Year To Date (YTD): ₹{ytd:,.0f}")
    lines.append("")
    lines.append("=== CATEGORY TOTALS ===")
    for _, row in category_totals.iterrows():
        lines.append(f"{row['Category']}: ₹{row['Total']:,.0f}")
    lines.append("")
    lines.append("=== SALESPERSON / CHANNEL TOTALS ===")
    for _, row in salesperson_totals.iterrows():
        lines.append(f"{row['Salesperson']} ({row['Category']}): ₹{row['Total']:,.0f}")
    lines.append("")
    lines.append("=== DAILY TOTALS ===")
    for i, val in enumerate(daily_totals):
        lines.append(f"Day {i + 1}: ₹{val:,.0f}")

    zero_list = get_zero_sales(df)
    if zero_list:
        lines.append("")
        lines.append("=== ZERO-SALES DAYS DETECTED ===")
        lines.append(", ".join(zero_list))

    return "\n".join(lines)