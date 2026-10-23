"""Customer Review CSV Cleaner - Modern Streamlit Application."""
from io import BytesIO
from pathlib import Path
import re
import time
import pandas as pd
import streamlit as st

from src.cleaner import (
    clean_reviews_dataframe,
    dataframe_to_csv_bytes,
    dataframe_to_json_bytes,
    generate_audit_report,
    identify_removed_records,
)

# -----------------------------------------------------------------------------
# Streamlit Page Setup
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="Review CSV Cleaner Pro",
    page_icon="🧹",
    layout="wide",
    initial_sidebar_state="expanded",
)

# -----------------------------------------------------------------------------
# Modern CSS Styling
# -----------------------------------------------------------------------------
CUSTOM_CSS = """
<style>
/* Modern typography & font smoothing */
@import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap');

html, body, [class*="css"] {
    font-family: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, sans-serif;
}

/* Hero & Header Styling */
.hero-container {
    background: linear-gradient(135deg, rgba(99, 102, 241, 0.12) 0%, rgba(168, 85, 247, 0.08) 50%, rgba(236, 72, 153, 0.05) 100%);
    border: 1px solid rgba(99, 102, 241, 0.25);
    border-radius: 20px;
    padding: 28px 32px;
    margin-bottom: 24px;
    box-shadow: 0 10px 30px -10px rgba(0, 0, 0, 0.15);
    backdrop-filter: blur(8px);
}

.hero-pill {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    background: rgba(99, 102, 241, 0.2);
    border: 1px solid rgba(99, 102, 241, 0.4);
    color: #818cf8;
    padding: 4px 14px;
    border-radius: 9999px;
    font-size: 0.8rem;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.06em;
    margin-bottom: 12px;
}

.hero-title {
    font-size: 2.2rem;
    font-weight: 800;
    letter-spacing: -0.02em;
    line-height: 1.2;
    margin: 0 0 8px 0;
    background: linear-gradient(135deg, #ffffff 0%, #cbd5e1 50%, #94a3b8 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
}

.hero-subtitle {
    color: #94a3b8;
    font-size: 1.05rem;
    margin: 0;
    font-weight: 400;
    line-height: 1.5;
}

.feature-badge-row {
    display: flex;
    flex-wrap: wrap;
    gap: 12px;
    margin-top: 16px;
}

.feature-badge {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    background: rgba(255, 255, 255, 0.04);
    border: 1px solid rgba(255, 255, 255, 0.08);
    color: #cbd5e1;
    padding: 5px 12px;
    border-radius: 8px;
    font-size: 0.82rem;
    font-weight: 500;
}

/* Sleek KPI Cards */
.kpi-card {
    background: linear-gradient(180deg, rgba(30, 41, 59, 0.75) 0%, rgba(15, 23, 42, 0.85) 100%);
    border: 1px solid rgba(255, 255, 255, 0.08);
    border-radius: 16px;
    padding: 20px;
    box-shadow: 0 4px 20px -2px rgba(0, 0, 0, 0.25);
    transition: transform 0.2s ease, border-color 0.2s ease;
    height: 100%;
}

.kpi-card:hover {
    border-color: rgba(99, 102, 241, 0.4);
    transform: translateY(-2px);
}

.kpi-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 8px;
}

.kpi-title {
    font-size: 0.85rem;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    color: #94a3b8;
}

.kpi-icon {
    font-size: 1.25rem;
}

.kpi-value {
    font-size: 2.1rem;
    font-weight: 800;
    letter-spacing: -0.02em;
    color: #f8fafc;
    margin: 4px 0;
}

.kpi-badge {
    display: inline-flex;
    align-items: center;
    gap: 4px;
    padding: 3px 8px;
    border-radius: 6px;
    font-size: 0.78rem;
    font-weight: 600;
    margin-top: 4px;
}

.badge-success {
    background: rgba(16, 185, 129, 0.15);
    color: #34d399;
    border: 1px solid rgba(16, 185, 129, 0.3);
}

.badge-danger {
    background: rgba(239, 68, 68, 0.15);
    color: #f87171;
    border: 1px solid rgba(239, 68, 68, 0.3);
}

.badge-info {
    background: rgba(99, 102, 241, 0.15);
    color: #818cf8;
    border: 1px solid rgba(99, 102, 241, 0.3);
}

.badge-warning {
    background: rgba(245, 158, 11, 0.15);
    color: #fbbf24;
    border: 1px solid rgba(245, 158, 11, 0.3);
}

/* Feature Showcase Cards (Empty State) */
.guide-card {
    background: rgba(30, 41, 59, 0.5);
    border: 1px solid rgba(255, 255, 255, 0.07);
    border-radius: 16px;
    padding: 24px;
    margin-bottom: 16px;
    height: 100%;
}

.guide-icon {
    font-size: 2rem;
    margin-bottom: 12px;
}

.guide-title {
    font-size: 1.15rem;
    font-weight: 700;
    color: #f8fafc;
    margin-bottom: 8px;
}

.guide-text {
    font-size: 0.9rem;
    color: #94a3b8;
    line-height: 1.5;
}

/* File Uploader styling */
[data-testid="stFileUploader"] {
    background: rgba(30, 41, 59, 0.4);
    border: 2px dashed rgba(99, 102, 241, 0.4);
    border-radius: 16px;
    padding: 16px;
    transition: all 0.2s ease;
}

[data-testid="stFileUploader"]:hover {
    border-color: rgba(99, 102, 241, 0.8);
    background: rgba(99, 102, 241, 0.05);
}

/* Tabs styling */
.stTabs [data-baseweb="tab-list"] {
    gap: 8px;
    border-bottom: 1px solid rgba(255, 255, 255, 0.1);
    padding-bottom: 6px;
}

.stTabs [data-baseweb="tab"] {
    border-radius: 10px;
    padding: 8px 18px;
    font-weight: 600;
    font-size: 0.92rem;
    border: 1px solid transparent;
    transition: all 0.2s ease;
}

.stTabs [aria-selected="true"] {
    background: rgba(99, 102, 241, 0.2) !important;
    border-color: rgba(99, 102, 241, 0.4) !important;
    color: #818cf8 !important;
}

/* Primary Button Styling */
.stButton > button[kind="primary"] {
    background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%);
    border: none;
    font-weight: 600;
    letter-spacing: 0.02em;
    border-radius: 10px;
    padding: 10px 24px;
    box-shadow: 0 4px 14px rgba(99, 102, 241, 0.35);
    transition: all 0.2s ease;
}

.stButton > button[kind="primary"]:hover {
    transform: translateY(-1px);
    box-shadow: 0 6px 20px rgba(99, 102, 241, 0.5);
}

/* Section Header styling */
.section-header {
    display: flex;
    align-items: center;
    gap: 10px;
    font-size: 1.15rem;
    font-weight: 700;
    color: #f1f5f9;
    margin: 16px 0 12px 0;
    padding-bottom: 6px;
    border-bottom: 1px solid rgba(255, 255, 255, 0.07);
}

/* Sidebar styling */
[data-testid="stSidebar"] {
    background: #0f172a;
    border-right: 1px solid rgba(255, 255, 255, 0.08);
}
</style>
"""
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)


# -----------------------------------------------------------------------------
# Helper Functions
# -----------------------------------------------------------------------------
def detect_columns(df: pd.DataFrame) -> dict[str, str | None]:
    """Detect common customer review column roles (rating, review, customer)."""
    detected = {"rating": None, "review": None, "customer": None}
    lower_map = {col.lower().strip(): col for col in df.columns}

    # Detect rating
    for candidate in ["rating", "score", "stars", "star_rating", "rate"]:
        if candidate in lower_map:
            detected["rating"] = lower_map[candidate]
            break

    # Detect review text
    for candidate in ["review", "review_text", "reviews", "feedback", "comment", "comments", "text"]:
        if candidate in lower_map:
            detected["review"] = lower_map[candidate]
            break

    # Detect customer identifier
    for candidate in ["customer", "customer_name", "user", "username", "author", "reviewer"]:
        if candidate in lower_map:
            detected["customer"] = lower_map[candidate]
            break

    return detected


# -----------------------------------------------------------------------------
# Hero Banner
# -----------------------------------------------------------------------------
st.markdown(
    """
    <div class="hero-container">
        <div class="hero-pill">✨ Data Quality & Sanitization Suite</div>
        <h1 class="hero-title">Customer Review CSV Cleaner</h1>
        <p class="hero-subtitle">
            Sanitize feedback datasets, eliminate duplicates, strip ghost whitespace, and audit removed records with real-time visual comparisons.
        </p>
        <div class="feature-badge-row">
            <span class="feature-badge">⚡ Instant Visual Diff</span>
            <span class="feature-badge">🛡️ 100% In-Memory Privacy</span>
            <span class="feature-badge">📊 Deep Quality Audit</span>
            <span class="feature-badge">🧼 Smart Text Normalization</span>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)


# -----------------------------------------------------------------------------
# Sidebar: Cleaning & Normalization Controls
# -----------------------------------------------------------------------------
with st.sidebar:
    st.markdown("### ⚙️ Cleaning Engine")
    st.caption("Configure precision deduplication and sanitization rules.")

    with st.expander("🧹 Deduplication & Empty Rows", expanded=True):
        remove_empty = st.checkbox(
            "Remove empty / whitespace rows",
            value=True,
            help="Purge rows where every field is empty, null, or whitespace-only.",
        )
        remove_duplicates = st.checkbox(
            "Remove duplicate rows",
            value=True,
            help="Purge duplicate records across all columns or selected key columns.",
        )

    with st.expander("🧼 Text Normalization", expanded=True):
        trim_whitespace = st.checkbox(
            "Trim leading/trailing spaces",
            value=True,
            help="Strip leading and trailing spaces from all string columns.",
        )
        normalize_spaces = st.checkbox(
            "Collapse multiple spaces",
            value=False,
            help="Replace multiple consecutive whitespace/newlines with a single space.",
        )
        strip_html = st.checkbox(
            "Strip HTML tags",
            value=False,
            help="Remove HTML tags (e.g. <br>, <p>) commonly found in scraped reviews.",
        )

    st.markdown("---")
    st.markdown("### 🗂️ Data Source")

# -----------------------------------------------------------------------------
# File Upload & Sample Loader Controls
# -----------------------------------------------------------------------------
col_upload, col_actions = st.columns([3, 1])

with col_upload:
    uploaded = st.file_uploader(
        "Upload Customer Reviews (.csv)",
        type=["csv"],
        help="Upload any standard comma-separated CSV file containing customer feedback.",
    )

with col_actions:
    st.markdown("<div style='height: 28px;'></div>", unsafe_allow_html=True)
    sample_btn = st.button("⚡ Load Demo CSV", use_container_width=True, help="Load sample customer review dataset to test immediately")
    clear_btn = st.button("🔄 Clear / Reset", use_container_width=True, help="Reset the workspace")

# Session state handling for sample dataset
if "use_sample" not in st.session_state:
    st.session_state.use_sample = False

if sample_btn:
    st.session_state.use_sample = True
    st.toast("Loaded sample dataset!", icon="🚀")

if clear_btn:
    st.session_state.use_sample = False
    st.rerun()

# Determine active dataset
original_df: pd.DataFrame | None = None
source_filename = ""

if uploaded is not None:
    try:
        original_df = pd.read_csv(uploaded)
        source_filename = uploaded.name
    except (pd.errors.ParserError, UnicodeDecodeError, ValueError) as exc:
        st.error(f"⚠️ Could not parse CSV. Verify file encoding (UTF-8 recommended). Error: {exc}")
        st.stop()
    except Exception as exc:
        st.error(f"⚠️ Error reading uploaded file: {exc}")
        st.stop()
elif st.session_state.use_sample:
    sample_path = Path("data/sample_reviews.csv")
    if sample_path.exists():
        original_df = pd.read_csv(sample_path)
        source_filename = "sample_reviews.csv"
    else:
        st.warning("Sample review file not found on disk.")

# -----------------------------------------------------------------------------
# Main Application Flow
# -----------------------------------------------------------------------------
if original_df is not None:
    detected = detect_columns(original_df)

    # Dynamic sidebar settings that depend on dataset columns
    with st.sidebar:
        with st.expander("🎯 Column-Specific Filters", expanded=False):
            key_cols = st.multiselect(
                "Deduplicate by specific keys only:",
                options=list(original_df.columns),
                default=[],
                help="If selected, only these columns are checked for duplicates. Leave empty for all columns.",
            )
            dedup_subset = key_cols if key_cols else None

            drop_empty_col = st.selectbox(
                "Drop row if empty in column:",
                options=["(None)"] + list(original_df.columns),
                index=0,
                help="Ensure required columns (such as review text) are never blank.",
            )
            drop_empty_target = None if drop_empty_col == "(None)" else drop_empty_col

        st.markdown("---")
        st.caption(f"📁 **Active File**: `{source_filename}`")
        st.caption(f"📊 **Raw Size**: `{len(original_df):,}` rows × `{len(original_df.columns)}` cols")

    # Run Cleaning Pipeline
    cleaned_df = clean_reviews_dataframe(
        original_df,
        remove_empty=remove_empty,
        remove_duplicates=remove_duplicates,
        trim_whitespace=trim_whitespace,
        normalize_spaces=normalize_spaces,
        strip_html=strip_html,
        duplicate_subset=dedup_subset,
        drop_empty_column=drop_empty_target,
    )

    # Identify exact removed rows with reason
    removed_df = identify_removed_records(
        original_df,
        remove_empty=remove_empty,
        remove_duplicates=remove_duplicates,
        duplicate_subset=dedup_subset,
        drop_empty_column=drop_empty_target,
    )

    total_orig = len(original_df)
    total_clean = len(cleaned_df)
    total_removed = len(removed_df)
    retention_pct = (total_clean / total_orig * 100) if total_orig > 0 else 100
    removal_pct = (total_removed / total_orig * 100) if total_orig > 0 else 0

    # Cleanliness score calculation
    health_score = max(0, min(100, int(100 - (total_removed / total_orig * 100)))) if total_orig > 0 else 100
    if health_score >= 90:
        health_badge = f'<span class="kpi-badge badge-success">🟢 Excellent ({health_score}%)</span>'
    elif health_score >= 70:
        health_badge = f'<span class="kpi-badge badge-warning">🟡 Moderate ({health_score}%)</span>'
    else:
        health_badge = f'<span class="kpi-badge badge-danger">🔴 Needs Cleaning ({health_score}%)</span>'

    # -------------------------------------------------------------------------
    # KPI Metric Cards
    # -------------------------------------------------------------------------
    kpi1, kpi2, kpi3, kpi4 = st.columns(4)

    with kpi1:
        st.markdown(
            f"""
            <div class="kpi-card">
                <div class="kpi-header">
                    <span class="kpi-title">Raw Records</span>
                    <span class="kpi-icon">📥</span>
                </div>
                <div class="kpi-value">{total_orig:,}</div>
                <span class="kpi-badge badge-info">{len(original_df.columns)} columns</span>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with kpi2:
        st.markdown(
            f"""
            <div class="kpi-card">
                <div class="kpi-header">
                    <span class="kpi-title">Clean Records</span>
                    <span class="kpi-icon">✨</span>
                </div>
                <div class="kpi-value">{total_clean:,}</div>
                <span class="kpi-badge badge-success">{retention_pct:.1f}% retained</span>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with kpi3:
        st.markdown(
            f"""
            <div class="kpi-card">
                <div class="kpi-header">
                    <span class="kpi-title">Removed Records</span>
                    <span class="kpi-icon">🗑️</span>
                </div>
                <div class="kpi-value">{total_removed:,}</div>
                <span class="kpi-badge badge-danger">-{removal_pct:.1f}% pruned</span>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with kpi4:
        st.markdown(
            f"""
            <div class="kpi-card">
                <div class="kpi-header">
                    <span class="kpi-title">Data Quality</span>
                    <span class="kpi-icon">🛡️</span>
                </div>
                <div class="kpi-value">{health_score}%</div>
                {health_badge}
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown("<div style='height: 18px;'></div>", unsafe_allow_html=True)

    # -------------------------------------------------------------------------
    # Quick Action Download Bar
    # -------------------------------------------------------------------------
    stem_name = Path(source_filename).stem if source_filename else "reviews"
    clean_csv_name = f"{stem_name}_cleaned.csv"
    clean_json_name = f"{stem_name}_cleaned.json"

    download_col1, download_col2, download_col3, status_col = st.columns([1.5, 1.2, 1.2, 2])
    with download_col1:
        st.download_button(
            label="⬇️ Download Cleaned CSV",
            data=dataframe_to_csv_bytes(cleaned_df),
            file_name=clean_csv_name,
            mime="text/csv",
            type="primary",
            use_container_width=True,
        )
    with download_col2:
        st.download_button(
            label="📦 Export JSON",
            data=dataframe_to_json_bytes(cleaned_df),
            file_name=clean_json_name,
            mime="application/json",
            use_container_width=True,
        )
    with download_col3:
        if total_removed > 0:
            st.download_button(
                label="🗑️ Export Removed CSV",
                data=dataframe_to_csv_bytes(removed_df),
                file_name=f"{stem_name}_removed_audit.csv",
                mime="text/csv",
                use_container_width=True,
            )
        else:
            st.button("🗑️ Export Removed CSV", disabled=True, use_container_width=True)
    with status_col:
        st.caption(f"Ready for export • Safe non-destructive processing • Source file unaffected.")

    st.markdown("<div style='height: 12px;'></div>", unsafe_allow_html=True)

    # -------------------------------------------------------------------------
    # Visual Interactive Workspace Tabs
    # -------------------------------------------------------------------------
    tab_overview, tab_compare, tab_removed, tab_health, tab_report = st.tabs(
        [
            "📊 Analytics & Overview",
            "🔍 Side-by-Side Comparison",
            f"🗑️ Removed Records ({total_removed})",
            "📋 Schema & Column Health",
            "📝 Audit Log & Report",
        ]
    )

    # --- TAB 1: Analytics & Overview ---
    with tab_overview:
        st.markdown("<div class='section-header'>📊 Cleaning Dynamics</div>", unsafe_allow_html=True)
        chart_col1, chart_col2 = st.columns(2)

        with chart_col1:
            st.markdown("##### 📈 Dataset Flow Breakdown")
            breakdown_data = pd.DataFrame({
                "Category": ["Clean Retained", "Removed Records"],
                "Count": [total_clean, total_removed],
            })
            st.bar_chart(
                breakdown_data,
                x="Category",
                y="Count",
                color="Category",
                use_container_width=True,
            )

        with chart_col2:
            st.markdown("##### 🔍 Removal Reasons Distribution")
            if not removed_df.empty and "removal_reason" in removed_df.columns:
                reasons_counts = removed_df["removal_reason"].value_counts().reset_index()
                reasons_counts.columns = ["Reason", "Count"]
                st.bar_chart(reasons_counts, x="Reason", y="Count", color="#f87171", use_container_width=True)
            else:
                st.success("🎉 No records were removed! Your dataset has zero blank or duplicate rows under current criteria.")

        # Additional insights if rating or review columns exist
        rating_col = detected["rating"]
        if rating_col and rating_col in cleaned_df.columns:
            st.markdown("<div class='section-header'>⭐ Rating Distribution (Clean Dataset)</div>", unsafe_allow_html=True)
            r_col1, r_col2 = st.columns([2, 1])
            with r_col1:
                rating_counts = cleaned_df[rating_col].value_counts().sort_index().reset_index()
                rating_counts.columns = ["Rating", "Count"]
                st.bar_chart(rating_counts, x="Rating", y="Count", color="#818cf8", use_container_width=True)
            with r_col2:
                numeric_ratings = pd.to_numeric(cleaned_df[rating_col], errors="coerce").dropna()
                if not numeric_ratings.empty:
                    st.metric("Average Rating", f"{numeric_ratings.mean():.2f} / 5.0")
                    st.metric("5-Star Reviews", f"{(numeric_ratings == 5).sum():,}")
                    st.metric("Critical Reviews (≤ 2)", f"{(numeric_ratings <= 2).sum():,}")

    # --- TAB 2: Side-by-Side Comparison ---
    with tab_compare:
        st.markdown("<div class='section-header'>🔍 Interactive Data Inspector</div>", unsafe_allow_html=True)
        filter_col, slider_col = st.columns([3, 1])
        with filter_col:
            search_query = st.text_input("Search records (fuzzy keyword filter):", placeholder="Type any name, keyword, or text...")
        with slider_col:
            preview_rows = st.slider("Preview Rows", min_value=5, max_value=min(200, max(10, total_orig)), value=min(15, total_orig))

        # Filter display copies
        disp_orig = original_df.copy()
        disp_clean = cleaned_df.copy()

        if search_query.strip():
            query = search_query.strip().lower()
            mask_orig = disp_orig.astype(str).apply(lambda row: row.str.lower().str.contains(query, regex=False)).any(axis=1)
            mask_clean = disp_clean.astype(str).apply(lambda row: row.str.lower().str.contains(query, regex=False)).any(axis=1)
            disp_orig = disp_orig[mask_orig]
            disp_clean = disp_clean[mask_clean]
            st.caption(f"Showing matches for: **'{search_query}'** ({len(disp_clean)} found in clean)")

        col_left, col_right = st.columns(2)
        with col_left:
            st.markdown(f"##### 📥 Original Data (`{len(disp_orig):,}` matching)")
            st.dataframe(disp_orig.head(preview_rows), use_container_width=True)

        with col_right:
            st.markdown(f"##### ✨ Cleaned Data (`{len(disp_clean):,}` matching)")
            st.dataframe(disp_clean.head(preview_rows), use_container_width=True)

    # --- TAB 3: Removed Records Inspector ---
    with tab_removed:
        st.markdown("<div class='section-header'>🗑️ Audit of Purged Records</div>", unsafe_allow_html=True)
        if removed_df.empty:
            st.markdown(
                """
                <div style="text-align: center; padding: 40px; background: rgba(16, 185, 129, 0.08); border-radius: 16px; border: 1px dashed rgba(16, 185, 129, 0.3);">
                    <h3>🎉 Zero records purged</h3>
                    <p style="color: #94a3b8;">Every single record satisfied your quality criteria. Nothing was removed.</p>
                </div>
                """,
                unsafe_allow_html=True,
            )
        else:
            st.info(f"The following {len(removed_df):,} record(s) were flagged and excluded based on your cleaning rules.")
            st.dataframe(removed_df, use_container_width=True)

    # --- TAB 4: Schema & Health ---
    with tab_health:
        st.markdown("<div class='section-header'>📋 Column Completeness & Schema</div>", unsafe_allow_html=True)
        schema_summary = []
        for col in original_df.columns:
            total_vals = len(original_df)
            clean_nulls = int(cleaned_df[col].isna().sum()) if col in cleaned_df.columns else 0
            clean_populated = len(cleaned_df) - clean_nulls
            unique_count = cleaned_df[col].nunique() if col in cleaned_df.columns else 0
            completeness = (clean_populated / len(cleaned_df) * 100) if len(cleaned_df) > 0 else 0

            schema_summary.append({
                "Column Name": col,
                "Data Type": str(original_df[col].dtype),
                "Populated (Clean)": clean_populated,
                "Missing Values": clean_nulls,
                "Completeness Rate": f"{completeness:.1f}%",
                "Unique Values": unique_count,
            })

        schema_df = pd.DataFrame(schema_summary)
        st.dataframe(schema_df, use_container_width=True)

    # --- TAB 5: Audit Log & Report ---
    with tab_report:
        st.markdown("<div class='section-header'>📝 Comprehensive Audit Log</div>", unsafe_allow_html=True)
        report_text = generate_audit_report(
            original_df=original_df,
            cleaned_df=cleaned_df,
            removed_df=removed_df,
            filename=source_filename,
        )
        st.text_area("Audit Report Preview", value=report_text, height=320)
        st.download_button(
            label="📄 Download Audit Report (.txt)",
            data=report_text.encode("utf-8"),
            file_name=f"{stem_name}_cleaning_audit.txt",
            mime="text/plain",
        )

# -----------------------------------------------------------------------------
# Empty State: Interactive Welcome & Feature Guide
# -----------------------------------------------------------------------------
else:
    st.markdown("<div style='height: 12px;'></div>", unsafe_allow_html=True)
    g1, g2, g3 = st.columns(3)

    with g1:
        st.markdown(
            """
            <div class="guide-card">
                <div class="guide-icon">🧹</div>
                <div class="guide-title">Precision Cleaning</div>
                <div class="guide-text">
                    Removes blank or whitespace-only records, deduplicates across all columns or specific key fields, and trims erratic text padding.
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with g2:
        st.markdown(
            """
            <div class="guide-card">
                <div class="guide-icon">🔍</div>
                <div class="guide-title">Real-time Visual Diff</div>
                <div class="guide-text">
                    Compare original versus cleaned datasets side-by-side with live keyword filtering and an inspector for every single pruned record.
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with g3:
        st.markdown(
            """
            <div class="guide-card">
                <div class="guide-icon">🛡️</div>
                <div class="guide-title">Privacy & Audit-Ready</div>
                <div class="guide-text">
                    Files are processed 100% in-memory locally. Download pristine CSVs, JSON exports, and timestamped audit summaries.
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown("<div style='height: 20px;'></div>", unsafe_allow_html=True)

    # Sample data preview card
    sample_csv_path = Path("data/sample_reviews.csv")
    if sample_csv_path.exists():
        st.markdown("#### 📂 Preview Sample Dataset")
        st.caption("Click **'⚡ Load Demo CSV'** above to immediately test with this sample dataset:")
        sample_preview = pd.read_csv(sample_csv_path)
        st.dataframe(sample_preview, use_container_width=True)
