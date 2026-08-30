import { createHash } from "node:crypto";
import { readdirSync, readFileSync, statSync } from "node:fs";
import { join, relative } from "node:path";

const BUILD_INPUTS = ["app", "public", "package-lock.json", "next.config.ts"];

function hashPath(hash: ReturnType<typeof createHash>, path: string): void {
  const stats = statSync(path);
  if (stats.isDirectory()) {
    for (const name of readdirSync(path).sort()) {
      hashPath(hash, join(path, name));
    }
    return;
  }
  hash.update(relative(process.cwd(), path).replaceAll("\\", "/"));
  hash.update("\0");
  hash.update(readFileSync(path));
  hash.update("\0");
}

function deterministicBuildId(): string {
  const hash = createHash("sha256");
  for (const input of BUILD_INPUTS) hashPath(hash, join(process.cwd(), input));
  return hash.digest("hex").slice(0, 32);
}

const buildIdentity = deterministicBuildId();
const apiOrigin = process.env.FINANCE_ASSURANCE_API_ORIGIN?.replace(/\/$/, "");

const nextConfig = {
  deploymentId: buildIdentity,
  generateBuildId: async () => buildIdentity,
  async rewrites() {
    if (!apiOrigin) return [];
    return [
      {
        source: "/api/:path*",
        destination: `${apiOrigin}/api/:path*`,
      },
    ];
  },
};

export default nextConfig;
