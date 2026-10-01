import json
from pathlib import Path

import pytest

from proyek_certan.constraint_solver.assignment_cli import main
from proyek_certan.constraint_solver.incident_assignment import (
    Technician,
    build_incident_assignment_csp,
    load_technicians,
    solve_incident_assignment,
    solve_incident_assignment_files,
    validate_solution,
    validate_technicians,
)
from proyek_certan.io import load_incidents
from proyek_certan.models import Incident


PROJECT_ROOT = Path(__file__).resolve().parents[1]
INCIDENT_PATH = PROJECT_ROOT / "data" / "sample_incidents.json"
TECHNICIAN_PATH = PROJECT_ROOT / "data" / "sample_technicians.json"


def _incident(incident_id: str, category: str) -> Incident:
    return Incident(
        incident_id=incident_id,
        category=category,
        location="Synthetic Test Location",
        urgency=1,
        impact=1,
        affected_users=1,
        service_criticality=1,
        waiting_time_min=0,
        estimated_handling_time_min=1,
    )


def test_domain_generation_matches_skill_availability_and_documentation() -> None:
    incidents = load_incidents(INCIDENT_PATH)
    technicians = load_technicians(TECHNICIAN_PATH)
    csp = build_incident_assignment_csp(incidents, technicians)

    expected_domains = {
        "INC001": {
            ("TECH004", "SLOT_1"),
            ("TECH004", "SLOT_2"),
            ("TECH004", "SLOT_3"),
        },
        "INC002": {
            ("TECH002", "SLOT_1"),
            ("TECH002", "SLOT_3"),
            ("TECH003", "SLOT_1"),
            ("TECH003", "SLOT_2"),
            ("TECH003", "SLOT_3"),
        },
        "INC003": {
            ("TECH002", "SLOT_1"),
            ("TECH002", "SLOT_3"),
            ("TECH003", "SLOT_1"),
            ("TECH003", "SLOT_2"),
            ("TECH003", "SLOT_3"),
        },
        "INC004": {
            ("TECH001", "SLOT_1"),
            ("TECH001", "SLOT_2"),
            ("TECH004", "SLOT_1"),
            ("TECH004", "SLOT_2"),
            ("TECH004", "SLOT_3"),
        },
        "INC005": {
            ("TECH001", "SLOT_1"),
            ("TECH001", "SLOT_2"),
            ("TECH005", "SLOT_2"),
            ("TECH005", "SLOT_3"),
        },
        "INC006": {
            ("TECH003", "SLOT_1"),
            ("TECH003", "SLOT_2"),
            ("TECH003", "SLOT_3"),
        },
        "INC007": {
            ("TECH001", "SLOT_1"),
            ("TECH001", "SLOT_2"),
            ("TECH004", "SLOT_1"),
            ("TECH004", "SLOT_2"),
            ("TECH004", "SLOT_3"),
            ("TECH005", "SLOT_2"),
            ("TECH005", "SLOT_3"),
        },
        "INC008": {
            ("TECH002", "SLOT_1"),
            ("TECH002", "SLOT_3"),
            ("TECH005", "SLOT_2"),
            ("TECH005", "SLOT_3"),
        },
        "INC009": {
            ("TECH002", "SLOT_1"),
            ("TECH002", "SLOT_3"),
            ("TECH003", "SLOT_1"),
            ("TECH003", "SLOT_2"),
            ("TECH003", "SLOT_3"),
        },
        "INC010": {
            ("TECH004", "SLOT_1"),
            ("TECH004", "SLOT_2"),
            ("TECH004", "SLOT_3"),
        },
        "INC011": {
            ("TECH001", "SLOT_1"),
            ("TECH001", "SLOT_2"),
            ("TECH004", "SLOT_1"),
            ("TECH004", "SLOT_2"),
            ("TECH004", "SLOT_3"),
        },
        "INC012": {
            ("TECH001", "SLOT_1"),
            ("TECH001", "SLOT_2"),
            ("TECH004", "SLOT_1"),
            ("TECH004", "SLOT_2"),
            ("TECH004", "SLOT_3"),
            ("TECH005", "SLOT_2"),
            ("TECH005", "SLOT_3"),
        },
    }

    assert set(csp.domains) == set(expected_domains)
    for incident_id, expected in expected_domains.items():
        assert set(csp.domains[incident_id]) == expected

    assert ("TECH002", "SLOT_1") not in csp.domains["INC001"]
    assert ("TECH001", "SLOT_3") not in csp.domains["INC004"]


def test_constraint_graph_exactly_tracks_shared_domain_resources() -> None:
    csp = build_incident_assignment_csp(
        load_incidents(INCIDENT_PATH),
        load_technicians(TECHNICIAN_PATH),
    )

    for first in csp.variables:
        for second in csp.variables:
            if first == second:
                assert second not in csp.neighbors[first]
                continue
            domains_overlap = bool(
                set(csp.domains[first]).intersection(csp.domains[second])
            )
            assert (second in csp.neighbors[first]) is domains_overlap
            assert (second in csp.neighbors[first]) == (
                first in csp.neighbors[second]
            )

    assert "INC010" in csp.neighbors["INC001"]
    assert "INC006" not in csp.neighbors["INC001"]


def test_sample_dataset_solves_to_a_complete_valid_assignment() -> None:
    incidents = load_incidents(INCIDENT_PATH)
    technicians = load_technicians(TECHNICIAN_PATH)

    result = solve_incident_assignment(incidents, technicians)

    assert result.status == "solved"
    assert result.assignment is not None
    assert tuple(result.assignment) == tuple(
        incident.incident_id for incident in incidents
    )
    assert len(result.assignment) == 12
    assert len(set(result.assignment.values())) == 12
    assert result.validation is not None
    assert result.validation.valid is True
    assert result.stats.backtracking.forward_checks > 0
    assert validate_solution(
        result.assignment, incidents, technicians
    ).valid is True


def test_solution_validation_rejects_each_project_constraint_violation() -> None:
    incidents = load_incidents(INCIDENT_PATH)
    technicians = load_technicians(TECHNICIAN_PATH)
    result = solve_incident_assignment(incidents, technicians)
    assert result.assignment is not None

    missing = dict(result.assignment)
    del missing["INC012"]
    assert "missing incident assignments" in " ".join(
        validate_solution(missing, incidents, technicians).errors
    )

    wrong_skill = dict(result.assignment)
    wrong_skill["INC001"] = ("TECH002", "SLOT_1")
    assert "lacks skill" in " ".join(
        validate_solution(wrong_skill, incidents, technicians).errors
    )

    unavailable = dict(result.assignment)
    unavailable["INC004"] = ("TECH001", "SLOT_3")
    assert "is unavailable" in " ".join(
        validate_solution(unavailable, incidents, technicians).errors
    )

    duplicate_resource = dict(result.assignment)
    duplicate_resource["INC010"] = duplicate_resource["INC001"]
    assert "is shared by" in " ".join(
        validate_solution(duplicate_resource, incidents, technicians).errors
    )


def test_unsatisfiable_synthetic_dataset_reports_no_solution() -> None:
    incidents = (
        _incident("INC101", "wifi_down"),
        _incident("INC102", "wifi_down"),
    )
    technicians = (
        Technician("TECH101", ("wifi_down",), ("SLOT_1",)),
    )

    result = solve_incident_assignment(incidents, technicians)

    assert result.status == "no-solution"
    assert result.assignment is None
    assert result.validation is None
    assert result.stats.ac3.values_pruned == 1


def test_same_input_produces_the_same_assignment_and_stats() -> None:
    first = solve_incident_assignment_files(INCIDENT_PATH, TECHNICIAN_PATH)
    second = solve_incident_assignment_files(INCIDENT_PATH, TECHNICIAN_PATH)

    assert first == second


def test_technician_validation_rejects_duplicate_ids() -> None:
    technician = Technician("TECH101", ("wifi_down",), ("SLOT_1",))

    with pytest.raises(ValueError, match="duplicate technician_id"):
        validate_technicians((technician, technician))


def test_technician_loader_validates_json_structure(tmp_path: Path) -> None:
    invalid_path = tmp_path / "technicians.json"
    invalid_path.write_text(
        json.dumps(
            [
                {
                    "technician_id": "TECH101",
                    "skills": ["wifi_down"],
                    "unexpected": ["SLOT_1"],
                }
            ]
        ),
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="missing fields: available_slots"):
        load_technicians(invalid_path)


def test_assignment_cli_prints_solution_validation_and_stats(capsys) -> None:
    exit_code = main(
        [
            "--incidents",
            str(INCIDENT_PATH),
            "--technicians",
            str(TECHNICIAN_PATH),
        ]
    )
    output = capsys.readouterr()

    assert exit_code == 0
    assert "status: solved" in output.out
    assert output.out.count(" -> ") == 12
    assert "validation: passed" in output.out
    assert "arcs_processed:" in output.out
    assert "revised_arcs:" in output.out
    assert "values_pruned:" in output.out
    assert "nodes_expanded:" in output.out
    assert "assignments_tried:" in output.out
    assert "backtracks:" in output.out
    assert "Forward Checking:" in output.out
    assert "checks:" in output.out
    assert output.err == ""
