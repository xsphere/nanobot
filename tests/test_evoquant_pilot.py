from pathlib import Path

from typer.testing import CliRunner

from nanobot.cli.commands import app
from nanobot.evoquant import TaskConfig, run_evolution


runner = CliRunner()


def test_run_evolution_generates_candidates_and_reports(tmp_path: Path):
    cfg = TaskConfig(
        run_id="pytest-run",
        generations=2,
        population_size=8,
        top_k=2,
        output_dir=str(tmp_path),
        seed=7,
    )

    result = run_evolution(cfg)

    assert result.config.run_id == "pytest-run"
    assert len(result.reports) > 0
    assert len(result.top_candidates) <= 2
    assert (tmp_path / "pytest-run" / "report.json").exists()
    assert result.memory_updates["alpha_zoo"] >= 1


def test_cli_evoquant_run(tmp_path: Path):
    out_dir = tmp_path / "runs"
    cli_result = runner.invoke(
        app,
        [
            "evoquant-run",
            "--run-id",
            "cli-run",
            "--generations",
            "2",
            "--population",
            "8",
            "--top-k",
            "2",
            "--output-dir",
            str(out_dir),
            "--seed",
            "9",
        ],
    )

    assert cli_result.exit_code == 0
    assert "EvoQuant run finished" in cli_result.stdout
    assert (out_dir / "cli-run" / "report.json").exists()
