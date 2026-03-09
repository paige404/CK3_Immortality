#!/usr/bin/env python
from pathlib import Path
import shutil

package_directory = "package"
included_directories = ["common", "events", "gfx", "localization"]
included_files = ["descriptor.mod", "README-CN.md", "README.md", "thumbnail.png"]


def ensure_directory_exists(directory_path: Path) -> None:
    if directory_path.exists() and directory_path.is_file():
        raise ValueError(f"Path exists but is file not directory: {directory_path}")
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


def main() -> None:
    cwd = Path.cwd()
    package_directory_path = cwd / package_directory

    ensure_directory_exists(package_directory_path)
    clear_directory(package_directory_path)

    for directory_name in included_directories:
        source_path = cwd / directory_name
        target_path = package_directory_path / directory_name
        shutil.copytree(source_path, target_path)

    for file_name in included_files:
        source_path = cwd / file_name
        target_path = package_directory_path / file_name
        shutil.copy(source_path, target_path)


if __name__ == "__main__":
    main()
