from __future__ import annotations

import importlib.util
import json
from pathlib import Path
from zipfile import ZipFile

import pytest

MODULE_PATH = Path(__file__).resolve().parents[2] / "scripts" / "create_private_backup.py"
SPEC = importlib.util.spec_from_file_location("create_private_backup", MODULE_PATH)
assert SPEC is not None and SPEC.loader is not None
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)
create_private_backup = MODULE.create_private_backup


def test_private_backup_preserves_ignored_authoring_assets(tmp_path: Path) -> None:
    root = tmp_path / "repository"
    destination = tmp_path / "vault"
    workbook = root / "consumer-products" / "excel" / "work" / "model.xlsx"
    report = root / "consumer-products" / "power-bi" / "work" / "report.pbix"
    digest = root / "build" / "pythia" / "PYTHIA-D6-V1" / "pythia.digest"
    for path, content in ((workbook, b"xlsx"), (report, b"pbix"), (digest, b"sha256:test\n")):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(content)

    archive = create_private_backup(root, destination, label="test")
    with ZipFile(archive) as backup:
        names = set(backup.namelist())
        assert workbook.relative_to(root).as_posix() in names
        assert report.relative_to(root).as_posix() in names
        manifest = json.loads(backup.read("backup-manifest.json"))
        assert manifest["file_count"] == 3
        assert all(row["sha256"].startswith("sha256:") for row in manifest["files"])
    assert archive.with_suffix(".zip.sha256").is_file()


def test_private_backup_rejects_repository_destination(tmp_path: Path) -> None:
    root = tmp_path / "repository"
    source = root / "consumer-products" / "excel" / "work" / "model.xlsx"
    source.parent.mkdir(parents=True)
    source.write_bytes(b"xlsx")
    with pytest.raises(ValueError, match="outside the repository"):
        create_private_backup(root, root / "backup")
