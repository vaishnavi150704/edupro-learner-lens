"""Step 1a - read the three sheets of the EduPro Excel file."""
import pandas as pd
import config

REQUIRED = {
    "users": ["UserID", "UserName", "Age", "Gender"],
    "courses": ["CourseID", "CourseName", "CourseCategory", "CourseType", "CourseLevel"],
    "transactions": ["TransactionID", "UserID", "CourseID", "TransactionDate"],
}


def _find_sheet(book: dict, wanted: str) -> pd.DataFrame:
    for name, df in book.items():
        if name.strip().lower() == wanted.lower():
            return df
    raise KeyError(f"Sheet '{wanted}' not found. Sheets in file: {list(book)}")


def load_raw(path=config.RAW_EXCEL):
    """Return (users, courses, transactions) DataFrames with tidy column names."""
    if not path.exists():
        raise FileNotFoundError(
            f"Dataset not found at {path}\nPut EduPro_Online_Platform.xlsx inside data/raw/"
        )
    book = pd.read_excel(path, sheet_name=None)
    users = _find_sheet(book, config.SHEET_USERS)
    courses = _find_sheet(book, config.SHEET_COURSES)
    tx = _find_sheet(book, config.SHEET_TX)
    out = []
    for key, df in zip(["users", "courses", "transactions"], [users, courses, tx]):
        df = df.copy()
        df.columns = [str(c).strip() for c in df.columns]
        missing = [c for c in REQUIRED[key] if c not in df.columns]
        if missing:
            raise KeyError(f"{key} sheet is missing columns {missing}. Found: {list(df.columns)}")
        out.append(df[REQUIRED[key]])
    return tuple(out)
