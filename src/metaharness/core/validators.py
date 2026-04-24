"""Semantic validation for graph snapshots."""

from __future__ import annotations

from collections import Counter, defaultdict

from metaharness.core.models import (
    GraphSnapshot,
    ValidationIssue,
    ValidationIssueCategory,
    ValidationReport,
)
from metaharness.sdk.registry import ComponentRegistry


def _is_protected_component(
    component_id: str,
    snapshot: GraphSnapshot,
    registry: ComponentRegistry,
) -> bool:
    node = next((node for node in snapshot.nodes if node.component_id == component_id), None)
    if node is not None and node.protected:
        return True
    return registry.is_protected(component_id)


def _incident_edges(
    snapshot: GraphSnapshot, component_id: str
) -> set[tuple[str, str, str, str, str]]:
    return {
        (
            edge.connection_id,
            edge.source,
            edge.target,
            edge.payload,
            edge.mode.value,
        )
        for edge in snapshot.edges
        if edge.source.rpartition(".")[0] == component_id
        or edge.target.rpartition(".")[0] == component_id
    }


def _protected_boundary_issues(
    snapshot: GraphSnapshot,
    registry: ComponentRegistry,
) -> list[ValidationIssue]:
    active_graph = registry.active_graph
    if active_graph is None:
        return []

    issues: list[ValidationIssue] = []
    active_nodes = {node.component_id for node in active_graph.nodes}
    candidate_nodes = {node.component_id for node in snapshot.nodes}
    protected_components = {
        component_id
        for component_id in active_nodes | candidate_nodes
        if _is_protected_component(component_id, active_graph, registry)
        or _is_protected_component(component_id, snapshot, registry)
    }

    for component_id in sorted(protected_components):
        if component_id in active_nodes and component_id not in candidate_nodes:
            issues.append(
                ValidationIssue(
                    code="protected_component_removed",
                    message="Protected component cannot be removed from the active graph",
                    subject=component_id,
                    category=ValidationIssueCategory.PROTECTED_COMPONENT,
                    blocks_promotion=True,
                )
            )
            continue
        if _incident_edges(active_graph, component_id) != _incident_edges(snapshot, component_id):
            issues.append(
                ValidationIssue(
                    code="protected_boundary_violation",
                    message="Protected component connections cannot be rewired",
                    subject=component_id,
                    category=ValidationIssueCategory.PROTECTED_COMPONENT,
                    blocks_promotion=True,
                )
            )
    return issues


def validate_graph(snapshot: GraphSnapshot, registry: ComponentRegistry) -> ValidationReport:
    """Validate a graph snapshot against registry declarations."""

    issues: list[ValidationIssue] = []
    node_ids = {node.component_id for node in snapshot.nodes}

    edge_ids = [edge.connection_id for edge in snapshot.edges]
    for edge_id, count in Counter(edge_ids).items():
        if count > 1:
            issues.append(
                ValidationIssue(
                    code="duplicate_connection", message="Duplicate connection id", subject=edge_id
                )
            )

    for node in snapshot.nodes:
        if node.component_id not in registry.components:
            issues.append(
                ValidationIssue(
                    code="unknown_component",
                    message="Component is not registered",
                    subject=node.component_id,
                )
            )

    incoming: dict[str, list[str]] = defaultdict(list)
    adjacency: dict[str, list[str]] = defaultdict(list)

    for edge in snapshot.edges:
        source_component, _, source_port = edge.source.rpartition(".")
        target_component, _, target_port = edge.target.rpartition(".")
        if source_component not in node_ids:
            issues.append(
                ValidationIssue(
                    code="unknown_source_component",
                    message="Connection source component is missing",
                    subject=edge.source,
                )
            )
        if target_component not in node_ids:
            issues.append(
                ValidationIssue(
                    code="unknown_target_component",
                    message="Connection target component is missing",
                    subject=edge.target,
                )
            )
        if source_component in node_ids and target_component in node_ids:
            adjacency[source_component].append(target_component)
            incoming[target_component].append(target_port)

        registered = registry.components.get(source_component)
        if registered and source_port:
            if source_port not in {port.name for port in registered.declarations.outputs}:
                issues.append(
                    ValidationIssue(
                        code="unknown_output_port",
                        message="Connection source port is not declared",
                        subject=edge.source,
                    )
                )
        registered = registry.components.get(target_component)
        if registered and target_port:
            declared_inputs = {port.name: port for port in registered.declarations.inputs}
            input_port = declared_inputs.get(target_port)
            if input_port is None:
                issues.append(
                    ValidationIssue(
                        code="unknown_input_port",
                        message="Connection target port is not declared",
                        subject=edge.target,
                    )
                )
            elif input_port.type != edge.payload:
                issues.append(
                    ValidationIssue(
                        code="payload_mismatch",
                        message="Connection payload does not match target input type",
                        subject=edge.connection_id,
                    )
                )

    for component_id, registered in registry.components.items():
        if component_id not in node_ids:
            continue
        required_inputs = {port.name for port in registered.declarations.inputs if port.required}
        bound_inputs = set(incoming.get(component_id, []))
        for missing in sorted(required_inputs - bound_inputs):
            issues.append(
                ValidationIssue(
                    code="missing_required_input",
                    message="Required input is not connected",
                    subject=f"{component_id}.{missing}",
                )
            )
        node = next(
            (n for n in snapshot.nodes if n.component_id == component_id),
            None,
        )
        node_protected = bool(node and node.protected)
        if registered.manifest.safety.protected or node_protected:
            for slot in registered.declarations.slots:
                if slot.binding == "primary":
                    bound = registry.slot_bindings.get(slot.slot, [])
                    if len(bound) > 1:
                        issues.append(
                            ValidationIssue(
                                code="protected_slot_override",
                                message="Protected primary slot has multiple bindings",
                                subject=slot.slot,
                                category=ValidationIssueCategory.PROTECTED_COMPONENT,
                                blocks_promotion=True,
                            )
                        )

    issues.extend(_protected_boundary_issues(snapshot, registry))

    visiting: set[str] = set()
    visited: set[str] = set()

    def has_cycle(node_id: str) -> bool:
        visiting.add(node_id)
        for neighbor in adjacency.get(node_id, []):
            if neighbor in visiting:
                return True
            if neighbor not in visited and has_cycle(neighbor):
                return True
        visiting.remove(node_id)
        visited.add(node_id)
        return False

    for component_id in node_ids:
        if component_id not in visited and has_cycle(component_id):
            issues.append(
                ValidationIssue(
                    code="cycle_detected",
                    message="Graph contains a cycle",
                    subject=component_id,
                    blocks_promotion=True,
                )
            )
            break

    referenced: set[str] = set()
    for edge in snapshot.edges:
        referenced.add(edge.source.rpartition(".")[0])
        referenced.add(edge.target.rpartition(".")[0])
    if len(snapshot.nodes) > 1:
        for node in snapshot.nodes:
            if node.component_id in referenced:
                continue
            registered = registry.components.get(node.component_id)
            # Components that declare no input ports cannot be targeted by
            # any connection; they participate through events or capability
            # lookups instead and are therefore not orphans.
            if registered is not None and not registered.declarations.inputs:
                continue
            issues.append(
                ValidationIssue(
                    code="orphan_component",
                    message="Component is not referenced by any connection",
                    subject=node.component_id,
                    blocks_promotion=True,
                )
            )

    return ValidationReport(valid=not issues, issues=issues)


def detect_orphans(snapshot: GraphSnapshot, registry: ComponentRegistry | None = None) -> list[str]:
    """Return component ids that are not referenced by any connection.

    Components declaring no input ports are not orphans since nothing could
    target them by design. Single-node graphs are always exempt.
    """

    referenced: set[str] = set()
    for edge in snapshot.edges:
        referenced.add(edge.source.rpartition(".")[0])
        referenced.add(edge.target.rpartition(".")[0])
    orphans: list[str] = []
    if len(snapshot.nodes) <= 1:
        return orphans
    for node in snapshot.nodes:
        if node.component_id in referenced:
            continue
        if registry is not None:
            registered = registry.components.get(node.component_id)
            if registered is not None and not registered.declarations.inputs:
                continue
        orphans.append(node.component_id)
    return orphans
