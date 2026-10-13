# MASCC Febrile Neutropenia Risk Index

Clinical reference implementation of the seven-component **Multinational Association for Supportive Care in Cancer (MASCC)** risk index for adults with febrile neutropenia. Higher scores mean lower risk of serious complications.

**Clinical caution:** A score ≥21 identifies a lower-risk group; it is **not** by itself a decision to discharge. Prompt clinical evaluation and empiric treatment, patient stability, comorbidities, psychosocial factors, and follow-up are essential.

## Browser calculator

The static, responsive browser application in [web/index.html](web/index.html) calculates the MASCC index locally. It requires no external JavaScript packages, server, Python interpreter, patient identity, or browser storage. JSON results can be downloaded. Use synthetic/de-identified cases only. The root `index.html` mirrors the app for branch-based static hosting.

## MASCC criteria

| Characteristic | Points |
| --- | ---: |
| Burden of illness: no/mild, moderate, or severe (exclusive) | 5 / 3 / 0 |
| No hypotension (systolic BP >90 mmHg) | 5 |
| No COPD | 4 |
| Solid tumor or hematologic malignancy without previous invasive fungal infection | 4 |
| No dehydration requiring IV fluids | 3 |
| Outpatient status at onset of fever | 3 |
| Age <60 years | 2 |

**Range:** 0–26. **Low risk:** ≥21. **High risk:** <21. All seven criteria are required; missing values cannot silently receive favorable points.

Clinical references: [IDSA 2010](https://doi.org/10.1093/cid/cir073), [ASCO/IDSA 2018 outpatient guidance](https://doi.org/10.1200/JCO.2017.77.6211), and Klastersky J et al., *J Clin Oncol.* 2000;18:3038–3051.

## Install and use

Requires Python 3.10+.

```bash
python -m pip install -e ".[dev]"
python mascc_score.py single --burden none_mild --no-hypotension yes --no-copd yes --favorable-malignancy yes --no-dehydration yes --outpatient-onset yes --age-under-60 yes
python mascc_score.py batch -i sample.csv -o results.csv
python -m pytest -q
```

After installation, `mascc` runs the clinical scoring command. `mascc-audit-demo` runs the separate legacy component-audit CLI. CSV inputs require the seven named criteria (`burden`, `no_hypotension`, `no_copd`, `favorable_malignancy`, `no_dehydration`, `outpatient_onset`, `age_under_60`) and permit only an optional synthetic `case_id` column. Boolean values must be `yes/no`, `true/false`, or `1/0`.

## API

```bash
python cli.py serve --host 127.0.0.1 --port 8000
```

`POST /api/score` accepts all seven criteria as JSON (binary fields are booleans) and returns the score, classification and point breakdown. FastAPI generates the definitive OpenAPI spec at `/openapi.json` and interactive documentation at `/docs`.

The retained `/api/audit`, `/api/chat`, `/api/audit/logs` and `/metrics` endpoints are **non-clinical experimental demonstrations**. They do not calculate the MASCC risk index. The mock chat provider performs no model inference or clinical verification. The audit ledger is held in memory and the limited pattern-based identifier guard does **not** establish HIPAA compliance. Never provide identifying patient information to these interfaces. The enrichment/simulator modules are likewise experimental, not validated clinical tools.

## Docker

```bash
export AUDIT_SECRET_KEY="$(python -c 'import secrets; print(secrets.token_hex(32))')"
docker compose up --build
```

The key is operator-supplied; audit records are not persisted. The server has no authentication; bind it only to a trusted environment. The browser calculator does not use this server.

## Testing, privacy and deployment

CI runs pytest and compilation across Python 3.10–3.12, plus command-line and JavaScript syntax checks. The browser application needs a modern Chromium, Firefox or Safari browser; no backend Python, Pyodide, analytics, or browser storage are required. GitHub Pages deployment uses `web/`, while the root `index.html` supports branch-based hosting.

MIT licensed; see [LICENSE](LICENSE).
