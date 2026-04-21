# API Stability Guarantees

Meta-Harness follows a tiered stability model. The tier a symbol
belongs to is encoded in the module path, not in its name, so you can
reason about stability with a quick glance at your imports.

## 1. Stability Tiers

| Tier | Module prefix | Stability contract |
|---|---|---|
| **Stable** | `metaharness.sdk.*`, `metaharness.core.*`, `metaharness.safety.*`, `metaharness.hotreload.*`, `metaharness.observability.*`, `metaharness.provenance.*` | Breaking changes only at a major version bump. Deprecation warnings for at least one minor release. |
| **Experimental** | `metaharness.optimizer.*` | Semantically stable signatures; may evolve between minor releases with migration notes in the changelog. |
| **Internal** | `metaharness._*`, anything under `*.internal.*` | No guarantees. Do not import from outside the package. |

Components, manifests, and XML schema files are treated as **stable**.
Bundled baseline manifests may gain new optional fields; required
fields will only change across major versions.

## 2. Versioning Scheme

Meta-Harness uses SemVer:

- `X.Y.Z` — regular release.
- Backward-compatible additions (new optional fields, new gates,
  new search strategies) bump `Y`.
- Bug fixes and documentation updates bump `Z`.
- Anything that renames an exported symbol, changes a method
  signature, or removes a public class bumps `X`.

## 3. Deprecation Policy

1. A replacement symbol must exist and be documented.
2. The deprecated symbol emits `DeprecationWarning` on first use and
   stays available for at least one minor release.
3. The `CHANGELOG` entry describes the removal timeline.
4. Removal happens in a major release only.

## 4. Back-Compat Aliases Already in the Tree

| Old symbol | Replacement | Removed in |
|---|---|---|
| `ComponentKind` | `ComponentType` | TBD (still present as alias) |
| `GraphVersionStore.commit(...)` with bare snapshot | `GraphVersionManager.cutover(snapshot)` | TBD (still present) |

## 5. Wire Formats

- **Graph XML** (`examples/graphs/*.xml`) — schema versioned via the
  `schemaVersion` attribute. Parsers must accept any schema version
  listed in `CHANGELOG`.
- **Manifest JSON** — schema version implied by `harness_version`.
  Static validation rejects manifests requiring a newer runtime.
- **Audit log JSONL** — append-only; every line carries a
  `merkle_index` and the root hash at insertion time, so consumers
  can detect truncation or tampering.

## 6. Run-Time Compatibility

The runtime will refuse to load a component whose manifest specifies
a `harness_version` the runtime cannot satisfy. `validate_manifest_static`
always runs before registration, so incompatible plugins never reach
production.

## 7. Contributing Changes

When adding a public symbol:

1. Export it from the owning package's `__init__.py`.
2. Add a test against the public import path.
3. Mention it in the changelog under the appropriate tier.

When removing a public symbol, follow the deprecation policy above
and update `ROADMAP_STATUS.md` so the roadmap matrix stays aligned
with the tree.
