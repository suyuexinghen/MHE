# MHE Test Guide

This guide describes the current verification layers for `MHE`, with an emphasis on the implemented DeepMD / DP-GEN extension APIs and their regression coverage.

## Prerequisites

- Python `>=3.11`
- `PYTHONPATH=MHE/src` when running from the repository root without an editable install
- Dev tools from `MHE[dev]` or equivalent local installs of `pytest` and `ruff`

Typical setup:

```bash
pip install -e ./MHE[dev]
```

## Core repo checks

Run the focused quality gates from the repository root:

```bash
ruff check MHE
ruff format --check MHE
PYTHONPATH=MHE/src pytest MHE/tests
```

By default, `pytest` excludes Nektar++ tests unless local solver binaries are installed.

## ABACUS directed test tier

The ABACUS extension has a focused directed suite that does not require a local ABACUS binary. Environment and execution behavior is covered with typed specs, patched probes, structured artifacts, and evidence-first validator fixtures.

Run the full ABACUS directed suite from the repository root:

```bash
PYTHONPATH=MHE/src pytest MHE/tests/test_metaharness_abacus_*.py -q
```

Focused ABACUS files:

```bash
PYTHONPATH=MHE/src pytest \
  MHE/tests/test_metaharness_abacus_manifest.py \
  MHE/tests/test_metaharness_abacus_gateway.py \
  MHE/tests/test_metaharness_abacus_environment.py \
  MHE/tests/test_metaharness_abacus_compiler.py \
  MHE/tests/test_metaharness_abacus_executor.py \
  MHE/tests/test_metaharness_abacus_validator.py \
  MHE/tests/test_metaharness_abacus_minimal_demo.py
```

Coverage focus:

- explicit manifest `policy.sandbox` / `policy.credentials` semantics
- typed SCF / NSCF / relax / MD task boundaries
- relax restart compatibility through typed `restart_file_path`
- deterministic `INPUT` rendering for params and relax controls
- required runtime asset grouping for pseudo, orbital, restart, charge-density, and `pot_file` inputs
- family-aware executor artifact discovery under `OUT.<suffix>/`
- evidence-first validator behavior, including strict NSCF `running_nscf.log` evidence and MD characteristic artifacts
- protected validator governance outputs: `issues`, `blocks_promotion`, `governance_state`, `ScoredEvidence`, and canonical `evidence_refs`

## DeepMD / DP-GEN test tiers

### Tier 1: Pure unit and mocked execution tests

These tests do not require installed `dp` or `dpgen` binaries. They patch subprocess execution or binary lookup and are the default regression layer for the DeepMD extension.

Recommended files:

```bash
PYTHONPATH=MHE/src pytest \
  MHE/tests/test_metaharness_deepmd_environment.py \
  MHE/tests/test_metaharness_deepmd_executor.py \
  MHE/tests/test_metaharness_dpgen_compiler.py \
  MHE/tests/test_metaharness_dpgen_collector.py \
  MHE/tests/test_metaharness_deepmd_validator.py \
  MHE/tests/test_metaharness_deepmd_evidence.py \
  MHE/tests/test_metaharness_deepmd_policy.py \
  MHE/tests/test_metaharness_deepmd_governance.py \
  MHE/tests/test_metaharness_deepmd_study.py \
  MHE/tests/test_metaharness_deepmd_minimal_demo.py
```

Coverage focus:

- family-aware environment checks for `deepmd_train`, `dpgen_run`, `dpgen_simplify`, and `dpgen_autotest`
- controlled compilation into `input.json`, `param.json`, and `machine.json`
- executor artifact collection and fallback failure shapes
- validator outputs including mode-aware statuses, `evidence_refs`, and `scored_evidence`
- evidence/policy review behavior for `allow`, `defer`, and `reject`
- governance adapter output, candidate promotion blocking, and runtime handoff
- study sweeps over supported typed mutation axes

### Tier 2: Runtime handoff regression tests

These tests still use patched command execution, but they validate that DeepMD extension outputs can be handed into the runtime promotion/session machinery.

Representative coverage lives in:

- `MHE/tests/test_metaharness_deepmd_minimal_demo.py`
- `MHE/tests/test_metaharness_deepmd_governance.py`

What they assert:

- `DeepMDGatewayComponent.run_baseline(...)` produces `core_validation_report` and `candidate_record`
- runtime handoff records candidate/session events through `HarnessRuntime.ingest_candidate_record(...)`
- current `CandidateRecord` payloads preserve runtime review state through `external_review`
- DeepMD validator output carries `scored_evidence` and stable `deepmd://...` evidence references

### Tier 3: Optional installed-binary smoke tests

The DeepMD test suite currently favors deterministic patched subprocess tests over mandatory local-binary execution. If you have local `dp` and `dpgen` installs and want an extra confidence pass, run the existing DeepMD demo-style regression modules and let the patched tests validate file/plan shapes.

Suggested smoke-oriented commands:

```bash
PYTHONPATH=MHE/src pytest MHE/tests/test_metaharness_deepmd_minimal_demo.py
PYTHONPATH=MHE/src pytest MHE/tests/test_metaharness_deepmd_study.py
```

If you add explicit installed-binary smoke tests later, keep them optional and skip them automatically when `dp` or `dpgen` is unavailable, following the same pattern the repo already uses for Nektar++ binary-gated coverage in `MHE/tests/conftest.py`.

## DeepMD surface summary

Current DeepMD public/testing surface:

- `DeepMDGatewayComponent.issue_task(...)` for the train baseline
- `DeepMDGatewayComponent.issue_dpgen_run_task(...)`
- `DeepMDGatewayComponent.issue_dpgen_simplify_task(...)`
- `DeepMDGatewayComponent.issue_dpgen_autotest_task(...)`
- `DeepMDGatewayComponent.run_baseline(...)` for baseline execution plus governance/runtime handoff
- `DeepMDStudyComponent.run_study(...)` for typed sweep studies

Current validated application families:

- `deepmd_train`
- `dpgen_run`
- `dpgen_simplify`
- `dpgen_autotest`

Current study mutation coverage:

- DeePMD: `numb_steps`, `rcut`, `rcut_smth`, `sel`
- DP-GEN run: `model_devi_f_trust_lo`, `model_devi_f_trust_hi`
- DP-GEN simplify: `relabeling.pick_number`

## Focused commands by area

### Validator / evidence / governance

```bash
PYTHONPATH=MHE/src pytest \
  MHE/tests/test_metaharness_deepmd_validator.py \
  MHE/tests/test_metaharness_deepmd_evidence.py \
  MHE/tests/test_metaharness_deepmd_policy.py \
  MHE/tests/test_metaharness_deepmd_governance.py
```

### DP-GEN compilers and execution

```bash
PYTHONPATH=MHE/src pytest \
  MHE/tests/test_metaharness_dpgen_compiler.py \
  MHE/tests/test_metaharness_dpgen_collector.py \
  MHE/tests/test_metaharness_dpgen_executor.py \
  MHE/tests/test_metaharness_deepmd_autotest.py
```

### Study and end-to-end demo wiring

```bash
PYTHONPATH=MHE/src pytest \
  MHE/tests/test_metaharness_deepmd_study.py \
  MHE/tests/test_metaharness_deepmd_minimal_demo.py
```

## What to look for

When reviewing DeepMD / DP-GEN test results, confirm:

- failures distinguish environment, workspace, runtime, and validation causes
- DP-GEN paths require iteration evidence before policy allows downstream review
- autotest paths require structured property evidence before policy allows downstream review
- validation reports expose stable `summary_metrics`, `evidence_refs`, and `scored_evidence`
- runtime handoff preserves candidate records and review state cleanly
- docs and tests only claim support for mutation axes that `study.py` actually mutates today
