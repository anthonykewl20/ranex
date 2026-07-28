# Wave 1 architecture-contract completeness report

Status: **GENERATED — RUN VALIDATOR**

This baseline covers executable documentation contracts only. It makes no
runtime, producer-enforcement, isolation, or production-readiness claim.

| Denominator | Count |
|---|---:|
| Governed YAML artifact templates/schemas | 36 |
| Capability zones | 36 |
| VITAL control tuples / assessments | 40 / 40 |
| Capability domains / projections | 10 / 10 |
| Architecture elements inventoried | 909 |
| ADR-0007 topology rules | 18 |
| ADR-0008 allowed roots / TDD rules | 18 / 19 |
| Definition-only per-rule assessments | 47 |
| Declared context edges / boundary-fit rows | 67 / 34 |
| ADR-0009 rules / fitness obligations | 10 / 9 |
| Coupling measures / feedback objectives | 6 / 4 |
| Negative semantic fixtures | 25 |
| Positive semantic fixtures | 1 |

All 40 control records are `NOT_ASSESSED` with separately recorded
`definition_status: DEFINED`. All ten domain projections derive `UNKNOWN`
because applicability and runtime evidence are unresolved. No numeric maturity
score is fabricated.

Run `uv run --project scripts/architecture python
scripts/architecture/validate_contracts.py` for the deterministic result.
