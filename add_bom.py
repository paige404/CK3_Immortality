#!/usr/bin/env python
from pathlib import Path

BOM = b"\xef\xbb\xbf"
DIRECTORIES = ["common", "events", "localization"]
ACCEPTED_SUFFIXES = [".txt", ".yml"]


def add_bom(directory: str) -> None:
    for path in Path(directory).rglob("*"):
        if path.is_file() and path.suffix in ACCEPTED_SUFFIXES:
            data = path.read_bytes()
            if not data.startswith(BOM):
                path.write_bytes(BOM + data)


def main() -> None:
    for directory in DIRECTORIES:
        add_bom(directory)


if __name__ == "__main__":
    main()
