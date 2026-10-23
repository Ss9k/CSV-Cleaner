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
):
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
    cleaned = dataframe.copy()

    # Optional text-level transformations
    if trim_whitespace or normalize_spaces or strip_html:
        str_cols = cleaned.select_dtypes(include=["object", "string"]).columns
        for col in str_cols:
            series = cleaned[col]
            if strip_html:
                series = series.apply(
                    lambda x: re.sub(r"<[^>]+>", "", str(x)) if pd.notna(x) else x
                )
            if normalize_spaces:
                series = series.apply(
                    lambda x: re.sub(r"\s+", " ", str(x)).strip() if pd.notna(x) else x
                )
            elif trim_whitespace:
                series = series.apply(
                    lambda x: x.strip() if isinstance(x, str) else x
                )
            cleaned[col] = series

    if remove_empty:
        cleaned = cleaned.replace(r"^\s*$", pd.NA, regex=True)
        cleaned = cleaned.dropna(how="all")

    if drop_empty_column and drop_empty_column in cleaned.columns:
        cleaned = cleaned.replace(r"^\s*$", pd.NA, regex=True)
        cleaned = cleaned.dropna(subset=[drop_empty_column])

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
) -> pd.DataFrame:
    """Return a DataFrame of removed records with a 'removal_reason' column."""
    working = dataframe.copy()
    reasons: dict[int, str] = {}

    # Check for empty rows
    if remove_empty:
        temp = working.replace(r"^\s*$", pd.NA, regex=True)
        empty_mask = temp.isna().all(axis=1)
        for idx in working[empty_mask].index:
            reasons[idx] = "Fully empty or whitespace-only row"

    # Check for missing required column
    if drop_empty_column and drop_empty_column in working.columns:
        temp_col = working[drop_empty_column].replace(r"^\s*$", pd.NA, regex=True)
        missing_mask = temp_col.isna()
        for idx in working[missing_mask].index:
            if idx not in reasons:
                reasons[idx] = f"Missing required column: {drop_empty_column}"

    # Check for duplicates (among remaining candidate rows)
    if remove_duplicates:
        candidate_indices = [i for i in working.index if i not in reasons]
        subset = duplicate_subset if duplicate_subset else None
        candidates = working.loc[candidate_indices]
        dup_mask = candidates.duplicated(subset=subset, keep="first")
        for idx in candidates[dup_mask].index:
            cols_note = f"in [{', '.join(subset)}]" if subset else "across all columns"
            reasons[idx] = f"Duplicate record ({cols_note})"

    if not reasons:
        empty_result = dataframe.iloc[0:0].copy()
        empty_result["removal_reason"] = []
        return empty_result

    removed_indices = sorted(reasons.keys())
    removed_df = dataframe.loc[removed_indices].copy()
    removed_df.insert(0, "removal_reason", [reasons[idx] for idx in removed_indices])
    return removed_df.reset_index(drop=True)


def clean_reviews_csv(input_path: str | Path, output_path: str | Path) -> pd.DataFrame:
    """Clean a CSV file and save the result to a separate output file."""
    source = Path(input_path)
    destination = Path(output_path)

    if source.resolve() == destination.resolve():
        raise ValueError("Input and output files must be different.")

    dataframe = pd.read_csv(source)
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

