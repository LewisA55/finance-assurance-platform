"""Pinned Artifact S XLSX type, writer, and external audit profiles."""

from __future__ import annotations

from typing import Literal

from pydantic import model_validator

from finance_assurance.handoff.contracts import HandoffContractModel
from finance_assurance.runtime.canonical import canonical_sha256
from finance_assurance.runtime.contracts.primitives import AsciiString, HashValue

XLSX_TYPE_MAP_HASH = (
    "sha256:41b42f86d6620e042e1137b352fee44018ecfa34b980fb4bca4f33eeb71e48dd"
)
XLSX_WRITER_PROFILE_HASH = (
    "sha256:1a7dc795c0f09c22db462051c1190cf8b86dea7f03c6e79b4990fa1637c15f76"
)
AUDIT_RENDERER_PROFILE_HASH = (
    "sha256:24a2358b6b8ca7e64b9730943ad9564cff83560c9ec84a357344acb02adbf909"
)


class _HashedProfile(HandoffContractModel):
    @model_validator(mode="after")
    def exact_hash_matches(self) -> _HashedProfile:
        expected = {
            "XLSX-TYPE-MAP@v1": XLSX_TYPE_MAP_HASH,
            "XLSXWRITER-3.2.9@v1": XLSX_WRITER_PROFILE_HASH,
            "S-GRID-RENDERER-PILLOW-12.3.0-WIN-ARIAL@v1": (
                AUDIT_RENDERER_PROFILE_HASH
            ),
        }[str(self.profile_ref)]
        if canonical_sha256(self.model_dump(mode="json")) != expected:
            raise ValueError("profile body does not match its pinned hash")
        return self


class XlsxTypeMap(_HashedProfile):
    boolean: Literal["BOOLEAN_NATIVE"]
    date: Literal["TEXT_DATE_ISO"]
    date_format: Literal["YYYY-MM-DD"]
    enum: Literal["TEXT_EXACT"]
    hash: Literal["TEXT_EXACT"]
    integer_precision_digits: Literal[15]
    integer_safe: Literal["NUMBER_EXACT"]
    integer_unsafe: Literal["TEXT_INT64"]
    null: Literal["ABSENT_CELL"]
    profile_ref: Literal["XLSX-TYPE-MAP@v1"]
    text: Literal["TEXT_EXACT"]
    timestamp: Literal["TEXT_TIMESTAMP_UTC"]
    timestamp_format: Literal["YYYY-MM-DDTHH:MM:SS.ffffffZ"]


class XlsxWriterProfile(_HashedProfile):
    autofilter: Literal["TABLE_HEADER"]
    body_row_height: Literal[18]
    calculation_mode: Literal["MANUAL"]
    column_widths: dict[str, int]
    constant_memory: Literal[False]
    date_system: Literal["1900"]
    default_font_name: Literal["Arial"]
    default_font_size: Literal[10]
    document_properties: dict[str, AsciiString]
    external_feature_policy: Literal["FORBIDDEN"]
    formula_policy: Literal["FORBIDDEN"]
    freeze_panes: Literal["ROW_1"]
    header_row_height: Literal[22]
    header_style: Literal["Table Style Medium 2"]
    implementation: Literal["XlsxWriter"]
    implementation_version: Literal["3.2.9"]
    in_memory: Literal[True]
    nan_inf_to_errors: Literal[False]
    number_formats: dict[str, AsciiString]
    openxml_conformance: Literal["ECMA-376-5TH-EDITION-TRANSITIONAL"]
    profile_ref: Literal["XLSXWRITER-3.2.9@v1"]
    python_version: Literal["3.13.5"]
    remove_timezone: Literal[False]
    shared_strings: Literal[True]
    strings_to_formulas: Literal[False]
    strings_to_numbers: Literal[False]
    strings_to_urls: Literal[False]
    text_wrap: Literal["README_AND_METADATA_ONLY"]
    use_zip64: Literal[False]
    worksheet_order: Literal["FIVE_METADATA_THEN_R_MANIFEST_TABLE_ORDER"]
    zip_compression: Literal["DEFLATE"]
    zip_entry_order: Literal["XLSXWRITER_NATIVE"]
    zip_timestamp: Literal["1980-01-01T00:00:00"]


class AuditRendererProfile(_HashedProfile):
    background: Literal["#FFFFFF"]
    body_text: Literal["#000000"]
    cell_width_px: Literal[160]
    dpi: Literal[96]
    evidence_scope: Literal["EXTERNAL_REVISION_BOUND"]
    font_asset: Literal["arial.ttf"]
    font_asset_path_policy: Literal["S4_REQUEST_EXTERNAL_ABSOLUTE_FILE"]
    font_sha256: HashValue
    font_size_px: Literal[12]
    grid: Literal["#D9E2F3"]
    header_fill: Literal["#1F4E78"]
    header_text: Literal["#FFFFFF"]
    implementation: Literal["finance-assurance-xlsx-grid-renderer"]
    implementation_version: Literal["1"]
    locale: Literal["en-GB"]
    output_format: Literal["PNG_RGBA"]
    pillow_version: Literal["12.3.0"]
    platform: Literal["WINDOWS_AMD64"]
    png_compression_level: Literal[9]
    profile_ref: Literal["S-GRID-RENDERER-PILLOW-12.3.0-WIN-ARIAL@v1"]
    python_version: Literal["3.13.5"]
    row_height_px: Literal[22]
    tile_columns: Literal[12]
    tile_data_rows: Literal[60]
    timezone: Literal["UTC"]


XLSX_TYPE_MAP = XlsxTypeMap.model_validate(
    {
        "boolean": "BOOLEAN_NATIVE",
        "date": "TEXT_DATE_ISO",
        "date_format": "YYYY-MM-DD",
        "enum": "TEXT_EXACT",
        "hash": "TEXT_EXACT",
        "integer_precision_digits": 15,
        "integer_safe": "NUMBER_EXACT",
        "integer_unsafe": "TEXT_INT64",
        "null": "ABSENT_CELL",
        "profile_ref": "XLSX-TYPE-MAP@v1",
        "text": "TEXT_EXACT",
        "timestamp": "TEXT_TIMESTAMP_UTC",
        "timestamp_format": "YYYY-MM-DDTHH:MM:SS.ffffffZ",
    }
)

XLSX_WRITER_PROFILE = XlsxWriterProfile.model_validate(
    {
        "autofilter": "TABLE_HEADER",
        "body_row_height": 18,
        "calculation_mode": "MANUAL",
        "column_widths": {
            "BOOLEAN_NATIVE": 8,
            "NUMBER_EXACT": 18,
            "README_KEY": 28,
            "README_VALUE": 96,
            "TEXT_DATE_ISO": 12,
            "TEXT_EXACT": 24,
            "TEXT_INT64": 22,
            "TEXT_TIMESTAMP_UTC": 28,
        },
        "constant_memory": False,
        "date_system": "1900",
        "default_font_name": "Arial",
        "default_font_size": 10,
        "document_properties": {
            "author": "Finance & Assurance Platform",
            "category": "Synthetic analytical handoff",
            "comments": "R_SYNTHETIC_DATA_NOTICE",
            "company": "Finance & Assurance Platform",
            "created": "BUILD_REQUEST_BUILT_AT_UTC",
            "keywords": "synthetic,data-only,LINEAGE",
            "subject": "Local Analytical Handoff",
            "title": "Finance & Assurance Data Pack",
        },
        "external_feature_policy": "FORBIDDEN",
        "formula_policy": "FORBIDDEN",
        "freeze_panes": "ROW_1",
        "header_row_height": 22,
        "header_style": "Table Style Medium 2",
        "implementation": "XlsxWriter",
        "implementation_version": "3.2.9",
        "in_memory": True,
        "nan_inf_to_errors": False,
        "number_formats": {"BOOLEAN": "General", "INTEGER": "0", "TEXT": "@"},
        "openxml_conformance": "ECMA-376-5TH-EDITION-TRANSITIONAL",
        "profile_ref": "XLSXWRITER-3.2.9@v1",
        "python_version": "3.13.5",
        "remove_timezone": False,
        "shared_strings": True,
        "strings_to_formulas": False,
        "strings_to_numbers": False,
        "strings_to_urls": False,
        "text_wrap": "README_AND_METADATA_ONLY",
        "use_zip64": False,
        "worksheet_order": "FIVE_METADATA_THEN_R_MANIFEST_TABLE_ORDER",
        "zip_compression": "DEFLATE",
        "zip_entry_order": "XLSXWRITER_NATIVE",
        "zip_timestamp": "1980-01-01T00:00:00",
    }
)

AUDIT_RENDERER_PROFILE = AuditRendererProfile.model_validate(
    {
        "background": "#FFFFFF",
        "body_text": "#000000",
        "cell_width_px": 160,
        "dpi": 96,
        "evidence_scope": "EXTERNAL_REVISION_BOUND",
        "font_asset": "arial.ttf",
        "font_asset_path_policy": "S4_REQUEST_EXTERNAL_ABSOLUTE_FILE",
        "font_sha256": (
            "sha256:b3658eadae55e682b5f69eb64c439c1ecc8f196c0bb8d4756d145d13bc86476a"
        ),
        "font_size_px": 12,
        "grid": "#D9E2F3",
        "header_fill": "#1F4E78",
        "header_text": "#FFFFFF",
        "implementation": "finance-assurance-xlsx-grid-renderer",
        "implementation_version": "1",
        "locale": "en-GB",
        "output_format": "PNG_RGBA",
        "pillow_version": "12.3.0",
        "platform": "WINDOWS_AMD64",
        "png_compression_level": 9,
        "profile_ref": "S-GRID-RENDERER-PILLOW-12.3.0-WIN-ARIAL@v1",
        "python_version": "3.13.5",
        "row_height_px": 22,
        "tile_columns": 12,
        "tile_data_rows": 60,
        "timezone": "UTC",
    }
)
