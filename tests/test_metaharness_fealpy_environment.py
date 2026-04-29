from unittest.mock import patch

from metaharness_ext.fealpy.contracts import FealpyProblemSpec
from metaharness_ext.fealpy.environment import FealpyEnvironmentProbeComponent


def _spec() -> FealpyProblemSpec:
    return FealpyProblemSpec(
        task_id="env-test",
        pde_family="poisson",
        example_key=1,
        backend="numpy",
    )


def test_environment_probe_fealpy_available() -> None:
    component = FealpyEnvironmentProbeComponent()
    with patch.object(component, "_probe_fealpy_version", return_value="5.0.0"):
        with patch.object(
            component,
            "_probe_backends",
            return_value={"numpy": True, "pytorch": False, "jax": False},
        ):
            report = component.probe(_spec())
            assert report.available is True
            assert report.status == "available"
            assert report.fealpy_version == "5.0.0"
            assert "numpy" in report.available_backends
            assert report.blocks_promotion is False


def test_environment_probe_fealpy_missing() -> None:
    component = FealpyEnvironmentProbeComponent()
    with patch.object(component, "_probe_fealpy_version", return_value=None):
        with patch.object(
            component,
            "_probe_backends",
            return_value={"numpy": False, "pytorch": False, "jax": False},
        ):
            report = component.probe(_spec())
            assert report.available is False
            assert report.blocks_promotion is True
            assert len(report.missing_prerequisites) > 0


def test_environment_probe_requested_backend_unavailable() -> None:
    component = FealpyEnvironmentProbeComponent()
    spec = FealpyProblemSpec(task_id="env-test", backend="pytorch")
    with patch.object(component, "_probe_fealpy_version", return_value="5.0.0"):
        with patch.object(
            component,
            "_probe_backends",
            return_value={"numpy": True, "pytorch": False, "jax": False},
        ):
            report = component.probe(spec)
            assert report.available is False
            assert "pytorch" not in report.available_backends


def test_environment_probe_pde_families() -> None:
    families = FealpyEnvironmentProbeComponent.pde_families()
    assert "poisson" in families
    assert "stokes" in families
    assert "helmholtz" in families
    assert len(families) > 10


def test_environment_probe_returns_python_version() -> None:
    component = FealpyEnvironmentProbeComponent()
    with patch.object(component, "_probe_fealpy_version", return_value="5.0.0"):
        with patch.object(
            component,
            "_probe_backends",
            return_value={"numpy": True, "pytorch": False, "jax": False},
        ):
            report = component.probe(_spec())
            assert report.python_version is not None
            assert "." in report.python_version
