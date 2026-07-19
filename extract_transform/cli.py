from __future__ import annotations

import argparse


def cmd_placeholder(command_name: str) -> int:
    print(f"{command_name} is scaffolded but not implemented yet.")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="genshin-extract",
        description="Extraction tooling.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    extract = subparsers.add_parser(
        "extract-rankings",
        help="Extract normalized rankings from cached HTML (placeholder).",
    )
    extract.add_argument("--version")
    extract.add_argument("--start-version")
    extract.add_argument("--end-version")
    extract.add_argument("--failed-only", action="store_true")
    extract.set_defaults(func=lambda _args: cmd_placeholder("extract-rankings"))

    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
