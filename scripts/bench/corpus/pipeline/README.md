# Pipeline

A small standard-library CSV data pipeline: read a CSV, parse one numeric
column, and aggregate it.

## Layout

- `pipeline/` — package: `ingest` (CSV reading), `transform` (parsing and
  normalization), `aggregate` (mean), `cli` (command line entry point).
- `tests/` — unittest suite.
- `data/sample.csv` — sample input.

## Commands

```text
python -m unittest discover -s tests -t .
python -m pipeline.cli data/sample.csv --column score
```

Stdlib only; no third-party dependencies.
