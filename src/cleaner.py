"""Reusable CSV cleaning and retry utilities."""
from functools import wraps
from io import BytesIO
from pathlib import Path
import re
import time
from typing import Callable, TypeVar

import pandas as pd

F = TypeVar("F", bound=Callable)


def retry(
    max_attempts: int = 3,
    delay: float = 1.0,
    exceptions: tuple[type[BaseException], ...] = (Exception,),
) -> Callable[[F], F]:
    """Retry a function after selected exceptions, then re-raise the final error."""
    if max_attempts < 1:
        raise ValueError("max_attempts must be at least 1")
    if delay < 0:
        raise ValueError("delay cannot be negative")

    def decorator(func: F) -> F:
        @wraps(func)
        def wrapper(*args, **kwargs):
            for attempt in range(max_attempts):
                try:
                    return func(*args, **kwargs)
                except exceptions:
                    if attempt == max_attempts - 1:
                        raise
                    time.sleep(delay)
        return wrapper  # type: ignore[return-value]
    return decorator

def read_reviews_csv(source) -> pd.DataFrame:
    """Read a CSV without turning real text like "NA" or "None" into NaN.

    Only truly empty fields are treated as missing.
    """
    return pd.read_csv(source, keep_default_na=False, na_values=[""])


def _blank_mask(dataframe: pd.DataFrame) -> pd.DataFrame:
    """Cell-wise mask: True where a value is null, empty, or whitespace-only."""
    as_text = dataframe.astype(str).apply(lambda col: col.str.strip().eq(""))
    return dataframe.isna() | as_text


def _apply_text_transforms(
    dataframe: pd.DataFrame,
    *,
    trim_whitespace: bool,
    normalize_spaces: bool,
    strip_html: bool,
) -> pd.DataFrame:
    """Apply text cleanups to string cells only; non-strings are left untouched."""
    if not (trim_whitespace or normalize_spaces or strip_html):
        return dataframe
    out = dataframe.copy()
    for col in out.select_dtypes(include=["object", "string"]).columns:
        series = out[col]
        if strip_html:
            series = series.apply(
                    lambda x: re.sub(r"</?[A-Za-z][^<>]*>|<!--.*?-->", "", x, flags=re.DOTALL)
                    if isinstance(x, str) else x
                )

        if normalize_spaces:
                series = series.apply(
                    lambda x: re.sub(r"\s+", " ", x).strip() if isinstance(x, str) else x
                )

        elif trim_whitespace:
            series = series.apply(lambda x: x.strip() if isinstance(x, str) else x)
        out[col] = series
    return out

def clean_reviews_dataframe(
    dataframe: pd.DataFrame,
    *,
    remove_empty: bool = True,
    remove_duplicates: bool = True,
    trim_whitespace: bool = False,
    normalize_spaces: bool = False,
    strip_html: bool = False,
    duplicate_subset: list[str] | None = None,
    drop_empty_column: str | None = None,
) -> pd.DataFrame:
    """Return a cleaned copy, preserving the input DataFrame.

    Empty rows are rows where every field is null, empty, or whitespace-only.
    Duplicate rows are exact matches across all columns (or duplicate_subset if provided).
    """
    cleaned = _apply_text_transforms(
        dataframe,
        trim_whitespace=trim_whitespace,
        normalize_spaces=normalize_spaces,
        strip_html=strip_html,
    ).copy()

    if remove_empty:
        cleaned = cleaned[~_blank_mask(cleaned).all(axis=1)]

    if drop_empty_column and drop_empty_column in cleaned.columns:
        cleaned = cleaned[~_blank_mask(cleaned)[drop_empty_column]]

    if remove_duplicates:
        subset = duplicate_subset if duplicate_subset else None
        cleaned = cleaned.drop_duplicates(subset=subset)

    return cleaned.reset_index(drop=True)


def identify_removed_records(
    dataframe: pd.DataFrame,
    *,
    remove_empty: bool = True,
    remove_duplicates: bool = True,
    duplicate_subset: list[str] | None = None,
    drop_empty_column: str | None = None,
    trim_whitespace: bool = False,
    normalize_spaces: bool = False,
    strip_html: bool = False,
) -> pd.DataFrame:
    """Return a DataFrame of removed records with a 'removal_reason' column.

    Pass the same options given to clean_reviews_dataframe so the removed set
    matches exactly what the cleaner dropped. Returned rows are the ORIGINAL data.
    """
    working = _apply_text_transforms(
        dataframe,
        trim_whitespace=trim_whitespace,
        normalize_spaces=normalize_spaces,
        strip_html=strip_html,
    )
    blank = _blank_mask(working)
    reasons: dict = {}

    # Check for empty rows
    if remove_empty:
        for idx in working.index[blank.all(axis=1)]:
            reasons[idx] = "Fully empty or whitespace-only row"

    # Check for missing required column
    if drop_empty_column and drop_empty_column in working.columns:
        for idx in working.index[blank[drop_empty_column]]:
            reasons.setdefault(idx, f"Missing required column: {drop_empty_column}")

    # Check for duplicates (among remaining candidate rows)
    if remove_duplicates:
        candidates = working.loc[[i for i in working.index if i not in reasons]]
        subset = duplicate_subset or None
        dup_mask = candidates.duplicated(subset=subset, keep="first")
        cols_note = f"in [{', '.join(subset)}]" if subset else "across all columns"
        for idx in candidates.index[dup_mask]:
            reasons[idx] = f"Duplicate record ({cols_note})"

    if not reasons:
        empty_result = dataframe.iloc[0:0].copy()
        empty_result["removal_reason"] = []
        return empty_result

    removed_indices = sorted(reasons)
    removed_df = dataframe.loc[removed_indices].copy()
    removed_df.insert(0, "removal_reason", [reasons[idx] for idx in removed_indices])
    return removed_df.reset_index(drop=True)

    
def clean_reviews_csv(input_path: str | Path, output_path: str | Path) -> pd.DataFrame:
    """Clean a CSV file and save the result to a separate output file."""
    source = Path(input_path)
    destination = Path(output_path)

    if source.resolve() == destination.resolve():
        raise ValueError("Input and output files must be different.")

    dataframe = read_reviews_csv(source)
    cleaned = clean_reviews_dataframe(dataframe)
    destination.parent.mkdir(parents=True, exist_ok=True)
    cleaned.to_csv(destination, index=False)
    return cleaned


def dataframe_to_csv_bytes(dataframe: pd.DataFrame) -> bytes:
    """Serialize a DataFrame as UTF-8 CSV bytes for a web download."""
    return dataframe.to_csv(index=False).encode("utf-8")


def dataframe_to_json_bytes(dataframe: pd.DataFrame) -> bytes:
    """Serialize a DataFrame as UTF-8 formatted JSON bytes."""
    return dataframe.to_json(orient="records", indent=2, force_ascii=False).encode("utf-8")


def generate_audit_report(
    original_df: pd.DataFrame,
    cleaned_df: pd.DataFrame,
    removed_df: pd.DataFrame,
    filename: str = "reviews.csv",
) -> str:
    """Generate a clean text audit report summarizing cleaning results."""
    total_original = len(original_df)
    total_clean = len(cleaned_df)
    total_removed = len(removed_df)
    retention_rate = (total_clean / total_original * 100) if total_original > 0 else 0

    reasons_breakdown = ""
    if "removal_reason" in removed_df.columns and not removed_df.empty:
        counts = removed_df["removal_reason"].value_counts()
        reasons_breakdown = "\n".join(f"  - {reason}: {count:,} row(s)" for reason, count in counts.items())
    else:
        reasons_breakdown = "  - None (all rows retained)"

    null_summary = ""
    for col in cleaned_df.columns:
        null_count = int(cleaned_df[col].isna().sum())
        null_summary += f"  - {col}: {null_count} nulls remaining\n"

    report = f"""================================================================================
                      DATA CLEANING AUDIT REPORT
================================================================================
File Processed     : {filename}
Timestamp (Local)  : {time.strftime('%Y-%m-%d %H:%M:%S')}

1. ROW COUNT SUMMARY
--------------------------------------------------------------------------------
Original Records   : {total_original:,}
Cleaned Records    : {total_clean:,}
Removed Records    : {total_removed:,}
Retention Rate     : {retention_rate:.1f}%

2. REMOVAL BREAKDOWN
--------------------------------------------------------------------------------
{reasons_breakdown}

3. COLUMN NULL AUDIT (CLEAN DATASET)
--------------------------------------------------------------------------------
{null_summary}
================================================================================
Generated by Customer Review CSV Cleaner Pro
================================================================================
"""
    return report

