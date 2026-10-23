# Customer Review CSV Cleaner Pro 🧹

An attractive, modern Streamlit application designed to inspect, deduplicate, sanitize, and audit customer feedback CSV files.

## Features

- **Modern & Attractive UI**: Glassmorphism hero cards, dynamic dark/light theme integration, KPI metric counters, and status badges.
- **One-Click Demo Dataset**: Instant sample data loader (`data/sample_reviews.csv`) to test the application with a single click.
- **Precision Deduplication**: Remove duplicates across all columns or target specific key identifiers (e.g. customer, review).
- **Whitespace & HTML Sanitization**: Automatically strip ghost whitespace, collapse multiple spaces, or purge HTML tags.
- **Side-by-Side Visual Diff**: Interactive comparison table with real-time keyword filtering and preview sliders.
- **Removed Records Inspector**: View every pruned record along with the exact reason it was excluded.
- **Analytics & Data Health**: Data Quality Score gauge, flow distribution charts, rating breakdowns, and schema completeness.
- **Multi-Format Export**: One-click download for cleaned CSV, cleaned JSON, removed-records CSV audit log, and full text audit summary.
- **Local & Privacy-Preserving**: 100% in-memory client-side processing — no data leaves your local machine.
- **Automated Test Suite**: Tested with pytest including edge cases and retry decorator utilities.

## Requirements

- Python 3.11 or newer
- pip

## Run locally (Windows PowerShell)

```powershell
py -3.12 -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
streamlit run app.py
```

If PowerShell blocks activation, run `.venv\Scripts\python.exe -m pip install -r requirements.txt`
and `.venv\Scripts\python.exe -m streamlit run app.py`.

## Run tests

```powershell
python -m pytest -v
```

## Cleaning rules

- An empty row means all its fields are null, empty strings, or whitespace-only.
- A duplicate row is an exact match across every column.
- Rows with a missing review but other populated fields are not removed automatically.
- The source file is not overwritten.

## Suggested contribution workflow

1. Create a feature branch.
2. Run the test suite.
3. Commit the changes.
4. Push the branch to your fork or repository.
5. Open a pull request with a summary and test results.
6. Merge after review and required checks pass.
