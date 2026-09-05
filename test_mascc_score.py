import math
import pytest
from mascc_score import calculate_metrics, process_batch


def test_mascc_score_single():
    res = calculate_metrics(v1=12.0, v2=4.0)
    assert "score" in res
    assert "classification" in res
    assert res["score"] > 0


def test_mascc_score_batch(tmp_path):
    csv_in = tmp_path / "in.csv"
    csv_out = tmp_path / "out.csv"
    csv_in.write_text("Patient,v1,v2\nPat_001,15.0,3.0\nPat_002,5.0,1.0\n", encoding="utf-8")

    process_batch(str(csv_in), str(csv_out))
    assert csv_out.exists()
    content = csv_out.read_text(encoding="utf-8")
    assert "Pat_001" in content
    assert "score" in content


def test_calculate_metrics_rejects_non_finite():
    """Non-finite values (NaN, inf) should be rejected, not propagate."""
    res = calculate_metrics(v1=10.0, v2=float("nan"), v3=float("inf"))
    assert math.isfinite(res["score"])
    assert res["score"] == 10.0


def test_calculate_metrics_classification_tiers():
    """Verify classification boundaries."""
    low = calculate_metrics(v1=5.0)
    assert low["classification"] == "Low / Standard"

    moderate = calculate_metrics(v1=15.0)
    assert moderate["classification"] == "Moderate / Intermediate"

    high = calculate_metrics(v1=30.0)
    assert high["classification"] == "High / Severe"


def test_process_batch_missing_file(tmp_path):
    """process_batch raises FileNotFoundError for missing input."""
    with pytest.raises(FileNotFoundError):
        process_batch(str(tmp_path / "nonexistent.csv"), str(tmp_path / "out.csv"))


def test_process_batch_empty_headers(tmp_path):
    """process_batch raises ValueError for CSV with no headers."""
    csv_in = tmp_path / "empty.csv"
    csv_in.write_text("", encoding="utf-8")
    with pytest.raises(ValueError):
        process_batch(str(csv_in), str(tmp_path / "out.csv"))
