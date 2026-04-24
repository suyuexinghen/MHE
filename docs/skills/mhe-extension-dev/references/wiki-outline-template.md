# Wiki Outline Template

Use this template when creating a new MHE extension design wiki at:
`MHE/docs/wiki/meta-harness-engineer/<name>-engine-wiki/`

The wiki should answer **how the extension should be designed**, not how implementation is sequenced. Put phase-by-phase execution, remaining backlog, and current progress truth in numbered blueprint / roadmap / implementation-plan docs instead.

## Directory-Level Rules

- Keep the wiki focused on stable design boundaries.
- Prefer current code, tests, manifests, and formal blueprint docs over stale notes.
- If old blueprint/roadmap content still lives in the wiki, move it to numbered docs and leave only design-boundary guidance here.
- If the extension is still in development, say so explicitly in `README.md` without overstating readiness.
- Use one canonical page set; avoid mixing old and new page names unless you are actively migrating and can explain the split.

---

## Canonical Page Set

Pick the page set that matches the extension's current complexity.

### Option A: Full 9-page set

Use when the extension has multiple families, non-trivial runtime lifecycle, or meaningful I/O model constraints.

### 01-overview.md
```markdown
# <Name> Extension Overview

## 1. Extension Positioning
- target software and why MHE integrates it
- selected interface layer

## 2. Scope Boundaries
- supported application families
- explicit out-of-scope areas

## 3. Design Goals
- controllability
- typed boundary
- validation/evidence goals

## 4. MHE Integration Seams
- where it touches MHE core
- what MHE still owns vs what the extension owns
```

### 02-workflow-and-components.md
```markdown
# Workflow and Component Chain

## 1. Canonical Component Chain
- gateway -> environment -> compiler -> preprocessor/workspace -> executor -> validator -> evidence/policy

## 2. Component Responsibilities
### Gateway
### Environment
### Compiler
### Preprocessor / Workspace
### Executor
### Validator
### Evidence / Policy

## 3. Data Flow Between Components
- what each handoff produces
- what later stages are allowed to assume
```

### 03-contracts-and-artifacts.md
```markdown
# Contracts and Artifacts

## 1. Typed Input / Task Contracts
## 2. Family-Aware Contract Split
## 3. Run Plan
## 4. Run Artifact
## 5. Validation Surface
## 6. Evidence / Policy Surface
## 7. Key Data Models and Naming Constraints
```

### 04-environment-validation-and-evidence.md
```markdown
# Environment, Validation, and Evidence

## 1. Environment Probe Surface
## 2. Failure Taxonomy
## 3. Validation States
## 4. Evidence / Governance Seam
## 5. Non-short-circuit vs short-circuit decisions
## 6. What counts as executed vs scientifically accepted
```

### 05-family-design.md
```markdown
# Family Design

## 1. Why Family Is a First-Class Design Object
## 2. Supported Families
## 3. Per-Family Boundaries
## 4. Family vs Baseline Distinction
## 5. Current Tested Support Matrix
## 6. Family Extension Rules
```

### 06-packaging-and-registration.md
```markdown
# Packaging and Registration

## 1. Package Layout
## 2. Exports
## 3. Capabilities
## 4. Slots / Protected Boundary
## 5. Manifest Surface
## 6. Registration / Discovery Path
```

### 07-scope-and-boundaries.md
```markdown
# Scope and Boundaries

## 1. Wiki Responsibility
## 2. Blueprint Responsibility
## 3. Roadmap Responsibility
## 4. Implementation Plan Responsibility
## 5. `.trash` / historical docs responsibility
## 6. Not expanded in this wiki
```

### 08-runtime-lifecycle.md
```markdown
# Runtime Lifecycle

## 1. Canonical Lifecycle
## 2. Family Differences
## 3. From Task Spec to Outputs
## 4. Restart / Resume Semantics
## 5. Artifact and evidence checkpoints
```

### 09-core-objects-and-io-model.md
```markdown
# Core Objects and I/O Model

## 1. Core Input Objects
## 2. Asset Model
## 3. Output Root / Workspace Layout
## 4. Restart / Resume Objects
## 5. Evidence Model
```

### Option B: Compact 7-page set

Use when the extension does not need separate runtime lifecycle and I/O-model pages yet.

- `01-overview.md`
- `02-workflow-and-components.md`
- `03-contracts-and-artifacts.md`
- `04-environment-validation-and-evidence.md`
- `05-family-design.md`
- `06-packaging-and-registration.md`
- `07-scope-and-boundaries.md`

If you choose the compact set, fold runtime lifecycle and I/O-model material into pages 02–04 explicitly instead of omitting it silently.

---

## README.md Structure

The README is the main router for the wiki. It should state design scope, separate wiki vs blueprint vs roadmap responsibilities, and guide reading order.

Suggested structure:

```markdown
# <Name> Extension for MHE Wiki

> Version: v0.x | Last updated: YYYY-MM-DD

This directory discusses only **how to design `metaharness_ext.<name>` inside `MHE`**.

It focuses on extension-level design boundaries: application families, typed contracts, environment / validation / evidence surfaces, packaging / registration, and seams to the MHE governance path.

Important: **this extension may still be in active development and may not be fully implemented yet.**

This directory is **not** the main home for:
- phased implementation sequencing
- rollout / milestone narration
- current implementation status tracking
- blueprint / roadmap / implementation-plan prose mixed into design pages

That material should live in the numbered docs under `blueprint/`; historical material may live under `.trash/` if such a directory exists.

---

## Navigation
| Document | Topic | Audience |
|---|---|---|
| [01-overview](01-overview.md) | ... | Everyone |
| [02-workflow-and-components](02-workflow-and-components.md) | ... | Architects / runtime engineers |
| ... | ... | ... |

---

## Terminology
- define family / baseline / artifact / evidence / policy seam terms
- call out code-literal spellings when relevant

## Design Principles
- summarize the stable design stance
- explain what this wiki optimizes for

## Division of Responsibility with `blueprint/` and `.trash/`
- wiki = how the extension should be designed
- blueprint = formal design position
- roadmap = sequencing and remaining gaps
- implementation plan = one executable slice
- `.trash` = historical material outside the main reading path

## Recommended Reading Order
- boundary-first reading path
- runtime-semantics reading path
- family/registration reading path
- formal execution-material reading path

## Out of Scope for This Wiki
- upstream software manual
- full build/install guide
- daily rollout logs
- anything not necessary for extension design
```

README rules:
- include a truthfulness disclaimer when the extension is incomplete
- state scope boundaries vs blueprint / roadmap / implementation plan / `.trash`
- recommend a reading order, not just a file list
- keep design-boundary framing explicit
- if the wiki uses only `blueprint/` and no `.trash`, say that directly rather than copying `.trash` wording blindly

---

## Wiki Quality Checklist

Before considering a wiki page set done, verify:
- page names match the selected canonical set
- README accurately describes the actual file set
- no roadmap/backlog text is still the main content of a design page
- family names and execution modes match current code/doc truth
- support matrix language matches tested evidence, not future intent
- blueprint / roadmap references point to the numbered canonical docs
