"""Serve or verify the bounded local public product with one command."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import signal
import socket
import subprocess
import sys
import tempfile
import time
from collections.abc import Sequence
from pathlib import Path
from urllib.error import URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

PROJECT_ROOT = Path(__file__).resolve().parent
WEB_ROOT = PROJECT_ROOT / "web"
DEFAULT_HOST = "127.0.0.1"
DEFAULT_API_PORT = 8000
DEFAULT_WEB_PORT = 3000
BUILD_ID_INPUTS = ("app", "public", "package-lock.json", "next.config.ts")
GENERATED_RUNTIME_CHUNK = re.compile(
    r"^server/_next/static/"
    r"(app-page-cache|app-route-handler-dispatch|isr-cache|seed-cache)-"
    r"[A-Za-z0-9_-]+\.js$"
)


def _npm_executable() -> str:
    candidate = "npm.cmd" if os.name == "nt" else "npm"
    resolved = shutil.which(candidate)
    if resolved is None:
        raise RuntimeError("Node.js and npm are required to run the public product")
    return resolved


def _node_executable() -> str:
    candidate = "node.exe" if os.name == "nt" else "node"
    resolved = shutil.which(candidate)
    if resolved is None:
        raise RuntimeError("Node.js is required to run the public product")
    return resolved


def _vinext_cli() -> Path:
    cli = WEB_ROOT / "node_modules" / "vinext" / "dist" / "cli.js"
    if not cli.is_file():
        raise RuntimeError(
            "vinext is not installed; run `npm ci` in the web directory"
        )
    return cli


def _web_dev_command(*, host: str, port: int) -> list[str]:
    """Target the long-lived Node process directly, without an npm wrapper."""

    return [
        _node_executable(),
        str(_vinext_cli()),
        "dev",
        "--hostname",
        host,
        "--port",
        str(port),
    ]


def _process_options() -> dict[str, object]:
    if os.name == "nt":
        return {"creationflags": subprocess.CREATE_NEW_PROCESS_GROUP}
    return {"start_new_session": True}


def _start_process(
    command: Sequence[str],
    *,
    cwd: Path,
    environment: dict[str, str],
    quiet: bool,
) -> subprocess.Popen[bytes]:
    output = subprocess.DEVNULL if quiet else None
    return subprocess.Popen(
        list(command),
        cwd=cwd,
        env=environment,
        stdin=subprocess.DEVNULL,
        stdout=output,
        stderr=output,
        **_process_options(),
    )


def _stop_process(process: subprocess.Popen[bytes]) -> None:
    if process.poll() is not None:
        return
    if os.name == "nt":
        subprocess.run(
            ["taskkill", "/PID", str(process.pid), "/T", "/F"],
            check=False,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()
        return
    try:
        os.killpg(process.pid, signal.SIGTERM)
        process.wait(timeout=5)
    except (OSError, subprocess.TimeoutExpired):
        process.kill()
        process.wait(timeout=5)


def _remove_file_with_retry(path: Path, *, timeout: float = 5.0) -> None:
    deadline = time.monotonic() + timeout
    while True:
        try:
            path.unlink(missing_ok=True)
            return
        except PermissionError:
            if time.monotonic() >= deadline:
                raise
            time.sleep(0.1)


def _ensure_port_available(host: str, port: int) -> None:
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as probe:
            probe.bind((host, port))
    except OSError as error:
        raise RuntimeError(
            f"local port {host}:{port} is already in use; stop the existing "
            "service or choose another port"
        ) from error


def _wait_for_tcp(
    host: str,
    port: int,
    *,
    process: subprocess.Popen[bytes] | None = None,
    timeout: float = 45.0,
) -> None:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if process is not None and process.poll() is not None:
            raise RuntimeError(
                f"local service exited before opening {host}:{port}"
            )
        try:
            with socket.create_connection((host, port), timeout=0.5):
                return
        except OSError:
            time.sleep(0.2)
    raise RuntimeError(f"local service did not start on {host}:{port}")


def _get(url: str, *, timeout: float = 10.0) -> tuple[int, bytes, str]:
    request = Request(url, headers={"Accept": "application/json, text/html"})
    try:
        with urlopen(request, timeout=timeout) as response:
            return (
                response.status,
                response.read(),
                response.headers.get("content-type", ""),
            )
    except URLError as error:
        raise RuntimeError(f"local request failed: {url}") from error


def _deterministic_build_identity(root: Path) -> bytes | None:
    web_root = root.parent
    inputs = [web_root / relative for relative in BUILD_ID_INPUTS]
    if not all(path.exists() for path in inputs):
        return None
    digest = hashlib.sha256()

    def hash_path(path: Path) -> None:
        if path.is_dir():
            for child in sorted(path.iterdir(), key=lambda item: item.name):
                hash_path(child)
            return
        digest.update(path.relative_to(web_root).as_posix().encode("utf-8"))
        digest.update(b"\0")
        digest.update(path.read_bytes())
        digest.update(b"\0")

    for input_path in inputs:
        hash_path(input_path)
    return digest.hexdigest()[:32].encode("ascii")


def _canonical_build_bytes(root: Path, path: Path) -> bytes:
    relative_path = path.relative_to(root).as_posix()
    data = path.read_bytes()
    if relative_path in {
        "server/vinext-server.json",
        "server/ssr/vinext-server.json",
    }:
        payload = json.loads(data)
        if not re.fullmatch(r"[0-9a-f]{64}", payload.get("prerenderSecret", "")):
            raise RuntimeError(f"unexpected prerender-secret shape in {relative_path}")
        payload["prerenderSecret"] = "<generated-prerender-secret>"
        return json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    if relative_path == "server/index.js":
        identities = set(re.findall(rb"`([0-9a-f]{32})`", data))
        expected_build_identity = _deterministic_build_identity(root)
        if expected_build_identity is not None:
            identities.discard(expected_build_identity)
        if len(identities) != 1:
            raise RuntimeError(
                "unexpected preview-mode identity count in server/index.js"
            )
        preview_identity = next(iter(identities))
        canonical = data.replace(
            b"`" + preview_identity + b"`",
            b"`<generated-preview-mode-id>`",
        )
        canonical = re.sub(
            rb"(app-page-cache|app-route-handler-dispatch|isr-cache|seed-cache)-"
            rb"[A-Za-z0-9_-]+\.js",
            lambda match: match.group(1) + b"-<generated-runtime-seed>.js",
            canonical,
        )
        return canonical
    return data


def _tree_digest(root: Path) -> str:
    digest = hashlib.sha256()
    files = sorted(
        path
        for path in root.rglob("*")
        if path.is_file()
        and not GENERATED_RUNTIME_CHUNK.fullmatch(path.relative_to(root).as_posix())
    )
    if not files:
        raise RuntimeError(f"build produced no files under {root}")
    for path in files:
        digest.update(path.relative_to(root).as_posix().encode("utf-8"))
        digest.update(b"\0")
        digest.update(_canonical_build_bytes(root, path))
        digest.update(b"\0")
    return digest.hexdigest()


def _run_build() -> str:
    subprocess.run(
        [_npm_executable(), "run", "build"],
        cwd=WEB_ROOT,
        check=True,
    )
    return _tree_digest(WEB_ROOT / "dist")


def _launch(
    *,
    host: str,
    api_port: int,
    web_port: int,
    database: Path,
    quiet: bool,
) -> tuple[subprocess.Popen[bytes], subprocess.Popen[bytes]]:
    _ensure_port_available(host, api_port)
    _ensure_port_available(host, web_port)

    environment = os.environ.copy()
    environment["FINANCE_ASSURANCE_DEMO_DB"] = str(database.resolve())
    environment["FINANCE_ASSURANCE_API_ORIGIN"] = f"http://{host}:{api_port}"

    api = _start_process(
        [
            sys.executable,
            "-m",
            "uvicorn",
            "finance_assurance.product.server:app",
            "--host",
            host,
            "--port",
            str(api_port),
        ],
        cwd=PROJECT_ROOT,
        environment=environment,
        quiet=quiet,
    )
    web: subprocess.Popen[bytes] | None = None
    try:
        _wait_for_tcp(host, api_port, process=api)
        web = _start_process(
            _web_dev_command(host=host, port=web_port),
            cwd=WEB_ROOT,
            environment=environment,
            quiet=quiet,
        )
        _wait_for_tcp(host, web_port, process=web)
    except Exception:
        if web is not None:
            _stop_process(web)
        _stop_process(api)
        raise
    assert web is not None
    return api, web


def serve(*, host: str, api_port: int, web_port: int) -> int:
    database = PROJECT_ROOT / "build" / "public-demo.sqlite3"
    database.parent.mkdir(parents=True, exist_ok=True)
    api, web = _launch(
        host=host,
        api_port=api_port,
        web_port=web_port,
        database=database,
        quiet=False,
    )
    print(f"Public product: http://{host}:{web_port}")
    print("Press Ctrl+C to stop both local services.")
    try:
        while api.poll() is None and web.poll() is None:
            time.sleep(0.5)
        raise RuntimeError("a local public-product service stopped unexpectedly")
    except KeyboardInterrupt:
        return 0
    finally:
        _stop_process(web)
        _stop_process(api)


def _verify_live_product(*, host: str, web_port: int) -> None:
    query = urlencode(
        {
            "view_contract_version": "1",
            "scenario_ref": "DEMO-C001-RESTATEMENT@v1",
            "semantic_as_of_time": "2026-07-14T12:00:00Z",
        }
    )
    status, body, content_type = _get(f"http://{host}:{web_port}/")
    if status != 200 or "text/html" not in content_type:
        raise RuntimeError("public shell did not return its HTML contract")
    if b"Nexus Technologies" not in body or b"CFO Command Centre" not in body:
        raise RuntimeError("public shell omitted the product identity")

    status, body, content_type = _get(
        f"http://{host}:{web_port}/api/v1/demo?{query}"
    )
    if status != 200 or "application/json" not in content_type:
        raise RuntimeError("same-origin public API did not return JSON")
    payload = json.loads(body)
    if payload.get("view_contract") != "O-V01":
        raise RuntimeError("same-origin public API returned the wrong contract")
    if payload.get("compatibility_read_mode") != "EXACT_ORIGINAL":
        raise RuntimeError("same-origin public API weakened compatibility mode")


def verify(*, host: str, api_port: int, web_port: int) -> int:
    first_digest = _run_build()
    second_digest = _run_build()
    if first_digest != second_digest:
        raise RuntimeError("two canonical public builds were not byte-identical")

    with tempfile.TemporaryDirectory(prefix="finance-assurance-public-") as directory:
        database = Path(directory) / "public-demo.sqlite3"
        api, web = _launch(
            host=host,
            api_port=api_port,
            web_port=web_port,
            database=database,
            quiet=True,
        )
        try:
            _verify_live_product(host=host, web_port=web_port)
        finally:
            _stop_process(web)
            _stop_process(api)
            _remove_file_with_retry(database)

    print(f"Deterministic application build: {first_digest}")
    print(
        "Generated preview and prerender security salts: "
        "shape-checked and normalized"
    )
    print("Local startup: verified")
    print("Same-origin O-V01 boundary: EXACT_ORIGINAL")
    return 0


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Serve or verify the deterministic public portfolio product."
    )
    parser.add_argument("action", choices=("serve", "verify"))
    parser.add_argument("--host", default=DEFAULT_HOST)
    parser.add_argument("--api-port", type=int, default=DEFAULT_API_PORT)
    parser.add_argument("--web-port", type=int, default=DEFAULT_WEB_PORT)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    arguments = _parser().parse_args(argv)
    if arguments.action == "serve":
        return serve(
            host=arguments.host,
            api_port=arguments.api_port,
            web_port=arguments.web_port,
        )
    return verify(
        host=arguments.host,
        api_port=arguments.api_port,
        web_port=arguments.web_port,
    )


if __name__ == "__main__":
    raise SystemExit(main())
