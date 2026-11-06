"""Project-specific CSP integration for assigning incidents to technicians."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
import json
from pathlib import Path
import re

from proyek_certan.constraint_solver.csp import CSP
from proyek_certan.constraint_solver.solver import SolverStats, SolverStatus, solve
from proyek_certan.io import load_incidents
from proyek_certan.models import Incident
from proyek_certan.validation import validate_incidents


TECHNICIAN_ID_PATTERN = re.compile(r"^TECH\d{3}$")
SLOT_ID_PATTERN = re.compile(r"^SLOT_\d+$")
TECHNICIAN_FIELDS = frozenset(
    {"technician_id", "skills", "available_slots"}
)

AssignmentValue = tuple[str, str]
AssignmentDomains = dict[str, tuple[AssignmentValue, ...]]
NeighborMap = dict[str, tuple[str, ...]]
IncidentAssignment = dict[str, AssignmentValue]


@dataclass(frozen=True, slots=True)
class Technician:
    """A validated technician used by the incident-assignment CSP."""

    technician_id: str
    skills: tuple[str, ...]
    available_slots: tuple[str, ...]

    def __post_init__(self) -> None:
        if not isinstance(self.technician_id, str):
            raise TypeError("technician_id must be a string")
        if not TECHNICIAN_ID_PATTERN.fullmatch(self.technician_id):
            raise ValueError("technician_id must match the format TECHxxx")

        self._validate_string_tuple("skills", self.skills)
        self._validate_string_tuple("available_slots", self.available_slots)
        invalid_slots = [
            slot
            for slot in self.available_slots
            if not SLOT_ID_PATTERN.fullmatch(slot)
        ]
        if invalid_slots:
            raise ValueError(
                "available_slots entries must match SLOT_<number>: "
                f"{invalid_slots!r}"
            )

    @staticmethod
    def _validate_string_tuple(name: str, values: object) -> None:
        if not isinstance(values, tuple):
            raise TypeError(f"{name} must be a tuple")
        if not values:
            raise ValueError(f"{name} must not be empty")
        if any(not isinstance(value, str) for value in values):
            raise TypeError(f"{name} entries must be strings")
        if any(not value.strip() for value in values):
            raise ValueError(f"{name} entries must not be empty")
        if len(set(values)) != len(values):
            raise ValueError(f"{name} entries must be unique")


@dataclass(frozen=True, slots=True)
class SolutionValidation:
    """Validation outcome for a project-specific assignment."""

    errors: tuple[str, ...] = ()

    @property
    def valid(self) -> bool:
        return not self.errors


@dataclass(frozen=True, slots=True)
class IncidentAssignmentResult:
    """Structured result from the project-specific assignment pipeline."""

    status: SolverStatus
    assignment: IncidentAssignment | None
    stats: SolverStats
    validation: SolutionValidation | None


def validate_technicians(
    technicians: Sequence[Technician],
) -> tuple[Technician, ...]:
    """Validate a non-empty technician batch and enforce unique IDs."""

    batch = tuple(technicians)
    if not batch:
        raise ValueError("technician batch must not be empty")

    seen_ids: set[str] = set()
    for index, technician in enumerate(batch):
        if not isinstance(technician, Technician):
            raise TypeError(f"technician at index {index} must be a Technician")
        if technician.technician_id in seen_ids:
            raise ValueError(
                f"duplicate technician_id: {technician.technician_id}"
            )
        seen_ids.add(technician.technician_id)

    return batch


def load_technicians(path: str | Path) -> tuple[Technician, ...]:
    """Load and validate a non-empty JSON array of technicians."""

    input_path = Path(path)
    try:
        with input_path.open("r", encoding="utf-8") as input_file:
            payload = json.load(input_file)
    except json.JSONDecodeError as error:
        raise ValueError(
            f"invalid JSON in {input_path}: "
            f"line {error.lineno}, column {error.colno}"
        ) from error

    if not isinstance(payload, list):
        raise ValueError("technician input root must be a JSON array")
    if not payload:
        raise ValueError("technician input JSON array must not be empty")

    technicians: list[Technician] = []
    for index, item in enumerate(payload):
        if not isinstance(item, dict):
            raise ValueError(f"technician at index {index} must be a JSON object")

        keys = set(item)
        missing = sorted(TECHNICIAN_FIELDS - keys)
        extra = sorted(keys - TECHNICIAN_FIELDS)
        if missing or extra:
            details: list[str] = []
            if missing:
                details.append(f"missing fields: {', '.join(missing)}")
            if extra:
                details.append(f"unexpected fields: {', '.join(extra)}")
            raise ValueError(
                f"technician at index {index} has {'; '.join(details)}"
            )

        skills = item["skills"]
        available_slots = item["available_slots"]
        if not isinstance(skills, list):
            raise TypeError(f"technician at index {index}: skills must be an array")
        if not isinstance(available_slots, list):
            raise TypeError(
                f"technician at index {index}: available_slots must be an array"
            )

        try:
            technicians.append(
                Technician(
                    technician_id=item["technician_id"],
                    skills=tuple(skills),
                    available_slots=tuple(available_slots),
                )
            )
        except (TypeError, ValueError) as error:
            raise type(error)(f"technician at index {index}: {error}") from error

    return validate_technicians(technicians)


def build_domains(
    incidents: Sequence[Incident],
    technicians: Sequence[Technician],
) -> AssignmentDomains:
    """Build ordered domains filtered by skill and availability."""

    incident_batch = validate_incidents(incidents)
    technician_batch = validate_technicians(technicians)
    return {
        incident.incident_id: tuple(
            (technician.technician_id, slot)
            for technician in technician_batch
            if incident.category in technician.skills
            for slot in technician.available_slots
        )
        for incident in incident_batch
    }


def build_neighbors(
    domains: Mapping[str, Sequence[AssignmentValue]],
) -> NeighborMap:
    """Connect incidents exactly when their domains share a resource."""

    variables = tuple(domains)
    domain_sets = {variable: set(domains[variable]) for variable in variables}
    neighbors: dict[str, list[str]] = {variable: [] for variable in variables}

    for index, first in enumerate(variables):
        for second in variables[index + 1 :]:
            if domain_sets[first].isdisjoint(domain_sets[second]):
                continue
            neighbors[first].append(second)
            neighbors[second].append(first)

    return {
        variable: tuple(neighbors[variable])
        for variable in variables
    }


def technician_slot_different(
    _first_incident: str,
    first_value: AssignmentValue,
    _second_incident: str,
    second_value: AssignmentValue,
) -> bool:
    """Reject two incidents using the same technician-slot resource."""

    return first_value != second_value


def build_incident_assignment_csp(
    incidents: Sequence[Incident],
    technicians: Sequence[Technician],
) -> CSP[str, AssignmentValue]:
    """Construct the project-specific binary CSP."""

    incident_batch = validate_incidents(incidents)
    technician_batch = validate_technicians(technicians)
    domains = build_domains(incident_batch, technician_batch)
    return CSP(
        variables=tuple(incident.incident_id for incident in incident_batch),
        domains=domains,
        neighbors=build_neighbors(domains),
        constraint=technician_slot_different,
    )


def validate_solution(
    solution: Mapping[str, AssignmentValue],
    incidents: Sequence[Incident],
    technicians: Sequence[Technician],
) -> SolutionValidation:
    """Validate completeness, skill, availability, and resource uniqueness."""

    incident_batch = validate_incidents(incidents)
    technician_batch = validate_technicians(technicians)
    expected_ids = tuple(incident.incident_id for incident in incident_batch)
    expected_id_set = set(expected_ids)
    technician_by_id = {
        technician.technician_id: technician
        for technician in technician_batch
    }
    incident_by_id = {
        incident.incident_id: incident for incident in incident_batch
    }
    errors: list[str] = []

    missing = [
        incident_id
        for incident_id in expected_ids
        if incident_id not in solution
    ]
    extra = sorted(
        incident_id
        for incident_id in solution
        if incident_id not in expected_id_set
    )
    if missing:
        errors.append(f"missing incident assignments: {missing!r}")
    if extra:
        errors.append(f"unknown incident assignments: {extra!r}")

    used_resources: dict[AssignmentValue, str] = {}
    for incident_id in expected_ids:
        if incident_id not in solution:
            continue
        value = solution[incident_id]
        if (
            not isinstance(value, tuple)
            or len(value) != 2
            or not all(isinstance(part, str) for part in value)
        ):
            errors.append(
                f"assignment for {incident_id} must be a "
                "(technician_id, slot) tuple"
            )
            continue

        technician_id, slot = value
        technician = technician_by_id.get(technician_id)
        if technician is None:
            errors.append(
                f"assignment for {incident_id} references unknown "
                f"technician {technician_id}"
            )
            continue

        incident = incident_by_id[incident_id]
        if incident.category not in technician.skills:
            errors.append(
                f"technician {technician_id} lacks skill "
                f"{incident.category} for {incident_id}"
            )
        if slot not in technician.available_slots:
            errors.append(
                f"technician {technician_id} is unavailable at "
                f"{slot} for {incident_id}"
            )

        previous_incident = used_resources.get(value)
        if previous_incident is not None:
            errors.append(
                f"resource {value!r} is shared by "
                f"{previous_incident} and {incident_id}"
            )
        else:
            used_resources[value] = incident_id

    return SolutionValidation(tuple(errors))


def solve_incident_assignment(
    incidents: Sequence[Incident],
    technicians: Sequence[Technician],
) -> IncidentAssignmentResult:
    """Build, solve, and validate an incident-assignment CSP."""

    incident_batch = validate_incidents(incidents)
    technician_batch = validate_technicians(technicians)
    csp = build_incident_assignment_csp(incident_batch, technician_batch)
    solver_result = solve(csp)

    if solver_result.solution is None:
        return IncidentAssignmentResult(
            status="no-solution",
            assignment=None,
            stats=solver_result.stats,
            validation=None,
        )

    assignment = dict(solver_result.solution)
    validation = validate_solution(
        assignment,
        incident_batch,
        technician_batch,
    )
    if not validation.valid:
        details = "; ".join(validation.errors)
        raise RuntimeError(f"solver returned an invalid assignment: {details}")

    return IncidentAssignmentResult(
        status="solved",
        assignment=assignment,
        stats=solver_result.stats,
        validation=validation,
    )


def solve_incident_assignment_files(
    incident_path: str | Path,
    technician_path: str | Path,
) -> IncidentAssignmentResult:
    """Load both datasets and run the complete assignment pipeline."""

    incidents = load_incidents(incident_path)
    technicians = load_technicians(technician_path)
    return solve_incident_assignment(incidents, technicians)
