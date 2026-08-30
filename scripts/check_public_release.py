"""Fail when the repository is not safe and self-contained for a public tag."""

from __future__ import annotations

import hashlib
import json
import os
import re
import subprocess
from fnmatch import fnmatch
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MAX_TRACKED_BYTES = 25 * 1024 * 1024
FORBIDDEN_PREFIXES = (
    "build/",
    "outputs/",
    "PBI/",
    "consumer-products/excel/work/",
    "consumer-products/excel/exports/",
    "consumer-products/power-bi/work/",
    "consumer-products/power-bi/exports/",
    "consumer-products/power-bi/model/.pbi/",
    "temp cover page tests/",
    "local-notes/",
    "web/public/duckdb/",
    "node_modules/",
)
FORBIDDEN_SUFFIXES = (".duckdb", ".xlsx", ".pbix", ".pem", ".key")
TEXT_SUFFIXES = {
    "",
    ".css",
    ".html",
    ".ini",
    ".js",
    ".json",
    ".jsonl",
    ".lock",
    ".md",
    ".mjs",
    ".py",
    ".sql",
    ".toml",
    ".ts",
    ".tsx",
    ".txt",
    ".xml",
    ".yaml",
    ".yml",
}
REQUIRED = {
    ".gitattributes",
    ".github/workflows/quality.yml",
    ".gitignore",
    "CHANGELOG.md",
    "CONTRIBUTING.md",
    "LICENSE.md",
    "README.md",
    "SECURITY.md",
    "docs/public-release/architecture.md",
    "docs/public-release/artifact-policy.md",
    "docs/public-release/reproducibility.md",
    "uv.lock",
    "web/package-lock.json",
    "web/public/finance-data/runtime-manifest.json",
}


def candidate_files() -> list[str]:
    result = subprocess.run(
        [
            "git",
            "ls-files",
            "--cached",
            "--others",
            "--exclude-standard",
        ],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    if result.returncode == 0:
        return sorted({line.replace("\\", "/") for line in result.stdout.splitlines()})

    # A release candidate may be inspected before its first `git init`. Use a
    # conservative filesystem view that mirrors the public artifact boundary;
    # once Git exists, the index remains the definitive release candidate.
    ignored_parts = {
        ".git",
        ".next",
        ".pytest_cache",
        ".ruff_cache",
        ".venv",
        ".vinext",
        ".wrangler",
        "__pycache__",
        "build",
        "coverage",
        "dist",
        "node_modules",
        "target",
    }
    ignored_patterns = (
        "*.duckdb",
        "*.log",
        "*.pbix",
        "*.pyc",
        "*.xlsx",
        ".test-tmp*/*",
        ".pytest-recovery*/*",
        "consumer-products/*/work/*",
        "consumer-products/*/exports/*",
        "PBI/*",
        "web/public/duckdb/*",
    )
    files: list[str] = []
    for directory, names, filenames in os.walk(ROOT):
        names[:] = [name for name in names if name not in ignored_parts]
        base = Path(directory)
        for filename in filenames:
            path = base / filename
            relative = path.relative_to(ROOT).as_posix()
            if any(fnmatch(relative, pattern) for pattern in ignored_patterns):
                continue
            files.append(relative)
    return sorted(files)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return f"sha256:{digest.hexdigest()}"


def main() -> int:
    errors: list[str] = []
    files = candidate_files()
    file_set = set(files)

    for required in sorted(REQUIRED - file_set):
        errors.append(f"required release file is missing: {required}")

    for child in ROOT.iterdir():
        if child.is_dir() and (child / ".git").exists():
            errors.append(f"nested Git repository is forbidden: {child.name}/.git")

    personal_path = re.compile(
        (r"[A-Za-z]:" + r"\\(?:Users|projects)" + r"\\[^\s\"']+").encode()
    )
    secret_patterns = (
        re.compile(("BEGIN " + "PRIVATE KEY").encode()),
        re.compile(("BEGIN RSA " + "PRIVATE KEY").encode()),
        re.compile(("sk" + r"-[A-Za-z0-9]{20,}").encode()),
        re.compile(("gh" + r"[pousr]_[A-Za-z0-9]{20,}").encode()),
        re.compile(("AKIA" + r"[A-Z0-9]{16}").encode()),
    )

    for relative in files:
        path = ROOT / relative
        if not path.is_file():
            continue
        if relative.startswith(FORBIDDEN_PREFIXES):
            errors.append(f"forbidden tracked path: {relative}")
        if relative.lower().endswith(FORBIDDEN_SUFFIXES):
            errors.append(f"forbidden tracked binary: {relative}")
        size = path.stat().st_size
        if size > MAX_TRACKED_BYTES:
            errors.append(f"tracked file exceeds 25 MB: {relative} ({size} bytes)")
        if path.suffix.lower() == ".parquet" and not relative.startswith(
            "web/public/finance-data/"
        ):
            errors.append(f"Parquet is only permitted in the v0.1 browser runtime: {relative}")
        if path.suffix.lower() in TEXT_SUFFIXES and size <= 5 * 1024 * 1024:
            payload = path.read_bytes()
            if personal_path.search(payload):
                errors.append(f"machine-specific absolute path found: {relative}")
            if any(pattern.search(payload) for pattern in secret_patterns):
                errors.append(f"credential signature found: {relative}")

    manifest_path = ROOT / "web/public/finance-data/runtime-manifest.json"
    if manifest_path.is_file():
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        integrity_rows = [
            item
            for table in manifest["runtimeTables"]
            for item in table["fileIntegrity"]
        ]
        if len(integrity_rows) != 114:
            count = len(integrity_rows)
            errors.append(
                "runtime manifest must authenticate 114 Parquet partitions, "
                f"found {count}"
            )
        for item in integrity_rows:
            relative = f"web/public{item['url']}"
            path = ROOT / relative
            if relative not in file_set or not path.is_file():
                errors.append(f"runtime file is missing from the release: {relative}")
                continue
            if path.stat().st_size != item["bytes"]:
                errors.append(f"runtime byte length mismatch: {relative}")
            if sha256(path) != item["digest"]:
                errors.append(f"runtime digest mismatch: {relative}")

    if errors:
        print("Public release check failed:")
        for error in errors:
            print(f"- {error}")
        return 1

    total_bytes = sum((ROOT / relative).stat().st_size for relative in files if (ROOT / relative).is_file())
    print(
        f"Public release check passed: {len(files)} files, {total_bytes:,} bytes, "
        "114 authenticated browser partitions."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
