"""Command-line interface for Milestone 2 incident assignment."""

from __future__ import annotations

import argparse
from collections.abc import Sequence
from pathlib import Path
import sys

from proyek_certan.constraint_solver.incident_assignment import (
    IncidentAssignmentResult,
    solve_incident_assignment_files,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="proyek-certan-assign",
        description="Assign network incidents to technician-slot resources.",
    )
    parser.add_argument(
        "--incidents",
        required=True,
        type=Path,
        help="path to a JSON array of synthetic incidents",
    )
    parser.add_argument(
        "--technicians",
        required=True,
        type=Path,
        help="path to a JSON array of synthetic technicians",
    )
    return parser


def format_result(result: IncidentAssignmentResult) -> str:
    """Format status, assignment, validation, and solver statistics."""

    lines = [f"status: {result.status}"]
    if result.assignment is not None:
        lines.append("assignments:")
        lines.extend(
            f"  {incident_id} -> ({technician_id}, {slot})"
            for incident_id, (technician_id, slot) in result.assignment.items()
        )
        validation_status = (
            "passed"
            if result.validation is not None and result.validation.valid
            else "failed"
        )
        lines.append(f"validation: {validation_status}")

    lines.extend(
        (
            "AC-3:",
            f"  arcs_processed: {result.stats.ac3.arcs_processed}",
            f"  revised_arcs: {result.stats.ac3.revised_arcs}",
            f"  values_pruned: {result.stats.ac3.values_pruned}",
            "Backtracking:",
            f"  nodes_expanded: {result.stats.backtracking.nodes_expanded}",
            f"  assignments_tried: {result.stats.backtracking.assignments_tried}",
            f"  backtracks: {result.stats.backtracking.backtracks}",
            "Forward Checking:",
            f"  checks: {result.stats.backtracking.forward_checks}",
            f"  values_pruned: {result.stats.backtracking.fc_values_pruned}",
        )
    )
    return "\n".join(lines)


def main(argv: Sequence[str] | None = None) -> int:
    """Run the Milestone 2 assignment CLI."""

    arguments = build_parser().parse_args(argv)
    try:
        result = solve_incident_assignment_files(
            arguments.incidents,
            arguments.technicians,
        )
    except (OSError, TypeError, ValueError) as error:
        print(f"Error: {error}", file=sys.stderr)
        return 2

    print(format_result(result))
    return 0 if result.status == "solved" else 1


if __name__ == "__main__":
    raise SystemExit(main())
