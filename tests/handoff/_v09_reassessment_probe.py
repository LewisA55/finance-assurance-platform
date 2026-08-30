from __future__ import annotations

import importlib.util
import tempfile
from contextlib import suppress
from pathlib import Path

import duckdb

from finance_assurance.digestion.service import ConsumerModelService
from finance_assurance.handoff import split_sql_authority


class _TempFactory:
    def __init__(self, root: Path) -> None:
        self.root = root

    def mktemp(self, name: str) -> Path:
        path = self.root / name
        path.mkdir()
        return path


def main() -> None:
    source = Path(__file__).parents[1] / "digestion" / "test_phase_r2_service.py"
    spec = importlib.util.spec_from_file_location("r2_test_support", source)
    assert spec is not None and spec.loader is not None
    support = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(support)

    with tempfile.TemporaryDirectory(prefix="artifact-s-v09-reassessment-") as raw:
        root = Path(raw)
        fixture = support.source_package.__wrapped__(_TempFactory(root))
        package, package_digest = next(fixture)
        try:
            model = root / "lineage-model"
            result = ConsumerModelService().build(
                support._request(
                    package,
                    package_digest,
                    model,
                    formats=("CSV", "PARQUET", "DUCKDB"),
                )
            )
            database = model / "warehouse" / "finance-assurance.duckdb"
            connection = duckdb.connect(str(database), read_only=True)
            try:
                starter_counts = {
                    query_id: len(connection.execute(sql).fetchall())
                    for query_id, sql in split_sql_authority("starter-queries-v1.sql")
                }
                validations: dict[str, tuple[int, int]] = {}
                for query_id, sql in split_sql_authority(
                    "reconciliation-queries-v1.sql"
                ):
                    cursor = connection.execute(sql)
                    row = cursor.fetchone()
                    assert row is not None
                    names = tuple(item[0] for item in cursor.description)
                    assertions = [
                        value
                        for name, value in zip(names, row, strict=True)
                        if name.startswith("assert_")
                    ]
                    validations[query_id] = (
                        len(assertions),
                        sum(value is True for value in assertions),
                    )
            finally:
                connection.close()
            print("model_digest", result.model_digest)
            print("starter_counts", starter_counts)
            print("validation_assertions", validations)
            print("assertion_totals", sum(x for x, _ in validations.values()))
            print("assertion_true", sum(x for _, x in validations.values()))
        finally:
            with suppress(StopIteration):
                next(fixture)


if __name__ == "__main__":
    main()
