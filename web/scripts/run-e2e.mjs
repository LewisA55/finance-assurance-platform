import { spawn, spawnSync } from "node:child_process";
import { existsSync } from "node:fs";
import net from "node:net";
import { dirname, join, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const webRoot = resolve(dirname(fileURLToPath(import.meta.url)), "..");
const repositoryRoot = resolve(webRoot, "..");
const python = process.platform === "win32"
  ? join(repositoryRoot, ".venv", "Scripts", "python.exe")
  : join(repositoryRoot, ".venv", "bin", "python");
const playwrightCli = join(webRoot, "node_modules", "@playwright", "test", "cli.js");
const host = "127.0.0.1";
const apiPort = 8100;
const webPort = 3100;
const children = [];
let stopping = false;

if (!existsSync(python)) {
  throw new Error("Locked Python environment unavailable; run uv sync --locked --dev first");
}

function portIsOpen(port) {
  return new Promise((resolvePort) => {
    const socket = net.createConnection({ host, port });
    socket.setTimeout(500);
    socket.once("connect", () => {
      socket.destroy();
      resolvePort(true);
    });
    const unavailable = () => {
      socket.destroy();
      resolvePort(false);
    };
    socket.once("error", unavailable);
    socket.once("timeout", unavailable);
  });
}

async function waitForPort(port, child) {
  const deadline = Date.now() + 120_000;
  while (Date.now() < deadline) {
    if (child.exitCode != null) {
      throw new Error(`E2E service for port ${port} stopped with exit code ${child.exitCode}`);
    }
    if (await portIsOpen(port)) return;
    await new Promise((resolveDelay) => setTimeout(resolveDelay, 250));
  }
  throw new Error(`Timed out waiting for E2E service on ${host}:${port}`);
}

function start(command, args, cwd, environment) {
  const child = spawn(command, args, {
    cwd,
    env: environment,
    stdio: "ignore",
    windowsHide: true,
    detached: process.platform !== "win32",
  });
  children.push(child);
  return child;
}

function stopTree(child) {
  if (child.exitCode != null || child.pid == null) return;
  if (process.platform === "win32") {
    child.kill();
    spawnSync("taskkill", ["/PID", String(child.pid), "/T", "/F"], {
      stdio: "ignore",
      timeout: 5_000,
    });
    child.unref();
    return;
  }
  try {
    process.kill(-child.pid, "SIGTERM");
  } catch {
    child.kill("SIGTERM");
  }
}

function stopWindowsPortListeners() {
  const result = spawnSync("netstat", ["-ano", "-p", "TCP"], { encoding: "utf8", timeout: 5_000 });
  const targetPorts = new Set([apiPort, webPort]);
  for (const line of result.stdout?.split(/\r?\n/) ?? []) {
    const match = line.match(/^\s*TCP\s+\S+:(\d+)\s+\S+\s+LISTENING\s+(\d+)\s*$/i);
    if (!match || !targetPorts.has(Number(match[1]))) continue;
    const pid = Number(match[2]);
    try {
      process.kill(pid);
    } catch {
      spawnSync("taskkill", ["/PID", String(pid), "/F"], { stdio: "ignore", timeout: 5_000 });
    }
  }
}

function cleanup() {
  if (stopping) return;
  stopping = true;
  for (const child of children.toReversed()) stopTree(child);
  if (process.platform === "win32") stopWindowsPortListeners();
}

for (const signal of ["SIGINT", "SIGTERM"]) {
  process.on(signal, () => {
    cleanup();
    process.exit(signal === "SIGINT" ? 130 : 143);
  });
}

async function main() {
  if (await portIsOpen(apiPort) || await portIsOpen(webPort)) {
    throw new Error(`E2E ports ${apiPort} and ${webPort} must be free before the isolated product starts`);
  }

  const environment = {
    ...process.env,
    FINANCE_ASSURANCE_DEMO_DB: join(repositoryRoot, "build", "public-demo.sqlite3"),
    FINANCE_ASSURANCE_API_ORIGIN: `http://${host}:${apiPort}`,
  };
  const api = start(
    python,
    ["-m", "uvicorn", "finance_assurance.product.server:app", "--host", host, "--port", String(apiPort)],
    repositoryRoot,
    environment,
  );
  await waitForPort(apiPort, api);
  const web = start(
    process.execPath,
    [join(webRoot, "node_modules", "vinext", "dist", "cli.js"), "dev", "--hostname", host, "--port", String(webPort)],
    webRoot,
    environment,
  );
  await waitForPort(webPort, web);

  const testRunner = spawn(process.execPath, [playwrightCli, "test", ...process.argv.slice(2)], {
    cwd: webRoot,
    env: { ...process.env, E2E_BASE_URL: `http://${host}:${webPort}` },
    stdio: "inherit",
    windowsHide: true,
  });
  const exitCode = await new Promise((resolveExit) => testRunner.once("exit", (code) => resolveExit(code ?? 1)));
  cleanup();
  process.exit(exitCode);
}

main().catch((error) => {
  cleanup();
  console.error(error instanceof Error ? error.message : String(error));
  process.exit(1);
});
