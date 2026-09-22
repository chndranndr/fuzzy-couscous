# Pipeline — Agent Guide

This repository is a small stdlib-only CSV data pipeline.

## Layout

- `pipeline/` — package modules: `ingest.py` (CSV reading), `transform.py`
  (parsing and normalization), `aggregate.py` (aggregations), `cli.py`
  (command line entry point).
- `tests/` — unittest suite.
- `data/` — CSV sample inputs.

## Commands

- Run tests: `python -m unittest discover -s tests -t .`
- Run the CLI: `python -m pipeline.cli data/sample.csv --column score`

## Conventions

- Python standard library only; do not add third-party dependencies.
- Follow the existing module structure and naming.
