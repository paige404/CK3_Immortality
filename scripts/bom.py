# SPDX-FileCopyrightText: 2026 ddbb07
#
# SPDX-License-Identifier: MIT

# /// script
# requires-python = ">=3.14"
# dependencies = []
# ///

import argparse
from pathlib import Path

BOM = b"\xef\xbb\xbf"
ROOT = Path(__file__).parent.parent
LOCALIZATION_DIR = ROOT / "localization"
DIRECTORIES = ["common", "events", "localization"]
ACCEPTED_SUFFIXES = [".txt", ".yml"]


def add_bom(directory: Path) -> None:
    for path in directory.rglob("*"):
        if path.is_file() and path.suffix in ACCEPTED_SUFFIXES:
            data = path.read_bytes()
            if not data.startswith(BOM):
                path.write_bytes(BOM + data)


def remove_bom(directory: Path) -> None:
    for path in directory.rglob("*"):
        if path.is_file() and path.suffix in ACCEPTED_SUFFIXES:
            data = path.read_bytes()
            if data.startswith(BOM):
                path.write_bytes(data.removeprefix(BOM))


class Args(argparse.Namespace):
    remove_localization_boms: bool


def parse_args() -> Args:
    parser = argparse.ArgumentParser()
    parser.add_argument("--remove-localization-boms", action="store_true")
    return parser.parse_args(namespace=Args())


def main() -> None:
    args = parse_args()

    if args.remove_localization_boms:
        remove_bom(LOCALIZATION_DIR)
        return

    for directory_str in DIRECTORIES:
        add_bom(ROOT / directory_str)


if __name__ == "__main__":
    main()
