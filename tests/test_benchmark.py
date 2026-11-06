import csv
from dataclasses import fields, replace
from pathlib import Path

import pytest

import proyek_certan.constraint_solver.benchmark as benchmark_module
from proyek_certan.constraint_solver.benchmark import (
    CSV_FIELDS,
    BenchmarkResult,
    benchmark_scenario,
    build_scenarios,
    format_results,
    run_benchmarks,
    write_csv,
)
from proyek_certan.constraint_solver.incident_assignment import (
    load_technicians,
)
from proyek_certan.io import load_incidents


PROJECT_ROOT = Path(__file__).resolve().parents[1]
INCIDENT_PATH = PROJECT_ROOT / "data" / "sample_incidents.json"
TECHNICIAN_PATH = PROJECT_ROOT / "data" / "sample_technicians.json"


def _load_data():
    return load_incidents(INCIDENT_PATH), load_technicians(TECHNICIAN_PATH)


def test_scenarios_use_ordered_prefixes_of_four_eight_and_twelve() -> None:
    incidents, _ = _load_data()

    scenarios = build_scenarios(incidents)

    assert tuple(size for size, _ in scenarios) == ("Small", "Medium", "Large")
    assert tuple(len(subset) for _, subset in scenarios) == (4, 8, 12)
    for _, subset in scenarios:
        assert tuple(item.incident_id for item in subset) == tuple(
            item.incident_id for item in incidents[: len(subset)]
        )


@pytest.mark.parametrize("runs", [0, -1])
def test_non_positive_runs_are_rejected(runs: int) -> None:
    incidents, technicians = _load_data()

    with pytest.raises(ValueError, match="runs must be greater than 0"):
        run_benchmarks(incidents, technicians, runs)


def test_results_contain_all_required_solver_statistics() -> None:
    incidents, technicians = _load_data()

    results = run_benchmarks(incidents, technicians, runs=1)

    assert tuple(field.name for field in fields(BenchmarkResult)) == CSV_FIELDS
    assert tuple(result.status for result in results) == (
        "solved",
        "solved",
        "solved",
    )
    for result in results:
        assert result.min_runtime_ms <= result.average_runtime_ms
        assert result.average_runtime_ms <= result.max_runtime_ms
        assert result.arcs_processed >= 0
        assert result.revised_arcs >= 0
        assert result.ac3_values_pruned >= 0
        assert result.nodes_expanded >= 0
        assert result.assignments_tried >= 0
        assert result.backtracks >= 0
        assert result.forward_checks >= 0
        assert result.fc_values_pruned >= 0


def test_solved_scenario_is_validated_by_the_benchmark(monkeypatch) -> None:
    incidents, technicians = _load_data()
    real_solver = benchmark_module.solve_incident_assignment
    observed_validations: list[bool] = []

    def observing_solver(incident_subset, technician_batch):
        result = real_solver(incident_subset, technician_batch)
        observed_validations.append(
            result.assignment is not None
            and len(result.assignment) == len(incident_subset)
            and result.validation is not None
            and result.validation.valid
        )
        return result

    monkeypatch.setattr(
        benchmark_module,
        "solve_incident_assignment",
        observing_solver,
    )

    result = benchmark_scenario(
        "Small",
        incidents[:4],
        technicians,
        runs=1,
    )

    assert result.status == "solved"
    assert observed_validations == [True]


def test_benchmark_does_not_mutate_inputs() -> None:
    incidents, technicians = _load_data()
    original_incidents = tuple(incidents)
    original_technicians = tuple(technicians)

    run_benchmarks(incidents, technicians, runs=2)

    assert incidents == original_incidents
    assert technicians == original_technicians


def test_determinism_check_rejects_changed_statistics(monkeypatch) -> None:
    incidents, technicians = _load_data()
    real_solver = benchmark_module.solve_incident_assignment
    call_count = 0

    def changing_solver(incident_subset, technician_batch):
        nonlocal call_count
        call_count += 1
        result = real_solver(incident_subset, technician_batch)
        if call_count == 2:
            changed_backtracking = replace(
                result.stats.backtracking,
                nodes_expanded=result.stats.backtracking.nodes_expanded + 1,
            )
            return replace(
                result,
                stats=replace(
                    result.stats,
                    backtracking=changed_backtracking,
                ),
            )
        return result

    monkeypatch.setattr(
        benchmark_module,
        "solve_incident_assignment",
        changing_solver,
    )

    with pytest.raises(RuntimeError, match="non-deterministic result"):
        benchmark_scenario(
            "Small",
            incidents[:4],
            technicians,
            runs=2,
        )


def test_terminal_and_csv_outputs_preserve_scenario_order(tmp_path: Path) -> None:
    incidents, technicians = _load_data()
    results = run_benchmarks(incidents, technicians, runs=1)
    table = format_results(results)
    csv_path = write_csv(results, tmp_path / "nested" / "benchmark.csv")

    assert table.index("Small") < table.index("Medium") < table.index("Large")
    with csv_path.open("r", encoding="utf-8", newline="") as input_file:
        reader = csv.DictReader(input_file)
        rows = list(reader)

    assert tuple(reader.fieldnames or ()) == CSV_FIELDS
    assert [row["size"] for row in rows] == ["Small", "Medium", "Large"]
    assert [int(row["incidents"]) for row in rows] == [4, 8, 12]
