# SPDX-FileCopyrightText: 2026 ddbb07
#
# SPDX-License-Identifier: MIT

# /// script
# requires-python = ">=3.14"
# dependencies = [
#     "pydantic>=2.14.1",
# ]
# ///

import difflib
import hashlib
import io
import re
import subprocess
import tempfile
import urllib.error
import urllib.request
import zipfile
from pathlib import Path

from pydantic import BaseModel, ConfigDict, HttpUrl, field_validator

REPO = "paige404/CK3_Immortality"
STEAM_USER = "ddbb07"
APP_ID = 1158310
ITEM_ID = 2243652060
DESCRIPTION = "steam/description.bbcode"
VERSION_PATTERN = re.compile(
    r"^version=\"(?P<major>\d+)\.(?P<minor>\d+)\.(?P<patch>\d+)\"$",
    re.MULTILINE,
)


class WorkshopItem(BaseModel):
    model_config = ConfigDict(
        alias_generator=lambda name: name.replace("_", ""),
        validate_by_name=True,
    )

    app_id: int = APP_ID
    published_file_id: int = ITEM_ID
    content_folder: Path
    preview_file: Path
    change_note: str
    description: str

    @field_validator("content_folder", "preview_file", "change_note", "description")
    @classmethod
    def check_vdf_safe(cls, value: str | Path) -> str | Path:
        text = value.as_posix() if isinstance(value, Path) else value
        if '"' in text or "\\" in text:
            raise ValueError("can't contain quotes or backslashes")
        return value

    def dump_vdf(self) -> str:
        fields = self.model_dump(by_alias=True, exclude_none=True)
        fields["contentfolder"] = self.content_folder.as_posix()
        fields["previewfile"] = self.preview_file.as_posix()
        body = "\n".join(f'\t"{key}" "{value}"' for key, value in fields.items())
        return f'"workshopitem"\n{{\n{body}\n}}\n'


class GithubAsset(BaseModel):
    name: str
    browser_download_url: HttpUrl
    digest: str


class GithubRelease(BaseModel):
    tag_name: str
    html_url: HttpUrl
    assets: list[GithubAsset]


def fetch(url: str) -> bytes:
    with urllib.request.urlopen(url, timeout=30) as resp:
        return resp.read()


def fetch_latest_release(repo: str) -> GithubRelease:
    return GithubRelease.model_validate_json(
        fetch(f"https://api.github.com/repos/{repo}/releases/latest")
    )


def fetch_description(repo: str, tag: str) -> str | None:
    try:
        data = fetch(f"https://raw.githubusercontent.com/{repo}/{tag}/{DESCRIPTION}")
    except urllib.error.HTTPError as error:
        if error.code == 404:
            return None
        raise
    return data.decode().strip()


def print_description_changes(
    old_description: str | None, old_tag: str, new_description: str, new_tag: str
) -> None:
    if old_description is None:
        print(f"Description (no {DESCRIPTION} in {old_tag}):\n{new_description}")
        return
    diff = difflib.unified_diff(
        old_description.splitlines(),
        new_description.splitlines(),
        old_tag,
        new_tag,
        lineterm="",
    )
    print("Description:")
    print("\n".join(diff) or "  unchanged")


def extract_release_zip(release: GithubRelease, target_directory: Path) -> Path:
    asset = next((a for a in release.assets if a.name.endswith(".zip")), None)
    if asset is None:
        raise ValueError(f"No zip in release {release.tag_name}")
    data = fetch(str(asset.browser_download_url))

    if "sha256:" + hashlib.sha256(data).hexdigest() != asset.digest:
        raise ValueError(f"Hash mismatch for {asset.name}")

    with zipfile.ZipFile(io.BytesIO(data)) as archive:
        archive.extractall(target_directory)

    folders = list(target_directory.iterdir())
    if len(folders) != 1:
        raise ValueError(f"Expected one mod folder in {asset.name}")
    return folders[0]


def hash_files(directory: Path) -> dict[str, str]:
    return {
        path.relative_to(directory).as_posix(): hashlib.sha256(
            path.read_bytes()
        ).hexdigest()
        for path in directory.rglob("*")
        if path.is_file()
    }


def print_file_changes(old_directory: Path, new_directory: Path) -> None:
    old_files = hash_files(old_directory)
    new_files = hash_files(new_directory)
    for name in sorted(old_files | new_files):
        if name not in old_files:
            print(f"  added    {name}")
        elif name not in new_files:
            print(f"  removed  {name}")
        elif old_files[name] != new_files[name]:
            print(f"  changed  {name}")


def read_mod_version(mod_directory: Path) -> str:
    descriptor = mod_directory / "descriptor.mod"
    match = VERSION_PATTERN.search(descriptor.read_text(encoding="utf-8-sig"))
    if not match:
        raise ValueError(f"Could not find valid version in: {descriptor}")
    return f"{match['major']}.{match['minor']}.{match['patch']}"


def version_key(version: str) -> tuple[int, ...]:
    return tuple(int(part) for part in version.split("."))


def run_steamcmd(*arguments: str) -> None:
    command = ["steamcmd", *arguments, "+exit"]
    output = ""
    with subprocess.Popen(command, stdout=subprocess.PIPE, encoding="utf-8") as process:
        assert process.stdout is not None
        while char := process.stdout.read(1):
            print(char, end="", flush=True)
            output += char
    if process.returncode != 0:
        raise SystemExit("SteamCMD exited non zero, aborting")
    if "ERROR" in output:
        raise SystemExit("SteamCMD reported an error, aborting")


def download_workshop_item(target_directory: Path) -> Path:
    run_steamcmd(
        "+force_install_dir",
        str(target_directory),
        "+login",
        STEAM_USER,
        "+workshop_download_item",
        str(APP_ID),
        str(ITEM_ID),
    )
    return target_directory / "steamapps/workshop/content" / str(APP_ID) / str(ITEM_ID)


def main() -> None:
    release = fetch_latest_release(REPO)
    change_note = (
        f"{release.tag_name}\n[url={release.html_url}]{release.html_url}[/url]"
    )
    description = fetch_description(REPO, release.tag_name)
    if description is None:
        raise SystemExit(f"No {DESCRIPTION} in {release.tag_name}")

    with tempfile.TemporaryDirectory() as temp:
        temp_directory = Path(temp)
        mod_directory = extract_release_zip(release, temp_directory / "content")
        preview_file = mod_directory / "thumbnail.png"
        if not preview_file.exists():
            raise SystemExit(f"No thumbnail.png in {release.tag_name}")
        workshop_item = WorkshopItem(
            content_folder=mod_directory,
            preview_file=preview_file,
            change_note=change_note,
            description=description,
        )

        workshop_directory = download_workshop_item(temp_directory / "workshop")
        release_version = read_mod_version(mod_directory)
        workshop_version = read_mod_version(workshop_directory)
        if version_key(workshop_version) >= version_key(release_version):
            raise SystemExit(
                f"Workshop already has {workshop_version}, not older than {release_version}"
            )

        print(f"\nWorkshop item: {ITEM_ID}")
        print(f"Release: {release.tag_name}")
        print(f"Version: {workshop_version} -> {release_version}")
        print("Files:")
        print_file_changes(workshop_directory, mod_directory)
        print(f"\nChange note:\n{change_note}")
        workshop_tag = f"v{workshop_version}"
        print_description_changes(
            fetch_description(REPO, workshop_tag),
            workshop_tag,
            description,
            release.tag_name,
        )
        print()
        if input("Upload to Steam? [y/N] ").strip().lower() != "y":
            raise SystemExit("Aborted")

        vdf_path = temp_directory / "workshop_item.vdf"
        vdf_path.write_text(workshop_item.dump_vdf(), encoding="utf-8")
        run_steamcmd("+login", STEAM_USER, "+workshop_build_item", str(vdf_path))


if __name__ == "__main__":
    main()
