#!/usr/bin/env python3
"""Validated MASCC febrile neutropenia risk index (adult cancer patients).

Points follow the original seven-variable MASCC index, maximum 26.
A higher score indicates a lower risk of serious complications.
This is risk stratification, not a stand-alone treatment/discharge decision.

References:
Klastersky et al. J Clin Oncol. 2000;18:3038-3051.
IDSA 2010 guideline: https://doi.org/10.1093/cid/cir073
ASCO/IDSA 2018 guideline: https://doi.org/10.1200/JCO.2017.77.6211
"""
import argparse
import csv
import json
import os
import sys
import tempfile
from pathlib import Path

CRITERIA = (
    "burden", "no_hypotension", "no_copd", "favorable_malignancy",
    "no_dehydration", "outpatient_onset", "age_under_60",
)
BOOLEAN_CRITERIA = CRITERIA[1:]
BURDEN_POINTS = {"none_mild": 5, "moderate": 3, "severe": 0}
POINTS = {
    "no_hypotension": 5,
    "no_copd": 4,
    "favorable_malignancy": 4,
    "no_dehydration": 3,
    "outpatient_onset": 3,
    "age_under_60": 2,
}


def _boolean(value, field):
    if isinstance(value, bool):
        return value
    if isinstance(value, int) and value in (0, 1):
        return bool(value)
    if isinstance(value, str) and value.strip().lower() in ("yes", "true", "1"):
        return True
    if isinstance(value, str) and value.strip().lower() in ("no", "false", "0"):
        return False
    raise ValueError(f"{field} must be yes/no, true/false or 1/0")


def calculate_metrics(*, burden, no_hypotension, no_copd,
                      favorable_malignancy, no_dehydration,
                      outpatient_onset, age_under_60):
    """Compute the 0–26 MASCC score from all seven required clinical criteria.

    'favorable_malignancy' means a solid tumor OR a hematologic malignancy
    without prior invasive fungal infection. 'no_hypotension' requires
    systolic BP >90 mmHg. 'no_dehydration' means IV rehydration not required.
    'outpatient_onset' refers to status at fever onset.
    """
    if not isinstance(burden, str) or burden.strip().lower() not in BURDEN_POINTS:
        raise ValueError("burden must be none_mild, moderate or severe")
    burden = burden.strip().lower()
    raw = locals().copy()
    components = {"burden": BURDEN_POINTS[burden]}
    for field in BOOLEAN_CRITERIA:
        components[field] = POINTS[field] if _boolean(raw[field], field) else 0
    score = sum(components.values())
    return {
        "tool": "mascc-febrile-neutropenia-score",
        "score": score,
        "classification": "Low risk" if score >= 21 else "High risk",
        "clinical_recommendation": (
            "May be considered for outpatient management only after full clinical, "
            "psychosocial and logistical assessment."
            if score >= 21 else
            "Higher risk of serious complications; inpatient assessment is generally indicated."
        ),
        "components": components,
        "inputs_evaluated": len(CRITERIA),
        "disclaimer": "Risk index only; febrile neutropenia needs urgent clinical assessment and empiric treatment.",
    }


def process_batch(input_csv, output_csv):
    """Evaluate a CSV with required MASCC criteria and optional synthetic case_id.

    Fail before writing if any row is invalid. Do not use patient identifiers.
    """
    source, destination = Path(input_csv), Path(output_csv)
    if source.resolve() == destination.resolve():
        raise ValueError("Input and output CSV must be different files")
    if not source.is_file():
        raise FileNotFoundError(f"Input CSV not found: {input_csv}")
    with source.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        headers = reader.fieldnames
        if not headers or len(headers) != len(set(headers)):
            raise ValueError("CSV requires unique headers")
        missing = [name for name in CRITERIA if name not in headers]
        unexpected = [name for name in headers if name not in (*CRITERIA, "case_id")]
        if missing or unexpected:
            raise ValueError(f"CSV columns invalid; missing={missing}, unexpected={unexpected}")
        rows = []
        for line, row in enumerate(reader, start=2):
            if None in row or any(value is None for value in row.values()):
                raise ValueError(f"Malformed CSV record on line {line}")
            try:
                result = calculate_metrics(**{name: row[name] for name in CRITERIA})
            except ValueError as exc:
                raise ValueError(f"Line {line}: {exc}") from exc
            rows.append({
                **row,
                "score": result["score"],
                "classification": result["classification"],
                "clinical_recommendation": result["clinical_recommendation"],
            })
    destination.parent.mkdir(parents=True, exist_ok=True)
    tmp_name = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w", encoding="utf-8", newline="", dir=destination.parent,
            prefix=".mascc-", suffix=".csv", delete=False
        ) as output:
            tmp_name = output.name
            writer = csv.DictWriter(output, fieldnames=[
                *headers, "score", "classification", "clinical_recommendation"
            ])
            writer.writeheader()
            writer.writerows(rows)
        os.replace(tmp_name, destination)
    finally:
        if tmp_name and os.path.exists(tmp_name):
            os.unlink(tmp_name)
    return len(rows)


def main(argv=None):
    parser = argparse.ArgumentParser(description="MASCC febrile neutropenia risk index (0–26)")
    sub = parser.add_subparsers(dest="command", required=True)
    single = sub.add_parser("single", help="Score all seven MASCC criteria")
    single.add_argument("--burden", choices=list(BURDEN_POINTS), required=True)
    for field in BOOLEAN_CRITERIA:
        single.add_argument("--" + field.replace("_", "-"),
                            choices=["yes", "no"], required=True)
    batch = sub.add_parser("batch", help="Score synthetic/de-identified CSV records")
    batch.add_argument("-i", "--input", required=True)
    batch.add_argument("-o", "--output", default="results.csv")
    args = parser.parse_args(argv)
    try:
        if args.command == "single":
            values = {field: getattr(args, field) for field in CRITERIA}
            print(json.dumps(calculate_metrics(**values), indent=2))
        else:
            count = process_batch(args.input, args.output)
            print(f"Processed {count} records -> {args.output}")
    except (ValueError, OSError, csv.Error) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
