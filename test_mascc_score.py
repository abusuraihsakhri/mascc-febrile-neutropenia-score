"""Regression and boundary tests for the clinical MASCC index."""
import csv
import pytest
from mascc_score import calculate_metrics, process_batch, main

BASE = dict(burden="none_mild", no_hypotension=True, no_copd=True,
            favorable_malignancy=True, no_dehydration=True,
            outpatient_onset=True, age_under_60=True)


def test_maximum_is_26_and_low_risk():
    result = calculate_metrics(**BASE)
    assert result["score"] == 26
    assert result["classification"] == "Low risk"
    assert sum(result["components"].values()) == 26


def test_minimum_is_0_and_high_risk():
    inputs = {**{key: False for key in BASE if key != "burden"}, "burden": "severe"}
    result = calculate_metrics(**inputs)
    assert result["score"] == 0
    assert result["classification"] == "High risk"


def test_each_component_and_boundary():
    assert calculate_metrics(**{**BASE, "burden": "moderate"})["score"] == 24
    assert calculate_metrics(**{**BASE, "burden": "severe"})["score"] == 21
    assert calculate_metrics(**{**BASE, "no_hypotension": False})["score"] == 21
    assert calculate_metrics(**{**BASE, "no_copd": False})["score"] == 22
    assert calculate_metrics(**{**BASE, "favorable_malignancy": False})["score"] == 22
    assert calculate_metrics(**{**BASE, "no_dehydration": False})["score"] == 23
    assert calculate_metrics(**{**BASE, "outpatient_onset": False})["score"] == 23
    assert calculate_metrics(**{**BASE, "age_under_60": False})["score"] == 24
    assert calculate_metrics(**{**BASE, "no_hypotension": False, "age_under_60": False})["score"] == 19


@pytest.mark.parametrize("key,value", [
    ("burden", "unknown"), ("burden", ""),
    ("no_copd", ""), ("age_under_60", "maybe"),
    ("no_hypotension", None), ("outpatient_onset", float("nan")),
])
def test_rejects_invalid_input(key, value):
    with pytest.raises(ValueError):
        calculate_metrics(**{**BASE, key: value})


def test_requires_all_criteria():
    with pytest.raises(TypeError):
        calculate_metrics(burden="moderate")


def test_csv_roundtrip_and_no_partial_output(tmp_path):
    source, dest = tmp_path / "cases.csv", tmp_path / "out.csv"
    source.write_text(
        "case_id,burden,no_hypotension,no_copd,favorable_malignancy,no_dehydration,outpatient_onset,age_under_60\n"
        "CASE-001,none_mild,yes,yes,yes,yes,yes,yes\n"
        "CASE-002,severe,no,no,no,no,no,no\n", encoding="utf-8"
    )
    assert process_batch(source, dest) == 2
    with dest.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    assert [int(row["score"]) for row in rows] == [26, 0]
    source.write_text(source.read_text().replace("CASE-002,severe", "CASE-002,invalid"))
    with pytest.raises(ValueError, match="Line 3"):
        process_batch(source, dest)
    assert dest.read_text()  # existing output preserved


def test_csv_rejects_unsafe_format(tmp_path):
    source, dest = tmp_path / "cases.csv", tmp_path / "out.csv"
    source.write_text("Patient,v1,v2\nSomeone,1,2\n")
    with pytest.raises(ValueError, match="columns invalid"):
        process_batch(source, dest)
    assert not dest.exists()
    with pytest.raises(ValueError):
        process_batch(source, source)


def test_cli_single_requires_explicit_values(capsys):
    argv = ["single", "--burden", "none_mild"]
    for name in BASE:
        if name != "burden":
            argv.extend(["--" + name.replace("_", "-"), "yes"])
    assert main(argv) == 0
    assert '"score": 26' in capsys.readouterr().out
