"""Closed Artifact R Phase R1 profile and semantic registries."""

from __future__ import annotations

import re
from collections import defaultdict

from finance_assurance.analytics.registry import (
    DATASET_BY_ID as Q_DATASET_BY_ID,
)
from finance_assurance.analytics.registry import (
    DATASETS as Q_DATASETS,
)
from finance_assurance.analytics.registry import (
    RELATIONSHIPS as Q_RELATIONSHIPS,
)
from finance_assurance.digestion.contracts import (
    ColumnSemantic,
    DatasetCoordinate,
    MeasureDefinition,
    ProfileId,
    RelationshipKeyProjection,
    RelationshipPlanEntry,
)
from finance_assurance.exports.registry import (
    DATASET_BY_ID as P_DATASET_BY_ID,
)
from finance_assurance.exports.registry import (
    DATASETS as P_DATASETS,
)
from finance_assurance.exports.registry import (
    RELATIONSHIPS as P_RELATIONSHIPS,
)
from finance_assurance.runtime.canonical import canonical_sha256

R_CONTRACT_VERSION = "R-v0.2"

CORE_DATASETS = frozenset(
    {
        *(f"P-D{number:02d}" for number in range(1, 16)),
        "P-D20",
        "Q-D01",
        "Q-D02",
        "Q-D03",
        "Q-D04",
        "Q-D05",
        "Q-D07",
        "Q-D08",
        "Q-D09",
        "Q-D10",
        "Q-D15",
    }
)
LINEAGE_ADDITIONS = frozenset({"P-D16", "P-D17", "Q-D06", "Q-D11", "Q-D12"})
DIAGNOSTIC_ADDITIONS = frozenset(
    {"P-D18", "P-D19", "P-D21", "Q-D13", "Q-D14", "Q-D16"}
)

PROFILE_DATASET_IDS: dict[ProfileId, frozenset[str]] = {
    "CORE": CORE_DATASETS,
    "LINEAGE": CORE_DATASETS | LINEAGE_ADDITIONS,
    "DIAGNOSTIC": CORE_DATASETS | LINEAGE_ADDITIONS | DIAGNOSTIC_ADDITIONS,
}

PRIMARY_CONSUMPTION_CLASS = {
    **{dataset_id: "CORE" for dataset_id in CORE_DATASETS},
    **{dataset_id: "LINEAGE" for dataset_id in LINEAGE_ADDITIONS},
    **{dataset_id: "DIAGNOSTIC" for dataset_id in DIAGNOSTIC_ADDITIONS},
}

PHYSICAL_TYPE_MAP = {
    "text": "UTF8",
    "enum": "UTF8",
    "integer": "INT64",
    "boolean": "BOOLEAN",
    "date": "DATE32",
    "timestamp": "TIMESTAMP_US_UTC",
    "hash": "UTF8",
}

COMPOSITE_RELATIONSHIP_IDS = (
    "P-RL02",
    "P-RL03",
    "P-RL04",
    "P-RL05",
    "P-RL06",
    "P-RL07",
    "P-RL08",
    "P-RL10",
)

ACTIVE_RELATIONSHIP_IDS = frozenset(
    {
        "P-RL01-P-D03",
        "P-RL01-P-D04",
        "P-RL01-P-D05",
        "P-RL01-P-D08",
        "P-RL01-P-D09",
        "P-RL01-P-D13",
        "P-RL01-P-D15",
        "P-RL01-P-D16",
        "P-RL01-P-D17",
        "P-RL01-P-D21",
        "P-RL02",
        "P-RL03",
        "P-RL05",
        "P-RL07",
        "P-RL08",
        "P-RL09",
        "P-RL10",
        "P-RL13",
        "Q-RL03",
        "Q-RL04",
        "Q-RL05",
        "Q-RL06",
        "Q-RL07",
        "Q-RL08",
        "Q-RL09",
        "Q-RL10",
        "Q-RL11",
        "Q-RL13",
        "Q-RL14",
        "Q-RL15",
        "Q-RL24-Q-D04",
        "Q-RL24-Q-D07",
        "Q-RL24-Q-D08",
    }
)

SOURCE_TECHNICAL_DATASETS = frozenset(
    {"P-D18", "P-D19", "P-D21", "Q-D13", "Q-D14", "Q-D16"}
)
SOURCE_TECHNICAL_ORIGINS = frozenset(
    {
        "P_TRANSPORT_METADATA",
        "P_STRUCTURAL_METADATA",
        "O_QUERY_FIELD",
        "O_ENVELOPE_FIELD",
        "PACKAGE_STRUCTURAL_METADATA",
    }
)

_P_COORDINATES = tuple(
    DatasetCoordinate(
        registry_id="P-EVIDENCE",
        registry_version=1,
        dataset_id=item.dataset_id,
        dataset_version=1,
    )
    for item in P_DATASETS
)
_Q_COORDINATES = tuple(
    DatasetCoordinate(
        registry_id="Q-ANALYTICS",
        registry_version=1,
        dataset_id=item.dataset_id,
        dataset_version=1,
    )
    for item in Q_DATASETS
)
ALL_DATASET_COORDINATES = _P_COORDINATES + _Q_COORDINATES


def _coordinate(registry_id: str, dataset_id: str) -> DatasetCoordinate:
    return DatasetCoordinate(
        registry_id=registry_id,
        registry_version=1,
        dataset_id=dataset_id,
        dataset_version=1,
    )  # type: ignore[arg-type]


def _dataset(registry_id: str, dataset_id: str) -> object:
    if registry_id == "P-EVIDENCE":
        return P_DATASET_BY_ID[dataset_id]
    if registry_id == "Q-ANALYTICS":
        return Q_DATASET_BY_ID[dataset_id]
    raise KeyError(registry_id)


def _column(registry_id: str, dataset_id: str, column_name: str) -> object:
    definition = _dataset(registry_id, dataset_id)
    return next(item for item in definition.columns if item.name == column_name)  # type: ignore[attr-defined]


def datasets_for_profile(profile_id: ProfileId) -> tuple[DatasetCoordinate, ...]:
    selected = PROFILE_DATASET_IDS[profile_id]
    return tuple(
        item for item in ALL_DATASET_COORDINATES if item.dataset_id in selected
    )


def portable_alias(registry_id: str, dataset_id: str, dataset_name: str) -> str:
    normalized = re.sub(r"[^a-z0-9]+", "_", dataset_name.lower()).rstrip("_")
    alias = f"r_{normalized}"
    if len(alias) <= 63:
        return alias
    identity_hash = canonical_sha256(
        {"dataset_id": dataset_id, "registry_id": registry_id}
    ).removeprefix("sha256:")
    return f"{alias[:50]}_{identity_hash[:12]}"


def _relationship_by_id(relationship_id: str) -> dict[str, object]:
    return next(
        item
        for item in (*P_RELATIONSHIPS, *Q_RELATIONSHIPS)
        if item["relationship_id"] == relationship_id
    )


def _standard_column_types(
    relationship: dict[str, object], endpoint: str
) -> tuple[str, ...]:
    registry_id = str(relationship[f"{endpoint}_registry"])
    dataset_id = str(relationship[f"{endpoint}_dataset"])
    columns = tuple(str(item) for item in relationship[f"{endpoint}_columns"])
    return tuple(str(_column(registry_id, dataset_id, item).type) for item in columns)  # type: ignore[attr-defined]


RELATIONSHIP_KEY_PROJECTIONS = tuple(
    RelationshipKeyProjection(
        relationship_id=relationship_id,
        technical_column_name=f"_r_hk_{relationship_id.lower().replace('-', '_')}",
        from_coordinate=_coordinate(
            str(_relationship_by_id(relationship_id)["from_registry"]),
            str(_relationship_by_id(relationship_id)["from_dataset"]),
        ),
        from_columns=tuple(
            str(item) for item in _relationship_by_id(relationship_id)["from_columns"]
        ),
        from_types=_standard_column_types(
            _relationship_by_id(relationship_id), "from"
        ),
        to_coordinate=_coordinate(
            str(_relationship_by_id(relationship_id)["to_registry"]),
            str(_relationship_by_id(relationship_id)["to_dataset"]),
        ),
        to_columns=tuple(
            str(item) for item in _relationship_by_id(relationship_id)["to_columns"]
        ),
        to_types=_standard_column_types(_relationship_by_id(relationship_id), "to"),
        role="R_TECHNICAL",
        visibility="HIDDEN",
    )
    for relationship_id in COMPOSITE_RELATIONSHIP_IDS
)
KEY_PROJECTION_BY_RELATIONSHIP = {
    item.relationship_id: item for item in RELATIONSHIP_KEY_PROJECTIONS
}


def _relationship_is_relevant(
    relationship: dict[str, object], selected: frozenset[str]
) -> bool:
    if str(relationship["from_dataset"]) not in selected:
        return False
    if relationship["relationship_type"] == "STANDARD":
        return str(relationship["to_dataset"]) in selected
    targets = relationship["allowed_targets"]
    return any(str(item["dataset_id"]) in selected for item in targets)  # type: ignore[index]


def relationship_plan(profile_id: ProfileId) -> tuple[RelationshipPlanEntry, ...]:
    selected = PROFILE_DATASET_IDS[profile_id]
    result: list[RelationshipPlanEntry] = []
    for source in (*P_RELATIONSHIPS, *Q_RELATIONSHIPS):
        if not _relationship_is_relevant(source, selected):
            continue
        relationship_id = str(source["relationship_id"])
        enforcement = str(source["enforcement"])
        if enforcement == "INTEGRITY_ONLY":
            disposition = "VALIDATION_ONLY"
            reason = "UPSTREAM_INTEGRITY_OR_POLYMORPHIC_VALIDATION"
        elif relationship_id in ACTIVE_RELATIONSHIP_IDS:
            disposition = "ACTIVE"
            reason = "FINITE_ACTIVE_FILTER_PLAN"
        elif relationship_id == "P-RL04":
            disposition = "INACTIVE_ROLE_PLAYING"
            reason = "SUCCESSOR_REPORTING_VERSION_ROLE"
        else:
            disposition = "NAVIGATION_ONLY"
            reason = "REDUNDANT_OR_AMBIGUOUS_FILTER_PATH"
        relationship_type = str(source["relationship_type"])
        allowed_targets = ()
        if relationship_type == "POLYMORPHIC_PARENT":
            allowed_targets = tuple(
                _coordinate(str(item["registry_id"]), str(item["dataset_id"]))
                for item in source["allowed_targets"]  # type: ignore[index]
                if str(item["dataset_id"]) in selected
            )
        result.append(
            RelationshipPlanEntry(
                relationship_id=relationship_id,
                relationship_type=relationship_type,  # type: ignore[arg-type]
                enforcement=enforcement,  # type: ignore[arg-type]
                from_registry=str(source["from_registry"]),  # type: ignore[arg-type]
                from_dataset=str(source["from_dataset"]),
                from_columns=tuple(
                    str(item) for item in source.get("from_columns", ())
                ),
                to_registry=(
                    str(source["to_registry"])
                    if relationship_type == "STANDARD"
                    else None
                ),  # type: ignore[arg-type]
                to_dataset=(
                    str(source["to_dataset"])
                    if relationship_type == "STANDARD"
                    else None
                ),
                to_columns=tuple(str(item) for item in source.get("to_columns", ())),
                allowed_target_coordinates=allowed_targets,
                load_disposition=disposition,  # type: ignore[arg-type]
                relationship_role=(
                    "FILTER_PATH" if disposition == "ACTIVE" else disposition
                ),
                projected_key_ref=(
                    KEY_PROJECTION_BY_RELATIONSHIP[relationship_id].technical_column_name
                    if relationship_id in KEY_PROJECTION_BY_RELATIONSHIP
                    else None
                ),
                cross_filter_direction=(
                    "ONE_TO_MANY" if disposition == "ACTIVE" else "NONE"
                ),
                consumer_reason=reason,
            )
        )
    return tuple(result)


def _consumer_endpoint_fields() -> frozenset[tuple[str, str, str]]:
    result: set[tuple[str, str, str]] = set()
    for item in (*P_RELATIONSHIPS, *Q_RELATIONSHIPS):
        if item["enforcement"] != "CONSUMER_RELATIONSHIP":
            continue
        for endpoint in ("from", "to"):
            for column_name in item[f"{endpoint}_columns"]:
                result.add(
                    (
                        str(item[f"{endpoint}_registry"]),
                        str(item[f"{endpoint}_dataset"]),
                        str(column_name),
                    )
                )
    return frozenset(result)


MEASURE_SOURCE_FIELDS = frozenset(
    {
        ("P-EVIDENCE", "P-D06", "amount_minor"),
        ("P-EVIDENCE", "P-D07", "adjustment_minor"),
        ("P-EVIDENCE", "P-D04", "difference_minor"),
        ("P-EVIDENCE", "P-D08", "difference_minor"),
        ("P-EVIDENCE", "P-D11", "monthly_cost_minor"),
        ("P-EVIDENCE", "P-D13", "control_account_net_movement_minor"),
        ("Q-ANALYTICS", "Q-D04", "total_debit_minor"),
        ("Q-ANALYTICS", "Q-D04", "total_credit_minor"),
        ("Q-ANALYTICS", "Q-D05", "debit_minor"),
        ("Q-ANALYTICS", "Q-D05", "credit_minor"),
        ("Q-ANALYTICS", "Q-D09", "debit_minor"),
        ("Q-ANALYTICS", "Q-D09", "credit_minor"),
    }
)
CONSUMER_ENDPOINT_FIELDS = _consumer_endpoint_fields()


def _natural_key_fields() -> frozenset[tuple[str, str, str]]:
    result: set[tuple[str, str, str]] = set()
    for coordinate in ALL_DATASET_COORDINATES:
        definition = _dataset(coordinate.registry_id, coordinate.dataset_id)
        for key in definition.unique_keys:  # type: ignore[attr-defined]
            if tuple(key) == ("row_key",):
                continue
            result.update(
                (coordinate.registry_id, coordinate.dataset_id, str(column))
                for column in key
            )
    return frozenset(result)


NATURAL_KEY_FIELDS = _natural_key_fields()


def _source_column_semantic(
    coordinate: DatasetCoordinate, column: object
) -> ColumnSemantic:
    identity = (coordinate.registry_id, coordinate.dataset_id, column.name)  # type: ignore[attr-defined]
    name = str(column.name)  # type: ignore[attr-defined]
    source_type = str(column.type)  # type: ignore[attr-defined]
    origin = str(column.value_origin)  # type: ignore[attr-defined]
    evidence_tokens = ("hash", "evidence", "verification", "proof")
    if name == "row_key" or coordinate.dataset_id in SOURCE_TECHNICAL_DATASETS:
        role = "SOURCE_TECHNICAL"
    elif source_type == "hash" or any(token in name for token in evidence_tokens):
        role = "EVIDENCE_ATTRIBUTE"
    elif identity in MEASURE_SOURCE_FIELDS:
        role = "DOMAIN_MEASURE_INPUT"
    elif identity in NATURAL_KEY_FIELDS or identity in CONSUMER_ENDPOINT_FIELDS:
        role = "DOMAIN_KEY"
    elif origin in SOURCE_TECHNICAL_ORIGINS:
        role = "SOURCE_TECHNICAL"
    else:
        role = "DOMAIN_ATTRIBUTE"
    hidden = (
        role in {"SOURCE_TECHNICAL", "EVIDENCE_ATTRIBUTE", "DOMAIN_MEASURE_INPUT"}
        or source_type == "integer"
        or any(token in name for token in ("ordinal", "version", "revision"))
    )
    return ColumnSemantic(
        source_coordinate=coordinate,
        source_name=name,
        source_type=source_type,  # type: ignore[arg-type]
        physical_type=PHYSICAL_TYPE_MAP[source_type],  # type: ignore[arg-type]
        nullable=bool(column.nullable),  # type: ignore[attr-defined]
        enum_values=tuple(str(item) for item in column.enum_values),  # type: ignore[attr-defined]
        value_origin=origin,
        transformation=str(column.transformation),  # type: ignore[attr-defined]
        column_role=role,  # type: ignore[arg-type]
        default_visibility="HIDDEN" if hidden else "VISIBLE",
        default_summarization="NONE",
        display_label=name.replace("_", " ").title(),
        display_folder=None,
    )


SOURCE_COLUMN_REGISTRY = tuple(
    _source_column_semantic(coordinate, column)
    for coordinate in ALL_DATASET_COORDINATES
    for column in _dataset(coordinate.registry_id, coordinate.dataset_id).columns  # type: ignore[attr-defined]
)

R_TECHNICAL_COLUMN_REGISTRY = tuple(
    ColumnSemantic(
        source_coordinate=coordinate,
        source_name=projection.technical_column_name,
        source_type="hash",
        physical_type="UTF8",
        nullable=False,
        enum_values=(),
        value_origin="R_TECHNICAL_PROJECTION",
        transformation="COMPOSITE_RELATIONSHIP_HASH",
        column_role="R_TECHNICAL",
        default_visibility="HIDDEN",
        default_summarization="NONE",
        display_label=projection.technical_column_name,
        display_folder="Technical Relationships",
    )
    for projection in RELATIONSHIP_KEY_PROJECTIONS
    for coordinate in (projection.from_coordinate, projection.to_coordinate)
)

COLUMN_ROLE_REGISTRY = SOURCE_COLUMN_REGISTRY + R_TECHNICAL_COLUMN_REGISTRY


def _business_key(registry_id: str, dataset_id: str) -> tuple[str, ...]:
    definition = _dataset(registry_id, dataset_id)
    return next(
        tuple(str(item) for item in key)
        for key in definition.unique_keys  # type: ignore[attr-defined]
        if tuple(key) != ("row_key",)
    )


def _exact_measure(
    measure_id: str,
    measure_name: str,
    registry_id: str,
    dataset_id: str,
    source_field: str,
    population_class: str,
    reporting_version_policy: str = "NONE",
) -> MeasureDefinition:
    grain = _business_key(registry_id, dataset_id)
    return MeasureDefinition(
        measure_id=measure_id,
        measure_name=measure_name,
        source_registry_id=registry_id,  # type: ignore[arg-type]
        source_dataset_id=dataset_id,
        source_field=source_field,
        classification="EXACT_VALUE",
        aggregation="SELECT_EXACT",
        required_grain=grain,
        required_grouping=grain,
        currency_policy="SINGLE_EXACT_CURRENCY",
        reporting_version_policy=reporting_version_policy,  # type: ignore[arg-type]
        population_class=population_class,
        multirow_behavior="BLANK_OR_ERROR",
        non_combinable_with=(),
        default_format="INTEGER_MINOR_UNITS",
    )


def _additive_measure(
    measure_id: str,
    measure_name: str,
    dataset_id: str,
    source_field: str,
    population_class: str,
    non_combinable_with: tuple[str, ...],
) -> MeasureDefinition:
    return MeasureDefinition(
        measure_id=measure_id,
        measure_name=measure_name,
        source_registry_id="Q-ANALYTICS",
        source_dataset_id=dataset_id,
        source_field=source_field,
        classification="ADDITIVE_GOVERNED_TOTAL",
        aggregation="SUM",
        required_grain=_business_key("Q-ANALYTICS", dataset_id),
        required_grouping=("scenario_ref", "currency"),
        currency_policy="SINGLE_EXACT_CURRENCY",
        reporting_version_policy="NONE",
        population_class=population_class,
        multirow_behavior="SUM_SAME_CURRENCY",
        non_combinable_with=non_combinable_with,
        default_format="INTEGER_MINOR_UNITS_GROSS_ACTIVITY",
    )


MEASURE_REGISTRY = (
    _exact_measure(
        "R-M01",
        "Reporting Value Minor",
        "P-EVIDENCE",
        "P-D06",
        "amount_minor",
        "REPORTING_VALUE",
        "EXACT_REPORTING_VERSION",
    ),
    _exact_measure(
        "R-M02",
        "Restatement Adjustment Minor",
        "P-EVIDENCE",
        "P-D07",
        "adjustment_minor",
        "RESTATEMENT_BRIDGE",
        "EXACT_PREDECESSOR_SUCCESSOR_PAIR",
    ),
    _exact_measure(
        "R-M03",
        "Reconciliation Difference Minor",
        "P-EVIDENCE",
        "P-D04",
        "difference_minor",
        "SOURCE_RECONCILIATION",
    ),
    _exact_measure(
        "R-M04",
        "Exception Difference Minor",
        "P-EVIDENCE",
        "P-D08",
        "difference_minor",
        "ASSURANCE_EXCEPTION",
    ),
    _exact_measure(
        "R-M05",
        "Decision Monthly Cost Minor",
        "P-EVIDENCE",
        "P-D11",
        "monthly_cost_minor",
        "GOVERNED_DECISION",
    ),
    _exact_measure(
        "R-M06",
        "Correction Net Movement Minor",
        "P-EVIDENCE",
        "P-D13",
        "control_account_net_movement_minor",
        "CORRECTION_CASE",
    ),
    _exact_measure(
        "R-M07",
        "Journal Debits Minor",
        "Q-ANALYTICS",
        "Q-D04",
        "total_debit_minor",
        "AUTHORED_JOURNAL",
    ),
    _exact_measure(
        "R-M08",
        "Journal Credits Minor",
        "Q-ANALYTICS",
        "Q-D04",
        "total_credit_minor",
        "AUTHORED_JOURNAL",
    ),
    _additive_measure(
        "R-M09",
        "Authored Journal Line Debits Gross Activity",
        "Q-D05",
        "debit_minor",
        "AUTHORED_JOURNAL_LINE",
        ("R-M11", "R-M12"),
    ),
    _additive_measure(
        "R-M10",
        "Authored Journal Line Credits Gross Activity",
        "Q-D05",
        "credit_minor",
        "AUTHORED_JOURNAL_LINE",
        ("R-M11", "R-M12"),
    ),
    _additive_measure(
        "R-M11",
        "Referenced Journal Line Debits Gross Activity",
        "Q-D09",
        "debit_minor",
        "REFERENCED_JOURNAL_LINE",
        ("R-M09", "R-M10"),
    ),
    _additive_measure(
        "R-M12",
        "Referenced Journal Line Credits Gross Activity",
        "Q-D09",
        "credit_minor",
        "REFERENCED_JOURNAL_LINE",
        ("R-M09", "R-M10"),
    ),
)


def _active_edges(
    plan: tuple[RelationshipPlanEntry, ...],
) -> tuple[tuple[tuple[str, str], tuple[str, str]], ...]:
    return tuple(
        (
            (str(item.to_registry), str(item.to_dataset)),
            (item.from_registry, item.from_dataset),
        )
        for item in plan
        if item.load_disposition == "ACTIVE"
    )


def _assert_active_graph_is_safe(plan: tuple[RelationshipPlanEntry, ...]) -> None:
    graph: dict[tuple[str, str], set[tuple[str, str]]] = defaultdict(set)
    for source, target in _active_edges(plan):
        graph[source].add(target)
    nodes = set(graph) | {target for targets in graph.values() for target in targets}
    visiting: set[tuple[str, str]] = set()
    visited: set[tuple[str, str]] = set()

    def visit(node: tuple[str, str]) -> None:
        if node in visiting:
            raise ValueError("active relationship graph contains a cycle")
        if node in visited:
            return
        visiting.add(node)
        for child in graph[node]:
            visit(child)
        visiting.remove(node)
        visited.add(node)

    for node in nodes:
        visit(node)

    for start in nodes:
        path_counts: dict[tuple[str, str], int] = defaultdict(int)

        def count_paths(
            node: tuple[str, str], counts: dict[tuple[str, str], int] = path_counts
        ) -> None:
            for child in graph[node]:
                counts[child] += 1
                if counts[child] > 1:
                    raise ValueError("active relationship graph has duplicate paths")
                count_paths(child)

        count_paths(start)


def validate_relationship_graph(plan: tuple[RelationshipPlanEntry, ...]) -> None:
    """Public R1 guard for active-cycle and duplicate-path rejection."""

    _assert_active_graph_is_safe(plan)


def validate_registry() -> None:
    dataset_ids = {item.dataset_id for item in ALL_DATASET_COORDINATES}
    if len(ALL_DATASET_COORDINATES) != 37 or len(dataset_ids) != 37:
        raise ValueError("R requires exactly 37 source datasets")
    if set(PRIMARY_CONSUMPTION_CLASS) != dataset_ids:
        raise ValueError("dataset primary classifications are not closed")
    profile_counts = tuple(
        len(PROFILE_DATASET_IDS[item])
        for item in ("CORE", "LINEAGE", "DIAGNOSTIC")
    )
    if profile_counts != (
        26,
        31,
        37,
    ):
        raise ValueError("cumulative profile cardinalities are invalid")
    if len(SOURCE_COLUMN_REGISTRY) != 427:
        raise ValueError("R requires exactly 427 classified source columns")
    identities = {
        (
            item.source_coordinate.registry_id,
            item.source_coordinate.dataset_id,
            item.source_name,
        )
        for item in SOURCE_COLUMN_REGISTRY
    }
    if len(identities) != 427:
        raise ValueError("source-column classifications are not unique")
    if len(RELATIONSHIP_KEY_PROJECTIONS) != 8:
        raise ValueError("R requires exactly eight composite-key projections")
    projection_ids = tuple(
        item.relationship_id for item in RELATIONSHIP_KEY_PROJECTIONS
    )
    if projection_ids != COMPOSITE_RELATIONSHIP_IDS:
        raise ValueError("composite-key projection set is not exact")
    if len(MEASURE_REGISTRY) != 12:
        raise ValueError("R requires exactly twelve measures")
    if len({item.measure_id for item in MEASURE_REGISTRY}) != 12:
        raise ValueError("measure identities are not unique")
    aliases = [
        portable_alias(
            item.registry_id,
            item.dataset_id,
            _dataset(item.registry_id, item.dataset_id).name,  # type: ignore[attr-defined]
        )
        for item in ALL_DATASET_COORDINATES
    ]
    if len(set(aliases)) != 37:
        raise ValueError("portable physical aliases collide")
    full_plan = relationship_plan("DIAGNOSTIC")
    if len(full_plan) != 64:
        raise ValueError("R requires all 64 source relationships in DIAGNOSTIC")
    if sum(item.load_disposition == "ACTIVE" for item in full_plan) != 33:
        raise ValueError("R requires exactly 33 active relationships")
    if sum(item.load_disposition == "INACTIVE_ROLE_PLAYING" for item in full_plan) != 1:
        raise ValueError("R requires one inactive role-playing relationship")
    _assert_active_graph_is_safe(full_plan)


def registry_contract_hash() -> str:
    return canonical_sha256(
        {
            "column_roles": [
                item.model_dump(mode="json") for item in COLUMN_ROLE_REGISTRY
            ],
            "contract_version": R_CONTRACT_VERSION,
            "datasets": [
                item.model_dump(mode="json") for item in ALL_DATASET_COORDINATES
            ],
            "measures": [item.model_dump(mode="json") for item in MEASURE_REGISTRY],
            "profiles": {
                key: sorted(value) for key, value in PROFILE_DATASET_IDS.items()
            },
            "relationship_keys": [
                item.model_dump(mode="json") for item in RELATIONSHIP_KEY_PROJECTIONS
            ],
            "relationships": [
                item.model_dump(mode="json") for item in relationship_plan("DIAGNOSTIC")
            ],
        }
    )
