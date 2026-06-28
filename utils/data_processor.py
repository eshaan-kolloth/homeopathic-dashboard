import pandas as pd
from utils.data_loader import get_category_for_person, get_summary_value

# ─────────────────────────────────────────────────────────────────
# CORE PROCESSORS — all work on the CLEAN df from data_loader
# ─────────────────────────────────────────────────────────────────

def get_date_columns(df: pd.DataFrame) -> list:
    """Returns list of date column names (everything except 'Name')."""
    return [c for c in df.columns if c != "Name"]


def get_salesperson_totals(df: pd.DataFrame) -> pd.DataFrame:
    """
    Returns DataFrame with columns [Salesperson, Category, Total].
    Only real person rows — no summaries, no category headers.
    """
    date_cols = get_date_columns(df)
    if not date_cols:
        return pd.DataFrame(columns=["Salesperson", "Category", "Total"])

    result_rows = []
    for _, row in df.iterrows():
        name = str(row["Name"]).strip()
        total = pd.to_numeric(
            pd.Series([row[c] for c in date_cols]), errors="coerce"
        ).fillna(0).sum()

        category = get_category_for_person(name)
        result_rows.append({
            "Salesperson": name,
            "Category":    category,
            "Total":       float(total),
        })

    result = pd.DataFrame(result_rows)
    result = result[result["Total"] > 0]
    result = result.sort_values("Total", ascending=False).reset_index(drop=True)
    return result[["Salesperson", "Category", "Total"]]


def get_category_totals(df: pd.DataFrame) -> pd.DataFrame:
    """Returns [Category, Total] grouped."""
    totals = get_salesperson_totals(df)
    if totals.empty:
        return pd.DataFrame(columns=["Category", "Total"])
    grouped = totals.groupby("Category", as_index=False)["Total"].sum()
    return grouped.sort_values("Total", ascending=False).reset_index(drop=True)


def get_daily_totals(df: pd.DataFrame) -> pd.Series:
    """Returns sum per date column — the real daily revenue."""
    date_cols = get_date_columns(df)
    if not date_cols:
        return pd.Series(dtype=float)
    numeric = df[date_cols].apply(pd.to_numeric, errors="coerce").fillna(0)
    return numeric.sum(axis=0)


def get_zero_sales(df: pd.DataFrame) -> list:
    """Returns list of salesperson names with at least one zero-sales day."""
    date_cols = get_date_columns(df)
    zero_list = []
    for _, row in df.iterrows():
        name = str(row["Name"]).strip()
        values = pd.to_numeric(
            pd.Series([row[c] for c in date_cols]), errors="coerce"
        ).fillna(0)
        if (values == 0).any():
            zero_list.append(name)
    return zero_list


def get_mtd_total(raw_df: pd.DataFrame) -> float:
    """Gets Month-To-Date from the raw (unfiltered) DataFrame."""
    val = get_summary_value(raw_df, "total to month")
    if val > 0:
        return val
    # Fallback — sum all numeric in the last column
    try:
        last_col = raw_df.iloc[:, -1]
        numeric  = pd.to_numeric(last_col, errors="coerce").fillna(0)
        return float(numeric.sum())
    except Exception:
        return 0.0


def get_ytd_total(raw_df: pd.DataFrame) -> float:
    """Gets Year-To-Date from the raw (unfiltered) DataFrame."""
    val = get_summary_value(raw_df, "total year to date")
    if val > 0:
        return val
    val = get_summary_value(raw_df, "year to date")
    return val


def get_bank_balance(raw_df: pd.DataFrame) -> float:
    return get_summary_value(raw_df, "bank balance total")


def get_cash_balance(raw_df: pd.DataFrame) -> float:
    return get_summary_value(raw_df, "cash balance total")


def get_bill_count(raw_df: pd.DataFrame) -> str:
    val = get_summary_value(raw_df, "bill count")
    if val > 0:
        return f"{int(val):,}"
    return "—"


def get_returns_total(raw_df: pd.DataFrame, lo: int, hi: int) -> float:
    """Gets sales returns for the selected date range."""
    for i, row in raw_df.iterrows():
        cell = str(row.iloc[0]).strip().lower()
        if "sales return" in cell or "cancellation" in cell:
            try:
                vals = pd.to_numeric(row.iloc[1:], errors="coerce").fillna(0)
                return float(vals.iloc[lo - 1: hi].sum())
            except Exception:
                return 0.0
    return 0.0


def get_product_category_totals(raw_df: pd.DataFrame, lo: int, hi: int) -> dict:
    """
    Extracts product category rows (AGRI, AQUA, DAIRY etc.)
    and returns {label: total} dict.
    """
    PRODUCT_ROWS = {
        "AGRI SALE":             ("🌾", "Agriculture",  "#10B981"),
        "AQUA":                  ("🐟", "Aquaculture",  "#06B6D4"),
        "DAIRY":                 ("🥛", "Dairy",        "#60A5FA"),
        "GENERAL MEDICINE":      ("💊", "General Med",  "#8B5CF6"),
        "MET LIVE STOCK":        ("🐄", "Livestock",    "#F59E0B"),
        "PET":                   ("🐾", "Pet Care",     "#EC4899"),
        "POULTRY":               ("🐔", "Poultry",      "#F97316"),
        "PRECRIPTION - GENERAL": ("📋", "Rx General",   "#3B82F6"),
        "PRECRIPTION - ANN":     ("📋", "Rx Ann",       "#A78BFA"),
        "PRECRIPTION - A K":     ("📋", "Rx AK",        "#34D399"),
    }

    result = {}
    for i, row in raw_df.iterrows():
        cell = str(row.iloc[0]).strip().upper()
        for key, meta in PRODUCT_ROWS.items():
            if cell == key:
                try:
                    vals = pd.to_numeric(row.iloc[1:], errors="coerce").fillna(0)
                    total = float(vals.iloc[lo - 1: hi].sum())
                    if total > 0:
                        result[key] = {
                            "emoji": meta[0],
                            "label": meta[1],
                            "color": meta[2],
                            "total": total,
                        }
                except Exception:
                    pass
    return result


def get_data_summary_for_ai(df: pd.DataFrame) -> str:
    """Creates a plain text summary for the AI model."""
    salesperson_totals = get_salesperson_totals(df)
    category_totals    = get_category_totals(df)
    daily_totals       = get_daily_totals(df)

    lines = ["=== ARIA SALES DATA SUMMARY ==="]
    lines.append(f"Total Sales: ₹{daily_totals.sum():,.0f}")
    lines.append(f"Daily Average: ₹{daily_totals.mean():,.0f}")
    lines.append(f"Days in period: {len(daily_totals)}")
    lines.append("")

    lines.append("=== CATEGORY TOTALS ===")
    for _, row in category_totals.iterrows():
        lines.append(f"{row['Category']}: ₹{row['Total']:,.0f}")
    lines.append("")

    lines.append("=== TOP SALESPEOPLE ===")
    for _, row in salesperson_totals.head(10).iterrows():
        lines.append(f"{row['Salesperson']} ({row['Category']}): ₹{row['Total']:,.0f}")
    lines.append("")

    lines.append("=== DAILY TOTALS ===")
    for col, val in daily_totals.items():
        lines.append(f"{col}: ₹{val:,.0f}")

    zero_list = get_zero_sales(df)
    if zero_list:
        lines.append("")
        lines.append("=== ZERO-SALES ALERTS ===")
        lines.append(", ".join(zero_list))

    return "\n".join(lines)