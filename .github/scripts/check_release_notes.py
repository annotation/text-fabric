"""Check that the current version of Text-Fabric has release notes.

The version is read from `tf/parameters.py` (`VERSION = '...'`) and compared with
the version in `setup.cfg`. Then `tf/docs/about/releases.md` must contain a heading
for that version, e.g. `#### 13.1.1`, or a range that covers it, e.g. `#### 13.0.15-16`.

Optionally, pass a git tag (e.g. `v13.1.1`) as the first argument;
it must match the version as well.

Exits with status 1 and a message if a check fails.
Uses only the standard library, so it runs without installing Text-Fabric.
"""

import os
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PARAMETERS = ROOT / "tf" / "parameters.py"
SETUP_CFG = ROOT / "setup.cfg"
RELEASES = ROOT / "tf" / "docs" / "about" / "releases.md"

HEADING_RE = re.compile(r"^####\s+(\d+)\.(\d+)\.(\d+)(?:\s*-\s*(\d+))?\s*$", re.M)


def fail(msg):
    print(f"::error::{msg}" if "GITHUB_ACTIONS" in os.environ else msg)
    sys.exit(1)


def readVersion():
    text = PARAMETERS.read_text(encoding="utf8")
    match = re.search(r"""^VERSION\s*=\s*['"]([^'"]+)['"]""", text, re.M)
    if not match:
        fail(f"No VERSION found in {PARAMETERS.relative_to(ROOT)}")
    return match.group(1)


def readSetupVersion():
    text = SETUP_CFG.read_text(encoding="utf8")
    match = re.search(r"^version\s*=\s*(\S+)", text, re.M)
    return match.group(1) if match else None


def documentedVersions():
    text = RELEASES.read_text(encoding="utf8")
    versions = set()
    for major, minor, patch, patchEnd in HEADING_RE.findall(text):
        first = int(patch)
        last = int(patchEnd) if patchEnd else first
        for p in range(first, last + 1):
            versions.add(f"{major}.{minor}.{p}")
    return versions


def main():
    version = readVersion()
    setupVersion = readSetupVersion()

    if setupVersion != version:
        fail(
            f"Version mismatch: tf/parameters.py has {version}, "
            f"setup.cfg has {setupVersion}"
        )

    if len(sys.argv) > 1 and sys.argv[1]:
        tag = sys.argv[1].removeprefix("refs/tags/")
        if tag != f"v{version}":
            fail(f"Tag {tag} does not match version {version}")

    if version not in documentedVersions():
        fail(
            f"No release notes for version {version}: "
            f"add a '#### {version}' section to "
            f"{RELEASES.relative_to(ROOT).as_posix()}"
        )

    print(f"Release notes for version {version} found.")


if __name__ == "__main__":
    main()
