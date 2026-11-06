"""Reproducible sensitivity benchmark for the Milestone 2 CSP solver."""

from __future__ import annotations

import argparse
from collections.abc import Sequence
import csv
from dataclasses import asdict, dataclass
from pathlib import Path
from statistics import fmean
import sys
from time import perf_counter_ns

from proyek_certan.constraint_solver.incident_assignment import (
    IncidentAssignmentResult,
    Technician,
    load_technicians,
    solve_incident_assignment,
)
from proyek_certan.constraint_solver.solver import SolverStatus
from proyek_certan.io import load_incidents
from proyek_certan.models import Incident


PROJECT_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_INCIDENT_PATH = PROJECT_ROOT / "data" / "sample_incidents.json"
DEFAULT_TECHNICIAN_PATH = PROJECT_ROOT / "data" / "sample_technicians.json"
DEFAULT_RUNS = 10
SCENARIO_SPECS = (("Small", 4), ("Medium", 8), ("Large", 12))
CSV_FIELDS = (
    "size",
    "incidents",
    "runs",
    "average_runtime_ms",
    "min_runtime_ms",
    "max_runtime_ms",
    "arcs_processed",
    "revised_arcs",
    "ac3_values_pruned",
    "nodes_expanded",
    "assignments_tried",
    "backtracks",
    "forward_checks",
    "fc_values_pruned",
    "status",
)


@dataclass(frozen=True, slots=True)
class BenchmarkResult:
    """One terminal and CSV row from a benchmark scenario."""

    size: str
    incidents: int
    runs: int
    average_runtime_ms: float
    min_runtime_ms: float
    max_runtime_ms: float
    arcs_processed: int
    revised_arcs: int
    ac3_values_pruned: int
    nodes_expanded: int
    assignments_tried: int
    backtracks: int
    forward_checks: int
    fc_values_pruned: int
    status: SolverStatus


def build_scenarios(
    incidents: Sequence[Incident],
) -> tuple[tuple[str, tuple[Incident, ...]], ...]:
    """Build deterministic 4, 8, and 12 incident prefixes."""

    incident_batch = tuple(incidents)
    required = SCENARIO_SPECS[-1][1]
    if len(incident_batch) < required:
        raise ValueError(
            f"benchmark requires at least {required} incidents; "
            f"got {len(incident_batch)}"
        )
    return tuple(
        (size, incident_batch[:count])
        for size, count in SCENARIO_SPECS
    )


def _validate_runs(runs: int) -> None:
    if isinstance(runs, bool) or not isinstance(runs, int):
        raise TypeError("runs must be an integer")
    if runs <= 0:
        raise ValueError("runs must be greater than 0")


def _parse_runs(value: str) -> int:
    try:
        runs = int(value)
    except ValueError as error:
        raise argparse.ArgumentTypeError("runs must be an integer") from error
    try:
        _validate_runs(runs)
    except (TypeError, ValueError) as error:
        raise argparse.ArgumentTypeError(str(error)) from error
    return runs


def _validate_solver_result(
    result: IncidentAssignmentResult,
    size: str,
    incident_count: int,
) -> None:
    if result.status != "solved":
        return

    problems: list[str] = []
    if result.assignment is None:
        problems.append("assignment is missing")
    elif len(result.assignment) != incident_count:
        problems.append(
            f"expected {incident_count} assignments, "
            f"got {len(result.assignment)}"
        )
    if result.validation is None:
        problems.append("solution validation is missing")
    elif not result.validation.valid:
        problems.append(
            "solution validation failed: "
            + "; ".join(result.validation.errors)
        )
    if problems:
        raise RuntimeError(
            f"invalid solved result for {size}: {'; '.join(problems)}"
        )


def _assert_deterministic(
    reference: IncidentAssignmentResult,
    current: IncidentAssignmentResult,
    size: str,
    run_number: int,
) -> None:
    differences: list[str] = []
    if current.status != reference.status:
        differences.append("status")
    if current.assignment != reference.assignment:
        differences.append("assignment")
    if current.stats.ac3 != reference.stats.ac3:
        differences.append("AC-3 statistics")
    if current.stats.backtracking != reference.stats.backtracking:
        differences.append("backtracking statistics")
    if differences:
        raise RuntimeError(
            f"non-deterministic result for {size} on run {run_number}: "
            + ", ".join(differences)
        )


def benchmark_scenario(
    size: str,
    incidents: Sequence[Incident],
    technicians: Sequence[Technician],
    runs: int,
) -> BenchmarkResult:
    """Benchmark one in-memory scenario and verify deterministic results."""

    _validate_runs(runs)
    incident_subset = tuple(incidents)
    technician_batch = tuple(technicians)
    runtimes_ms: list[float] = []
    reference: IncidentAssignmentResult | None = None

    for run_number in range(1, runs + 1):
        start_ns = perf_counter_ns()
        result = solve_incident_assignment(incident_subset, technician_batch)
        end_ns = perf_counter_ns()

        runtimes_ms.append((end_ns - start_ns) / 1_000_000)
        _validate_solver_result(result, size, len(incident_subset))
        if reference is None:
            reference = result
        else:
            _assert_deterministic(reference, result, size, run_number)

    if reference is None:
        raise RuntimeError(f"benchmark scenario {size} produced no runs")

    ac3_stats = reference.stats.ac3
    backtracking_stats = reference.stats.backtracking
    return BenchmarkResult(
        size=size,
        incidents=len(incident_subset),
        runs=runs,
        average_runtime_ms=fmean(runtimes_ms),
        min_runtime_ms=min(runtimes_ms),
        max_runtime_ms=max(runtimes_ms),
        arcs_processed=ac3_stats.arcs_processed,
        revised_arcs=ac3_stats.revised_arcs,
        ac3_values_pruned=ac3_stats.values_pruned,
        nodes_expanded=backtracking_stats.nodes_expanded,
        assignments_tried=backtracking_stats.assignments_tried,
        backtracks=backtracking_stats.backtracks,
        forward_checks=backtracking_stats.forward_checks,
        fc_values_pruned=backtracking_stats.fc_values_pruned,
        status=reference.status,
    )


def run_benchmarks(
    incidents: Sequence[Incident],
    technicians: Sequence[Technician],
    runs: int = DEFAULT_RUNS,
) -> tuple[BenchmarkResult, ...]:
    """Run Small, Medium, and Large scenarios in that order."""

    _validate_runs(runs)
    technician_batch = tuple(technicians)
    return tuple(
        benchmark_scenario(size, subset, technician_batch, runs)
        for size, subset in build_scenarios(incidents)
    )


def _format_table(
    headers: Sequence[str],
    rows: Sequence[Sequence[str]],
) -> str:
    widths = [len(header) for header in headers]
    for row in rows:
        for index, cell in enumerate(row):
            widths[index] = max(widths[index], len(cell))

    def format_row(row: Sequence[str]) -> str:
        return " | ".join(
            cell.ljust(widths[index])
            for index, cell in enumerate(row)
        )

    lines = [format_row(headers), "-+-".join("-" * width for width in widths)]
    lines.extend(format_row(row) for row in rows)
    return "\n".join(lines)


def format_results(results: Sequence[BenchmarkResult]) -> str:
    """Format benchmark results as a dependency-free terminal table."""

    headers = (
        "Size",
        "Incidents",
        "Runs",
        "Avg Runtime (ms)",
        "Min Runtime (ms)",
        "Max Runtime (ms)",
        "AC3 Arcs",
        "AC3 Revised",
        "AC3 Pruned",
        "Nodes",
        "Tried",
        "Backtracks",
        "FC Checks",
        "FC Pruned",
        "Status",
    )
    rows = [
        (
            result.size,
            str(result.incidents),
            str(result.runs),
            f"{result.average_runtime_ms:.6f}",
            f"{result.min_runtime_ms:.6f}",
            f"{result.max_runtime_ms:.6f}",
            str(result.arcs_processed),
            str(result.revised_arcs),
            str(result.ac3_values_pruned),
            str(result.nodes_expanded),
            str(result.assignments_tried),
            str(result.backtracks),
            str(result.forward_checks),
            str(result.fc_values_pruned),
            result.status,
        )
        for result in results
    ]
    return _format_table(headers, rows)


def write_csv(
    results: Sequence[BenchmarkResult],
    path: str | Path,
) -> Path:
    """Write unrounded benchmark data using the documented CSV schema."""

    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8", newline="") as output_file:
        writer = csv.DictWriter(output_file, fieldnames=CSV_FIELDS)
        writer.writeheader()
        writer.writerows(asdict(result) for result in results)
    return output_path


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="proyek-certan-benchmark",
        description="Benchmark Milestone 2 CSP sensitivity scenarios.",
    )
    parser.add_argument(
        "--runs",
        type=_parse_runs,
        default=DEFAULT_RUNS,
        help="positive repetitions per scenario (default: 10)",
    )
    parser.add_argument(
        "--csv",
        type=Path,
        help="optional path for CSV experiment output",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    """Load datasets once, run all scenarios, and print the result table."""

    arguments = build_parser().parse_args(argv)
    try:
        incidents = load_incidents(DEFAULT_INCIDENT_PATH)
        technicians = load_technicians(DEFAULT_TECHNICIAN_PATH)
        results = run_benchmarks(incidents, technicians, arguments.runs)
        if arguments.csv is not None:
            write_csv(results, arguments.csv)
    except (OSError, RuntimeError, TypeError, ValueError) as error:
        print(f"Error: {error}", file=sys.stderr)
        return 2

    print(format_results(results))
    if arguments.csv is not None:
        print(f"CSV: {arguments.csv}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
