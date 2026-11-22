"""Bind both comparison views to reproducibly materialised Power BI data."""
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "shared"))
import nexus_build as nb
from materialize import materialize

GUID = "NexusComparisonDE96413A903F4A7A8716560B4F2981C5"
NUMERIC = ["base", "middle", "end", "firstDelta", "secondDelta", "netDelta", "expected"]
TEXT = ["key", "mode", "groupKey", "groupLabel", "label", "period", "scope", "currency",
        "direction", "baseRef", "middleRef", "endRef", "evidence", "adapterDigest"]
ROLES = nb.roles(grouping=["key"], group_or_measure=TEXT[1:] + NUMERIC, measure=[])
PAGES = [
    ("3092b6abee574a1a90a1", "Planning Variance", "variance",
     "June 2026 management actuals and budget with a synthetic May forecast vintage."),
    ("3092b6abee574a1a90a2", "Restatement Comparator", "restatement",
     "C-001 accounting replay. Compare the original June publication with its approved republication."),
]


def m_value(value):
    if value is None:
        return "null"
    if isinstance(value, int):
        return str(value)
    return '"' + value.replace('"', '""') + '"'


def write_adapter(table, mode, all_rows):
    rows = [r for r in all_rows if r["mode"] == mode]
    fields = TEXT + NUMERIC
    schema = ", ".join(f'{f} = {"nullable number" if f in NUMERIC else "text"}' for f in fields)
    cells = ",\n        ".join("{" + ", ".join(m_value(r[f]) for f in fields) + "}" for r in rows)
    types = ", ".join('{"' + f + '", Int64.Type}' for f in NUMERIC)
    source = (
        "let\n"
        f"    Data = #table(type table [{schema}], {{\n        {cells}\n    }}),\n"
        f"    Typed = Table.TransformColumnTypes(Data, {{{types}}})\n"
        "in\n    Typed"
    )
    nb.assert_balanced(source, table)
    model = f"table '{table}'\n\n"
    for f in fields:
        model += (f"\tcolumn '{f}'\n\t\tdataType: {'int64' if f in NUMERIC else 'string'}\n"
                  f"\t\tsourceColumn: {f}\n\t\tsummarizeBy: none\n\t\tisHidden\n\n")
    model += f"\tpartition '{table}' = m\n\t\tmode: import\n\t\tsource =\n"
    model += "\n".join("\t\t\t" + line for line in source.splitlines()) + "\n"
    nb.write_table(table, model)
    nb.ref_tables([table])


def build():
    rows = materialize()
    nb.emit_package(HERE, ROLES, optional=set(), window=128, name="nexusComparison",
                    display_name="Nexus Financial Comparison", guid=GUID,
                    description="Two-stage management variance and version-bound restatement evidence.",
                    rgb=(22, 119, 110))
    for page_id, title, mode, subtitle in PAGES:
        table = title + " Data"
        write_adapter(table, mode, rows)
        nb.register_page(page_id, nb.page(page_id, title))
        nb.write_visual(page_id, nb.page_header(page_id[:-2] + "05", title, subtitle))
        v = nb.visual(page_id[:-2] + "06", GUID, 24, 96, 1232, 596)
        v["visual"]["query"] = {"queryState": {
            r: {"projections": [{"field": nb.field(table, r), "queryRef": f"{table}.{r}",
                                 "nativeQueryRef": r}]} for r in ROLES
        }}
        v["visual"]["visualContainerObjects"] = {
            "title": [{"properties": {"show": {"expr": {"Literal": {"Value": "false"}}}}}]
        }
        nb.write_visual(page_id, v)
    registry = nb.REPORT / "definition/pages/pages.json"
    pages = json.loads(registry.read_text())
    for (page_id, *_), after in zip(
        PAGES, ["8c5d16b8f8a74d18ac85", "e7c34d918b2a4f67905e"], strict=True
    ):
        pages["pageOrder"].remove(page_id)
        pages["pageOrder"].insert(pages["pageOrder"].index(after) + 1, page_id)
    nb.write_json(registry, pages)
    print(f'Materialised {len(rows)} rows, adapter digest {rows[0]["adapterDigest"]}.')


if __name__ == "__main__":
    build()
