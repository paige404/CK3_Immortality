# SPDX-FileCopyrightText: 2026 ddbb07
#
# SPDX-License-Identifier: MIT

# /// script
# requires-python = ">=3.14"
# dependencies = []
# ///

from pathlib import Path

BOM = b"\xef\xbb\xbf"
ROOT = Path(__file__).parent.parent
DIRECTORIES = ["common", "events", "localization"]
ACCEPTED_SUFFIXES = [".txt", ".yml"]


def add_bom(directory: Path) -> None:
    for path in directory.rglob("*"):
        if path.is_file() and path.suffix in ACCEPTED_SUFFIXES:
            data = path.read_bytes()
            if not data.startswith(BOM):
                path.write_bytes(BOM + data)


def main() -> None:
    for directory_str in DIRECTORIES:
        add_bom(ROOT / directory_str)


if __name__ == "__main__":
    main()
