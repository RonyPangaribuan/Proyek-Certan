"""Command-line interface for the Milestone 1 prototype."""

from __future__ import annotations

import argparse
from collections.abc import Sequence
from pathlib import Path
import sys

from proyek_certan.baselines.fifo import fifo_schedule
from proyek_certan.io import load_incidents
from proyek_certan.models import (
    ImportanceWeights,
    ScheduleResult,
    ScoreBreakdown,
    SearchResult,
)
from proyek_certan.scoring import score_incidents
from proyek_certan.search.ucs import uniform_cost_search


PROJECT_TITLE = (
    "Sistem Pendukung Keputusan Berbasis AI untuk Prioritisasi dan "
    "Penanganan Insiden Jaringan Kampus"
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="proyek-certan",
        description=PROJECT_TITLE,
    )
    parser.add_argument(
        "--input",
        required=True,
        type=Path,
        help="path to a JSON array of synthetic incidents",
    )
    parser.add_argument("--weight-urgency", type=float, default=0.30)
    parser.add_argument("--weight-impact", type=float, default=0.25)
    parser.add_argument("--weight-service-criticality", type=float, default=0.20)
    parser.add_argument("--weight-affected-users", type=float, default=0.15)
    parser.add_argument("--weight-waiting-time", type=float, default=0.10)
    return parser


def _format_table(headers: Sequence[str], rows: Sequence[Sequence[str]]) -> str:
    string_rows = [tuple(str(cell) for cell in row) for row in rows]
    widths = [len(header) for header in headers]
    for row in string_rows:
        for index, cell in enumerate(row):
            widths[index] = max(widths[index], len(cell))

    def format_row(row: Sequence[str]) -> str:
        return " | ".join(cell.ljust(widths[index]) for index, cell in enumerate(row))

    separator = "-+-".join("-" * width for width in widths)
    lines = [format_row(headers), separator]
    lines.extend(format_row(row) for row in string_rows)
    return "\n".join(lines)


def _score_rows(scores: dict[str, ScoreBreakdown]) -> list[tuple[str, ...]]:
    rows: list[tuple[str, ...]] = []
    for incident_id in sorted(scores):
        score = scores[incident_id]
        rows.append(
            (
                incident_id,
                score.incident.category,
                score.incident.location,
                f"{score.urgency_contribution:.4f}",
                f"{score.impact_contribution:.4f}",
                f"{score.service_criticality_contribution:.4f}",
                f"{score.affected_users_contribution:.4f}",
                f"{score.waiting_time_contribution:.4f}",
                f"{score.importance_score:.4f}",
            )
        )
    return rows


def _schedule_rows(
    result: ScheduleResult | SearchResult,
) -> list[tuple[str, ...]]:
    return [
        (
            str(step.position),
            step.incident.incident_id,
            step.incident.category,
            step.incident.location,
            f"{step.importance_score:.4f}",
            str(step.incident.estimated_handling_time_min),
            str(step.completion_time_min),
            f"{step.step_cost:.4f}",
        )
        for step in result.steps
    ]


def _print_schedule(title: str, result: ScheduleResult | SearchResult) -> None:
    print(f"\n{title}")
    print(
        _format_table(
            (
                "Pos",
                "Incident ID",
                "Category",
                "Location",
                "Importance",
                "Handling (min)",
                "Completion (min)",
                "Step Cost",
            ),
            _schedule_rows(result),
        )
    )
    print(f"Total cost: {result.total_cost:.4f}")


def main(argv: Sequence[str] | None = None) -> int:
    """Run the CLI and return a process exit status."""

    parser = build_parser()
    arguments = parser.parse_args(argv)

    try:
        weights = ImportanceWeights(
            urgency=arguments.weight_urgency,
            impact=arguments.weight_impact,
            service_criticality=arguments.weight_service_criticality,
            affected_users=arguments.weight_affected_users,
            waiting_time=arguments.weight_waiting_time,
        )
        incidents = load_incidents(arguments.input)
        scores = score_incidents(incidents, weights)
        ucs_result = uniform_cost_search(incidents, scores)
        fifo_result = fifo_schedule(incidents, scores)
    except (OSError, TypeError, ValueError) as error:
        print(f"Error: {error}", file=sys.stderr)
        return 2

    print(PROJECT_TITLE)
    print(f"Input: {arguments.input}")
    print(f"Incidents: {len(incidents)}")
    print("Data note: synthetic snapshot; recommendation only.")

    print("\nImportance Score Breakdown (weighted contributions)")
    print(
        _format_table(
            (
                "Incident ID",
                "Category",
                "Location",
                "Urgency",
                "Impact",
                "Criticality",
                "Users",
                "Waiting",
                "Score",
            ),
            _score_rows(scores),
        )
    )

    _print_schedule("UCS Recommendation", ucs_result)
    print("Search statistics:")
    print(f"  States expanded: {ucs_result.states_expanded}")
    print(f"  Execution time: {ucs_result.execution_time_seconds:.6f} seconds")
    _print_schedule("FIFO Comparison (non-search)", fifo_result)

    cost_difference = fifo_result.total_cost - ucs_result.total_cost
    print("\nComparison")
    print(f"Cost difference (FIFO - UCS): {cost_difference:.4f}")
    if fifo_result.total_cost > 0:
        reduction = cost_difference / fifo_result.total_cost * 100
        print(f"Cost reduction: {reduction:.2f}%")
    else:
        print("Cost reduction: N/A (FIFO total cost is zero)")

    print("Final decision remains with the network administrator.")
    return 0
