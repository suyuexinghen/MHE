"""Optimizer & self-growth engine for Meta-Harness."""

from metaharness.optimizer.action_space import (
    ActionLayer,
    ActionSpaceFunnel,
    CandidateAction,
)
from metaharness.optimizer.convergence import (
    ConvergenceCriterion,
    ConvergenceResult,
    DeadEndDetector,
    NonMarkovianGuard,
    TripleConvergence,
)
from metaharness.optimizer.encoder import GINEncoder, GraphEmbedding, NodeFeatures
from metaharness.optimizer.fitness import (
    FitnessEvaluator,
    NegativeRewardLoop,
    RewardComponents,
    composite_fitness,
)
from metaharness.optimizer.search.bayesian import BayesianOptimizer
from metaharness.optimizer.search.phase_a import LocalParameterSearch
from metaharness.optimizer.search.phase_b import TopologyTemplateSearch
from metaharness.optimizer.search.phase_c import ConstrainedSynthesis
from metaharness.optimizer.search.rl import RLEnhancement
from metaharness.optimizer.templates.codegen import CodegenPipeline, GeneratedArtifact
from metaharness.optimizer.templates.migration import (
    MigrationAdapter,
    MigrationAdapterSystem,
)
from metaharness.optimizer.templates.registry import (
    ComponentTemplate,
    TemplateRegistry,
)
from metaharness.optimizer.templates.slots import SlotBinding, SlotFillingEngine
from metaharness.optimizer.triggers import (
    LayeredTriggerSystem,
    Trigger,
    TriggerEvent,
    TriggerKind,
    TriggerThreshold,
)

__all__ = [
    "ActionLayer",
    "ActionSpaceFunnel",
    "BayesianOptimizer",
    "CandidateAction",
    "CodegenPipeline",
    "ComponentTemplate",
    "ConstrainedSynthesis",
    "ConvergenceCriterion",
    "ConvergenceResult",
    "DeadEndDetector",
    "FitnessEvaluator",
    "GINEncoder",
    "GeneratedArtifact",
    "GraphEmbedding",
    "LayeredTriggerSystem",
    "LocalParameterSearch",
    "MigrationAdapter",
    "MigrationAdapterSystem",
    "NegativeRewardLoop",
    "NodeFeatures",
    "NonMarkovianGuard",
    "RLEnhancement",
    "RewardComponents",
    "SlotBinding",
    "SlotFillingEngine",
    "TemplateRegistry",
    "TopologyTemplateSearch",
    "Trigger",
    "TriggerEvent",
    "TriggerKind",
    "TriggerThreshold",
    "TripleConvergence",
    "composite_fitness",
]
