import pandas as pd
import pytest

from src.cleaner import (
    clean_reviews_csv,
    clean_reviews_dataframe,
    identify_removed_records,
    read_reviews_csv,
    retry,
)


def test_removes_fully_empty_and_whitespace_rows():
    data = pd.DataFrame({
        "customer": ["Alice", None, "   "],
        "review": ["Good", None, "\t"],
    })
    result = clean_reviews_dataframe(data)
    assert len(result) == 1
    assert result.iloc[0]["customer"] == "Alice"


def test_removes_exact_duplicates():
    data = pd.DataFrame({
        "customer": ["Alice", "Alice", "Bob"],
        "review": ["Good", "Good", "Okay"],
    })
    result = clean_reviews_dataframe(data)
    assert len(result) == 2


def test_preserves_non_duplicate_reviews():
    data = pd.DataFrame({
        "customer": ["Alice", "Bob"],
        "review": ["Good", "Great"],
    })
    result = clean_reviews_dataframe(data)
    assert len(result) == 2


def test_does_not_mutate_input_dataframe():
    data = pd.DataFrame({"customer": ["Alice", "Alice"], "review": ["Good", "Good"]})
    original = data.copy(deep=True)
    clean_reviews_dataframe(data)
    pd.testing.assert_frame_equal(data, original)


def test_can_disable_cleaning_options():
    data = pd.DataFrame({"customer": ["Alice", "Alice"], "review": ["Good", "Good"]})
    result = clean_reviews_dataframe(data, remove_empty=False, remove_duplicates=False)
    assert len(result) == 2


def test_saves_cleaned_csv_to_output_path(tmp_path):
    source = tmp_path / "reviews.csv"
    destination = tmp_path / "output" / "clean.csv"
    source.write_text(
        "customer,review\nAlice,Good\nAlice,Good\n,\n",
        encoding="utf-8",
    )

    result = clean_reviews_csv(source, destination)

    assert destination.exists()
    assert len(result) == 1
    saved = pd.read_csv(destination)
    assert len(saved) == 1
    assert saved.iloc[0]["customer"] == "Alice"


def test_rejects_same_input_and_output_path(tmp_path):
    source = tmp_path / "reviews.csv"
    source.write_text("customer,review\nAlice,Good\n", encoding="utf-8")

    with pytest.raises(ValueError, match="different"):
        clean_reviews_csv(source, source)


def test_retry_succeeds_after_transient_failure():
    calls = {"count": 0}

    @retry(max_attempts=3, delay=0, exceptions=(ValueError,))
    def sometimes_fails():
        calls["count"] += 1
        if calls["count"] < 3:
            raise ValueError("temporary")
        return "ok"

    assert sometimes_fails() == "ok"
    assert calls["count"] == 3


def test_retry_reraises_after_max_attempts():
    calls = {"count": 0}

    @retry(max_attempts=2, delay=0, exceptions=(ValueError,))
    def always_fails():
        calls["count"] += 1
        raise ValueError("still failing")

    with pytest.raises(ValueError, match="still failing"):
        always_fails()
    assert calls["count"] == 2


def test_retry_rejects_invalid_attempt_count():
    with pytest.raises(ValueError, match="at least 1"):
        retry(max_attempts=0)


def test_trim_whitespace_and_normalize_spaces():
    data = pd.DataFrame({
        "customer": ["  Alice  ", "Bob  "],
        "review": ["Great    product!", "Loved   it \n a lot"],
    })
    result = clean_reviews_dataframe(data, trim_whitespace=True, normalize_spaces=True)
    assert result.iloc[0]["customer"] == "Alice"
    assert result.iloc[0]["review"] == "Great product!"
    assert result.iloc[1]["review"] == "Loved it a lot"


def test_strip_html_tags():
    data = pd.DataFrame({
        "customer": ["Alice"],
        "review": ["<b>Superb</b> quality! <br/> Highly recommended."],
    })
    result = clean_reviews_dataframe(data, strip_html=True)
    assert result.iloc[0]["review"] == "Superb quality!  Highly recommended."


def test_identify_removed_records():
    data = pd.DataFrame({
        "customer": ["Alice", "Bob", "Alice", "   ", None],
        "review": ["Good", "Bad", "Good", "   ", None],
    })
    removed = identify_removed_records(data)
    assert len(removed) == 3
    # 2 are empty/whitespace rows, 1 is duplicate
    reasons = list(removed["removal_reason"])
    assert any("empty" in r.lower() for r in reasons)
    assert any("duplicate" in r.lower() for r in reasons)

# --- Regression tests for bug-hunt fixes ---

def test_removed_report_matches_cleaner_when_text_normalization_on():
    data = pd.DataFrame({
        "customer": ["Alice", "Alice ", "Bob"],
        "review": ["Great", "Great", "Ok"],
    })
    opts = dict(trim_whitespace=True)
    cleaned = clean_reviews_dataframe(data, **opts)
    removed = identify_removed_records(data, **opts)
    assert len(cleaned) + len(removed) == len(data)


def test_whitespace_only_cell_in_kept_row_is_not_nulled():
    data = pd.DataFrame({
        "customer": ["Alice", "Bob"],
        "review": ["   ", "Fine"],
        "rating": [5, 3],
    })
    cleaned = clean_reviews_dataframe(data)
    assert len(cleaned) == 2
    assert cleaned.loc[0, "review"] == "   "


def test_strip_html_keeps_plain_angle_brackets_and_non_strings():
    data = pd.DataFrame({
        "review": ["1 <2 stars, rating >0", "<b>bold</b>"],
        "mixed": [1, "x"],
    })
    cleaned = clean_reviews_dataframe(data, strip_html=True)
    assert cleaned.loc[0, "review"] == "1 <2 stars, rating >0"
    assert cleaned.loc[1, "review"] == "bold"
    assert cleaned.loc[0, "mixed"] == 1


def test_read_reviews_csv_keeps_na_like_text(tmp_path):
    path = tmp_path / "in.csv"
    path.write_text("customer,review,rating\nNA,None,5\nBob,,3\n")
    df = read_reviews_csv(path)
    assert df.loc[0, "customer"] == "NA" and df.loc[0, "review"] == "None"
    assert pd.isna(df.loc[1, "review"])