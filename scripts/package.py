# SPDX-FileCopyrightText: 2026 ddbb07
#
# SPDX-License-Identifier: MIT

# /// script
# requires-python = ">=3.14"
# dependencies = []
# ///

import argparse
import re
import shutil
from pathlib import Path

ROOT = Path(__file__).parent.parent
PACKAGE_DIRECTORY = ROOT / "package"
MOD_NAME = "CK3_Immortality"
MOD_DIRECTORY = PACKAGE_DIRECTORY / MOD_NAME
INCLUDED_DIRECTORIES = ["common", "events", "gfx", "localization"]
INCLUDED_FILES = ["descriptor.mod", "README-CN.md", "README.md", "thumbnail.png"]
VERSION_PATTERN = re.compile(
    r"^version=\"(?P<major>\d+)\.(?P<minor>\d+)\.(?P<patch>\d+)\"$",
    re.MULTILINE,
)


def read_mod_version() -> str:
    descriptor = ROOT / "descriptor.mod"
    match = VERSION_PATTERN.search(descriptor.read_text(encoding="utf-8-sig"))
    if not match:
        raise ValueError(f"Could not find valid version in: {descriptor}")
    return f"{match['major']}.{match['minor']}.{match['patch']}"


def ensure_directory_exists(directory_path: Path) -> None:
    if directory_path.is_file():
        raise NotADirectoryError(
            f"Path exists but is file, not directory: {directory_path}"
        )
    directory_path.mkdir(exist_ok=True)


def clear_directory(directory_path: Path) -> None:
    for path in directory_path.iterdir():
        if path.is_symlink() or path.is_file():
            path.unlink()
            continue
        if path.is_dir():
            shutil.rmtree(path)
            continue
        raise ValueError(f"Path type is not recognized: {path}")


def package() -> None:
    ensure_directory_exists(PACKAGE_DIRECTORY)
    clear_directory(PACKAGE_DIRECTORY)
    ensure_directory_exists(MOD_DIRECTORY)

    for directory_name in INCLUDED_DIRECTORIES:
        source_path = ROOT / directory_name
        target_path = MOD_DIRECTORY / directory_name
        shutil.copytree(source_path, target_path)

    for file_name in INCLUDED_FILES:
        source_path = ROOT / file_name
        target_path = MOD_DIRECTORY / file_name
        shutil.copy(source_path, target_path)


def archive() -> None:
    mod_version = read_mod_version()
    shutil.make_archive(
        base_name=str(PACKAGE_DIRECTORY / f"{MOD_NAME}-v{mod_version}"),
        format="zip",
        root_dir=MOD_DIRECTORY.parent,
        base_dir=MOD_DIRECTORY.name,
    )


class Args(argparse.Namespace):
    archive: bool


def parse_args() -> Args:
    parser = argparse.ArgumentParser()
    parser.add_argument("-a", "--archive", action="store_true")
    return parser.parse_args(namespace=Args())


def main() -> None:
    args = parse_args()
    package()
    if args.archive:
        archive()


if __name__ == "__main__":
    main()
