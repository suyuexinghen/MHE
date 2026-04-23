from pathlib import Path

from metaharness_ext.deepmd.collector import DPGenIterationCollector


def test_dpgen_collector_collects_iterations_and_counts(tmp_path: Path) -> None:
    run_dir = tmp_path / "dpgen-run"
    iteration_dir = run_dir / "iter.000000"
    (iteration_dir / "00.train").mkdir(parents=True)
    (iteration_dir / "01.model_devi").mkdir()
    (iteration_dir / "02.fp").mkdir()
    (run_dir / "record.dpgen").write_text(
        "candidate_count = 2\naccurate_count = 1\nfailed_count = 0\n"
    )
    (iteration_dir / "01.model_devi" / "stats.out").write_text(
        "candidate_count = 3\naccurate_count = 2\nfailed_count = 1\n"
    )

    collection = DPGenIterationCollector().collect(run_dir)

    assert collection.record_path == str(run_dir / "record.dpgen")
    assert len(collection.iterations) == 1
    assert collection.iterations[0].iteration_id == "iter.000000"
    assert collection.iterations[0].train_path == str(iteration_dir / "00.train")
    assert collection.iterations[0].model_devi_path == str(iteration_dir / "01.model_devi")
    assert collection.iterations[0].fp_path == str(iteration_dir / "02.fp")
    assert collection.candidate_count == 3
    assert collection.accurate_count == 2
    assert collection.failed_count == 1


def test_dpgen_collector_detects_relabeling_and_convergence(tmp_path: Path) -> None:
    run_dir = tmp_path / "dpgen-simplify"
    iteration_dir = run_dir / "iter.000000"
    (iteration_dir / "00.train").mkdir(parents=True)
    (iteration_dir / "01.model_devi").mkdir()
    (iteration_dir / "02.fp").mkdir()
    (run_dir / "record.dpgen").write_text(
        "candidate_count = 0\naccurate_count = 2\nfailed_count = 0\nconverged\n"
    )
    (iteration_dir / "02.fp" / "relabel.log").write_text("relabel pick_number = 4\n")

    collection = DPGenIterationCollector().collect(run_dir)

    assert any("relabel" in message.lower() for message in collection.messages)
    assert any("converged" in message.lower() for message in collection.messages)
