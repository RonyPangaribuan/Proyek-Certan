from pathlib import Path
import subprocess
import sys

from proyek_certan.cli import main


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SAMPLE_INPUT = PROJECT_ROOT / "data" / "sample_incidents.json"


def test_cli_reads_sample_and_prints_required_sections(capsys) -> None:
    exit_code = main(["--input", str(SAMPLE_INPUT)])
    output = capsys.readouterr()

    assert exit_code == 0
    assert "Sistem Pendukung Keputusan Berbasis AI" in output.out
    assert "Importance Score Breakdown" in output.out
    assert "UCS Recommendation" in output.out
    assert "FIFO Comparison (non-search)" in output.out
    assert "States expanded" in output.out
    assert "Cost difference" in output.out
    assert "Cost reduction" in output.out
    assert output.err == ""


def test_cli_accepts_custom_weights(capsys) -> None:
    exit_code = main(
        [
            "--input",
            str(SAMPLE_INPUT),
            "--weight-urgency",
            "1",
            "--weight-impact",
            "0",
            "--weight-service-criticality",
            "0",
            "--weight-affected-users",
            "0",
            "--weight-waiting-time",
            "0",
        ]
    )

    assert exit_code == 0
    assert "UCS Recommendation" in capsys.readouterr().out


def test_cli_returns_nonzero_for_invalid_weights(capsys) -> None:
    exit_code = main(
        ["--input", str(SAMPLE_INPUT), "--weight-urgency", "0.20"]
    )
    output = capsys.readouterr()

    assert exit_code == 2
    assert "sum to 1.0" in output.err


def test_cli_returns_nonzero_for_missing_input(capsys, tmp_path) -> None:
    exit_code = main(["--input", str(tmp_path / "missing.json")])
    output = capsys.readouterr()

    assert exit_code == 2
    assert "Error:" in output.err


def test_python_module_entry_point_runs_successfully() -> None:
    completed = subprocess.run(
        [
            sys.executable,
            "-m",
            "proyek_certan",
            "--input",
            str(SAMPLE_INPUT),
        ],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )

    assert completed.returncode == 0, completed.stderr
    assert "UCS Recommendation" in completed.stdout
    assert "FIFO Comparison (non-search)" in completed.stdout
