# Historical Artifact S authority recovery

Status: Active recovery record

Date: 2026-08-29

The repository recovery restored the executable Artifact S v0.9 through v0.12
builders, logical resolvers, mutation contexts, and tests from the preserved
development record. The original generated metadata files were not recoverable
as bytes.

The restored builders reproduce the historical structure exactly:

- 31 LINEAGE tables;
- 388 governed columns;
- 10,663 field-provenance entries;
- complete source-document authentication in v0.11;
- private-copy mutation and independently derived first failures; and
- idempotent semantic reseals in v0.12.

All four mutation contexts reproduce their historical file and canonical-object
digests. Registry-derived metadata was regenerated from the recovered current
P, Q, and R source registries and therefore has new active byte authorities.
The original hashes remain in the dated milestone correction documents as
historical evidence; they were not rewritten or represented as reproduced.

| Authority | Recovered file SHA-256 | Recovered object SHA-256 |
|---|---|---|
| `metadata-positive-logical-vectors-v2.json` | `sha256:febfb07b82465ac8204db036d9fd758a023526d86faa4ff7ae70cf7662f3460b` | `sha256:f372e26b65872e9b64ec2e80266b8b14ce75c75623ee33990c076f5af722454d` |
| `metadata-positive-logical-vectors-v3.json` | `sha256:e2eafd5219822547e06513191165180ba7283bb44de342c60a79314579de945f` | `sha256:9568d76a28acd4c44eb881fa50022bc86ad3c1a6bdd693404decaae464a14268` |
| `metadata-positive-logical-vectors-v4.json` | `sha256:bcff1b1aabb2d94ce113178b192b12a6dd7187ff9315d33a2e80728ffaec98e8` | `sha256:117917c3ebbfb160086ece7c34d665b53cd4fdb9eb59088e393a32246c3dfc23` |

This is a recovery rebaseline, not a claim that the lost historical byte
streams were reproduced. Active tests pin the recovered authorities above.
