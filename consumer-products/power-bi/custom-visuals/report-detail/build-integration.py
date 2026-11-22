"""Replace the report's legacy grids and trends while retaining their queries."""
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "shared"))
import nexus_build as nb

GUID = "NexusReportDetail36313AD96E7F4E25A3F0C03834F7CFAA"
PAGES = ("45d6c278b45d4f468959", "4926286591b94aacac02", "8c5d16b8f8a74d18ac85",
         "bc4784caea56418190a2", "c0f28564b4824ff79b7c", "d4b82e6a1c7f49538a0d")
BRIDGES = {"bc4784caea56418190a2": "CASH", "c0f28564b4824ff79b7c": "MRR"}
ROLLFORWARD = "b7e4c1a9d3f84e2b9065"
SLIP = "00000000000000000017"
FOOT = "00000000000000000020"
PANEL_SIZE = 480
EVIDENCE_PAGE = "4926286591b94aacac02"
ASSURANCE_PAGE = "d4b82e6a1c7f49538a0d"


def emit_capabilities():
    roles = nb.roles(grouping=["period"], group_or_measure=["fields"], measure=["series"])
    nb.emit_package(HERE, roles, optional=set(), window=3000, name="nexusReportDetail",
                    display_name="Nexus Report Detail", guid=GUID,
                    description="Financial detail grid and time-series view with row-level evidence interaction.",
                    rgb=(25, 55, 79))
    path = HERE / "capabilities.json"
    spec = json.loads(path.read_text())
    mappings = []
    for conditions in (
        {"fields": {"min": 1, "max": 12}, "period": {"max": 0}, "series": {"max": 0}},
        {"fields": {"max": 0}, "period": {"min": 1, "max": 1}, "series": {"min": 1, "max": 3}},
    ):
        mappings.append({"conditions": [conditions], "table": {"rows": {
            "select": [{"for": {"in": role}} for role, bound in conditions.items() if bound["max"]],
            "dataReductionAlgorithm": {"window": {"count": 3000}},
        }}})
    spec["dataViewMappings"] = mappings
    nb.write_json(path, spec)


def replace_schedules(pages):
    candidates = [json.loads(p.read_text()) for p in (pages / ROLLFORWARD).glob("visuals/*/visual.json")]
    for page_id, key in BRIDGES.items():
        path = pages / page_id
        bridge = next(v for v in candidates if key in str(v.get("filterConfig", {}).get("filters", []))
                      and v.get("filterConfig", {}).get("filters", [])[0]["name"].endswith("_" + key))
        # These two strips were already pinned to the June close. Preserve that
        # pin and bind the full, independently checked rollforward query.
        updated = json.loads((path / "visuals" / SLIP / "visual.json").read_text())
        updated["visual"] = bridge["visual"]
        updated["filterConfig"] = {"filters": [*bridge["filterConfig"]["filters"],
                                              nb.filter_value("Period", "Period ID", "2026-06")]}
        updated["position"]["height"] = PANEL_SIZE
        nb.write_visual(page_id, updated)
        footer = json.loads((path / "visuals" / FOOT / "visual.json").read_text())
        footer["position"]["y"] = updated["position"]["y"] + PANEL_SIZE + 10
        nb.write_visual(page_id, footer)
        page = json.loads((path / "page.json").read_text())
        page["height"] = footer["position"]["y"] + footer["position"]["height"] + 10
        page["displayOption"] = "FitToWidth"
        nb.write_json(path / "page.json", page)


def replace_detail(pages):
    replaced = 0
    for page_id in PAGES:
        for path in (pages / page_id).glob("visuals/*/visual.json"):
            spec = json.loads(path.read_text())
            visual = spec["visual"]
            role_map = {"tableEx": {"Values": "fields"}, "lineChart": {"Category": "period", "Y": "series"}}
            roles = role_map.get(visual["visualType"])
            if roles is None and visual["visualType"] != GUID:
                continue
            if roles is not None:
                query = visual["query"]
                query["queryState"] = {roles[role]: binding for role, binding in query["queryState"].items()}
                visual["visualType"] = GUID
                visual.pop("objects", None)
                replaced += 1
            visual.setdefault("visualContainerObjects", {})["subTitle"] = [
                {"properties": {"show": {"expr": {"Literal": {"Value": "false"}}}}}
            ]
            nb.write_json(path, spec)
    print(f"Replaced {replaced} legacy table and trend bindings.")


def size_evidence(pages):
    path = pages / EVIDENCE_PAGE
    fields = sorted(path.glob("visuals/*/visual.json"))
    grids = [json.loads(f.read_text()) for f in fields]
    grids = [v for v in grids if v["visual"]["visualType"] == GUID]
    for i, v in enumerate(grids):
        v["position"].update(y=150 + 146 * i, height=140)
        nb.write_visual(EVIDENCE_PAGE, v)
    footer = json.loads((path / "visuals/00000000000000000015/visual.json").read_text())
    footer["position"]["y"] = 737
    nb.write_visual(EVIDENCE_PAGE, footer)
    page = json.loads((path / "page.json").read_text())
    page["height"] = 780
    nb.write_json(path / "page.json", page)


def size_exception_register(pages):
    path = pages / ASSURANCE_PAGE
    positions = {
        "d4b82e6a1c7f49538a11": (936, 112),
        "d4b82e6a1c7f49538a10": (1060, 350),
        "d4b82e6a1c7f49538a12": (1424, 260),
    }
    for visual_id, (y, height) in positions.items():
        v = json.loads((path / "visuals" / visual_id / "visual.json").read_text())
        v["position"].update(x=24, y=y, width=1232, height=height)
        nb.write_visual(ASSURANCE_PAGE, v)
    page = json.loads((path / "page.json").read_text())
    page["height"] = 1708
    nb.write_json(path / "page.json", page)


if __name__ == "__main__":
    emit_capabilities()
    root = nb.REPORT / "definition/pages"
    replace_schedules(root)
    replace_detail(root)
    size_evidence(root)
    size_exception_register(root)
