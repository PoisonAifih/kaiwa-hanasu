"""Build backend/data/jmdict.sqlite.

Usage: uv run python scripts/build_dictionary.py [--source path/to/jmdict-eng.json(.zip)]
"""

import argparse
import io
import json
import sys
import urllib.request
import zipfile
from pathlib import Path

from hanasu_backend.config import get_settings
from hanasu_backend.gloss.dictionary_build import build_dictionary

LATEST_RELEASE = "https://api.github.com/repos/scriptin/jmdict-simplified/releases/latest"
# Full export, not common-only
ASSET_PREFIX = "jmdict-eng-3"
ASSET_SUFFIX = ".json.zip"


def find_download_url() -> str:
    with urllib.request.urlopen(LATEST_RELEASE) as response:
        release = json.load(response)
    for asset in release["assets"]:
        name = asset["name"]
        if name.startswith(ASSET_PREFIX) and name.endswith(ASSET_SUFFIX):
            return asset["browser_download_url"]
    raise SystemExit("No jmdict-eng .json.zip asset in the latest jmdict-simplified release")


def read_source(raw: bytes) -> dict:
    if raw[:2] != b"PK":
        return json.loads(raw)
    with zipfile.ZipFile(io.BytesIO(raw)) as archive:
        name = next(n for n in archive.namelist() if n.endswith(".json"))
        return json.loads(archive.read(name))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, help="local jmdict-eng .json or .json.zip")
    args = parser.parse_args()

    if args.source:
        raw = args.source.read_bytes()
    else:
        url = find_download_url()
        print(f"Downloading {url}", file=sys.stderr)
        with urllib.request.urlopen(url) as response:
            raw = response.read()

    target = get_settings().dictionary_path
    count = build_dictionary(read_source(raw), target)
    print(f"Wrote {count} entries to {target}", file=sys.stderr)


if __name__ == "__main__":
    main()
