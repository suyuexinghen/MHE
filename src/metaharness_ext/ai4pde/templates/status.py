from __future__ import annotations

from metaharness_ext.ai4pde.templates.catalog import PDETemplate
from metaharness_ext.ai4pde.types import TemplateStatus


def can_instantiate_template(template: PDETemplate) -> bool:
    return template.status in {TemplateStatus.CANDIDATE, TemplateStatus.STABLE}


def promote_template_status(template: PDETemplate, *, successful_benchmarks: int) -> TemplateStatus:
    if successful_benchmarks >= 3:
        return TemplateStatus.STABLE
    if successful_benchmarks >= 1:
        return TemplateStatus.CANDIDATE
    return TemplateStatus.DRAFT
