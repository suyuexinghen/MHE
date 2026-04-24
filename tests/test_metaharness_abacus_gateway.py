from metaharness_ext.abacus.contracts import AbacusMdSpec
from metaharness_ext.abacus.gateway import AbacusGatewayComponent


def test_abacus_gateway_issues_md_task() -> None:
    gateway = AbacusGatewayComponent()

    task = gateway.issue_task(
        task_id="task-md",
        family="md",
        structure_content="ATOMIC_SPECIES\nSi 28.0 Si.upf\n",
        basis_type="pw",
        esolver_type="ksdft",
    )

    assert isinstance(task, AbacusMdSpec)
    assert task.application_family == "md"
    assert task.calculation == "md"
    assert task.basis_type == "pw"
    assert task.esolver_type == "ksdft"


def test_abacus_gateway_issues_md_dp_task_with_pot_file() -> None:
    gateway = AbacusGatewayComponent()

    task = gateway.issue_task(
        task_id="task-md-dp",
        family="md",
        structure_content="ATOMIC_SPECIES\nSi 28.0 Si.upf\n",
        basis_type="pw",
        esolver_type="dp",
        pot_file="/tmp/model.pb",
    )

    assert isinstance(task, AbacusMdSpec)
    assert task.esolver_type == "dp"
    assert task.pot_file == "/tmp/model.pb"
