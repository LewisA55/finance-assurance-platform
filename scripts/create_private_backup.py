"""Create an integrity-listed private backup of ignored consumer authoring files."""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from datetime import UTC, datetime
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile

PRIVATE_PATTERNS = (
    "consumer-products/excel/work/**/*",
    "consumer-products/excel/exports/**/*",
    "consumer-products/power-bi/work/**/*",
    "consumer-products/power-bi/exports/**/*",
)
AUTHORITY_PATTERNS = (
    "build/**/*.digest",
    "build/**/*-manifest.json",
    "build/**/checksums.json",
)


def _digest(path: Path) -> str:
    value = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            value.update(chunk)
    return f"sha256:{value.hexdigest()}"


def _git_head(root: Path) -> str | None:
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=root, text=True, stderr=subprocess.DEVNULL
        ).strip()
    except (OSError, subprocess.CalledProcessError):
        return None


def collect_backup_files(root: Path) -> list[Path]:
    files: set[Path] = set()
    for pattern in (*PRIVATE_PATTERNS, *AUTHORITY_PATTERNS):
        for path in root.glob(pattern):
            if path.is_file() and not path.is_symlink():
                files.add(path.resolve())
    return sorted(files, key=lambda path: path.relative_to(root).as_posix())


def create_private_backup(root: Path, destination: Path, *, label: str | None = None) -> Path:
    root = root.resolve()
    destination = destination.resolve()
    if destination == root or root in destination.parents:
        raise ValueError("backup destination must be outside the repository")
    destination.mkdir(parents=True, exist_ok=True)
    files = collect_backup_files(root)
    if not files:
        raise ValueError("no private consumer files or authority receipts were found")

    timestamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    safe_label = "" if not label else f"-{''.join(c for c in label if c.isalnum() or c in '-_')}"
    archive = destination / f"finance-assurance-private{safe_label}-{timestamp}.zip"
    partial = archive.with_suffix(".zip.partial")
    inventory = [
        {
            "path": path.relative_to(root).as_posix(),
            "byte_count": path.stat().st_size,
            "sha256": _digest(path),
        }
        for path in files
    ]
    manifest = {
        "contract_version": "finance-assurance-private-backup@v1",
        "created_at": datetime.now(UTC).isoformat().replace("+00:00", "Z"),
        "git_head": _git_head(root),
        "file_count": len(inventory),
        "files": inventory,
    }
    with ZipFile(partial, "w", compression=ZIP_DEFLATED, compresslevel=9) as output:
        for path in files:
            output.write(path, path.relative_to(root).as_posix())
        output.writestr(
            "backup-manifest.json",
            json.dumps(manifest, indent=2, sort_keys=True) + "\n",
        )
    partial.replace(archive)
    archive.with_suffix(".zip.sha256").write_text(f"{_digest(archive)}  {archive.name}\n", encoding="ascii")
    return archive


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--destination", required=True, type=Path)
    parser.add_argument("--label")
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    archive = create_private_backup(root, args.destination, label=args.label)
    print(archive)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
