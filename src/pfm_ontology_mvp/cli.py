from __future__ import annotations

import argparse
from .pipeline import Pipeline


def main() -> None:
    parser = argparse.ArgumentParser(description="PFM ontology MVP pipeline")
    sub = parser.add_subparsers(dest="command")
    sub.add_parser("run", help="Run the full pipeline")
    args = parser.parse_args()
    if args.command == "run":
        Pipeline().run()
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
