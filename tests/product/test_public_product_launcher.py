from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest

SCRIPT = Path(__file__).resolve().parents[2] / "public_product.py"
SPEC = importlib.util.spec_from_file_location("public_product_launcher", SCRIPT)
assert SPEC is not None and SPEC.loader is not None
public_product = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(public_product)


def _write_build(root: Path, *, preview: str, prerender: str, value: str) -> None:
    (root / "server" / "ssr").mkdir(parents=True)
    (root / "client").mkdir()
    (root / "client" / "product.js").write_text(value, encoding="utf-8")
    (root / "server" / "index.js").write_text(
        f"const preview=`{preview}`;const product='stable';",
        encoding="utf-8",
    )
    payload = json.dumps({"prerenderSecret": prerender})
    (root / "server" / "vinext-server.json").write_text(
        payload, encoding="utf-8"
    )
    (root / "server" / "ssr" / "vinext-server.json").write_text(
        payload, encoding="utf-8"
    )


def test_build_digest_normalizes_only_vinext_security_entropy(tmp_path: Path) -> None:
    first = tmp_path / "first"
    second = tmp_path / "second"
    _write_build(first, preview="a" * 32, prerender="b" * 64, value="product")
    _write_build(second, preview="c" * 32, prerender="d" * 64, value="product")

    assert public_product._tree_digest(first) == public_product._tree_digest(second)

    (second / "client" / "product.js").write_text("changed", encoding="utf-8")
    assert public_product._tree_digest(first) != public_product._tree_digest(second)


@pytest.mark.parametrize("secret", ["short", "g" * 64, "A" * 64])
def test_build_digest_rejects_unexpected_prerender_secret(
    tmp_path: Path, secret: str
) -> None:
    _write_build(
        tmp_path,
        preview="a" * 32,
        prerender=secret,
        value="product",
    )

    with pytest.raises(RuntimeError, match="unexpected prerender-secret shape"):
        public_product._tree_digest(tmp_path)


def test_build_digest_rejects_ambiguous_preview_identity(tmp_path: Path) -> None:
    _write_build(
        tmp_path,
        preview="a" * 32,
        prerender="b" * 64,
        value="product",
    )
    index = tmp_path / "server" / "index.js"
    index.write_text(
        index.read_text() + "const extra=`c" + "c" * 31 + "`;",
        encoding="utf-8",
    )

    with pytest.raises(RuntimeError, match="preview-mode identity count"):
        public_product._tree_digest(tmp_path)
