"""Command line entry point: python -m pipeline.cli DATA --column NAME."""

import argparse

from . import aggregate, ingest, transform


def build_parser():
    parser = argparse.ArgumentParser(prog="pipeline.cli")
    parser.add_argument("data", help="CSV file with a header row")
    parser.add_argument("--column", required=True, help="numeric column to aggregate")
    return parser


def main(argv=None):
    args = build_parser().parse_args(argv)
    header, rows = ingest.read_records(args.data)
    index = ingest.column_index(header, args.column)
    values = transform.normalize_range(rows, index)
    print(f"mean\t{aggregate.mean(values):.4f}")


if __name__ == "__main__":
    main()
