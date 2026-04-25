"""Scientific artifact lineage helpers."""

from __future__ import annotations

from metaharness.provenance.evidence import ProvGraph, RelationKind


def attach_scientific_lineage(
    graph: ProvGraph,
    *,
    experiment_spec_id: str,
    run_plan_id: str,
    run_artifact_id: str,
    validation_report_id: str,
    evidence_bundle_id: str,
) -> None:
    graph.add_entity(id=experiment_spec_id, kind="experiment_spec")
    graph.add_entity(id=run_plan_id, kind="run_plan")
    graph.add_entity(id=run_artifact_id, kind="run_artifact")
    graph.add_entity(id=validation_report_id, kind="validation_report")
    graph.add_entity(id=evidence_bundle_id, kind="evidence_bundle")

    graph.relate(run_plan_id, RelationKind.WAS_DERIVED_FROM, experiment_spec_id)
    graph.relate(run_artifact_id, RelationKind.WAS_DERIVED_FROM, run_plan_id)
    graph.relate(validation_report_id, RelationKind.WAS_DERIVED_FROM, run_artifact_id)
    graph.relate(evidence_bundle_id, RelationKind.WAS_DERIVED_FROM, validation_report_id)
