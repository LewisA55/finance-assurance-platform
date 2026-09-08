# Reproducibility

## Fresh-clone product build

The public v0.1 repository contains the compact governed React runtime. A fresh
clone therefore needs only locked dependencies to validate and build the product:

```bash
uv sync --locked --dev
cd web
npm ci
npm test
```

`npm test` prepares exact DuckDB-Wasm chunks from the pinned npm package and a
digest-pinned signed Parquet extension from DuckDB's official repository, builds
the application and runs the rendered-route and hardening tests. The product
then serves the extension locally and disables further runtime installation.

## Full finance regeneration

The large synthetic population and warehouse are intentionally not committed.
Maintainers can reconstruct the complete authority chain with the versioned CLIs.

| Package | Digest |
|---|---|
| `ATLAS-FINANCE-STATUTORY-A24@v1` | `sha256:39af66f379d5497399f89e3956e601b6fb99a070146d8c6d378bb684f288b7e5` |
| `Q-FINANCE-C1@v1` | `sha256:16b7795117b7bba57f9d7f7fcb0b72dcdd36f346668611dddad4400a15ad5d8a` |
| `Q-FINANCE-C2@v1` | `sha256:7538132e08ea2b7e8c20f339db10e6c138cd2a08c71c4708c47c378d7c1b0141` |
| `PYTHIA-D6@v1` | `sha256:907f015413018c5badde7ca696177fd94b17df9653d907465655a2718991aac3` |

Build the source/Bronze package:

```bash
uv run finance-assurance-finance-data build \
  --data-ref ATLAS-FINANCE-STATUTORY-A24@v1 \
  --output build/finance-data-substrate/ATLAS-FINANCE-STATUTORY-A24-V1 \
  --built-at 2026-08-24T23:50:00Z \
  --scale-profile PORTFOLIO \
  --statutory-contract-version A2.4
```

Build the Silver/Gold model:

```bash
uv run finance-assurance-finance-model build \
  --source-package build/finance-data-substrate/ATLAS-FINANCE-STATUTORY-A24-V1 \
  --output build/finance-model/Q-FINANCE-C1-V1 \
  --expected-source-digest sha256:39af66f379d5497399f89e3956e601b6fb99a070146d8c6d378bb684f288b7e5 \
  --built-at 2026-08-25T00:15:00Z \
  --model-ref Q-FINANCE-C1@v1
```

The C2 delivery and Pythia CLIs then materialise the consumer package and
scenario authority. Their exact argument contracts are available through:

```bash
uv run finance-assurance-finance-delivery --help
uv run finance-assurance-pythia --help
```

Finally, refresh the versioned browser runtime from rebuilt C2 and Pythia packages:

```bash
cd web
npm ci
npm run sync:finance-data
npm run test:finance
```

The sync process republishes only after reading exact expected package references
and digests. Runtime tests independently replay row populations, financial
equations and physical file hashes.

## Determinism boundary

Package digests cover canonical records and declared metadata. Build outputs are
not source authority. Reproduction and verification operate from immutable inputs
and reject resealed mutations, missing provenance, population drift and control failures.
