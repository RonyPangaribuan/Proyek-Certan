"""Data models used by the incident-prioritization baseline."""

from __future__ import annotations

from dataclasses import dataclass, fields
import math
import re


INCIDENT_ID_PATTERN = re.compile(r"^INC\d{3}$")


def _require_integer(name: str, value: object) -> int:
    if type(value) is not int:
        raise TypeError(f"{name} must be an integer")
    return value


@dataclass(frozen=True, slots=True)
class Incident:
    """A validated synthetic network incident."""

    incident_id: str
    category: str
    location: str
    urgency: int
    impact: int
    affected_users: int
    service_criticality: int
    waiting_time_min: int
    estimated_handling_time_min: int

    def __post_init__(self) -> None:
        if not isinstance(self.incident_id, str):
            raise TypeError("incident_id must be a string")
        if not INCIDENT_ID_PATTERN.fullmatch(self.incident_id):
            raise ValueError("incident_id must match the format INCxxx")

        for name in ("category", "location"):
            value = getattr(self, name)
            if not isinstance(value, str):
                raise TypeError(f"{name} must be a string")
            if not value.strip():
                raise ValueError(f"{name} must not be empty")

        for name in ("urgency", "impact", "service_criticality"):
            value = _require_integer(name, getattr(self, name))
            if not 1 <= value <= 5:
                raise ValueError(f"{name} must be between 1 and 5")

        affected_users = _require_integer("affected_users", self.affected_users)
        if affected_users < 0:
            raise ValueError("affected_users must be greater than or equal to 0")

        waiting_time = _require_integer("waiting_time_min", self.waiting_time_min)
        if waiting_time < 0:
            raise ValueError("waiting_time_min must be greater than or equal to 0")

        handling_time = _require_integer(
            "estimated_handling_time_min", self.estimated_handling_time_min
        )
        if handling_time <= 0:
            raise ValueError("estimated_handling_time_min must be greater than 0")


@dataclass(frozen=True, slots=True)
class ImportanceWeights:
    """Configurable weights for the baseline importance formula."""

    urgency: float = 0.30
    impact: float = 0.25
    service_criticality: float = 0.20
    affected_users: float = 0.15
    waiting_time: float = 0.10

    def __post_init__(self) -> None:
        values: list[float] = []
        for field in fields(self):
            value = getattr(self, field.name)
            if isinstance(value, bool) or not isinstance(value, (int, float)):
                raise TypeError(f"weight {field.name} must be a number")
            numeric_value = float(value)
            if not math.isfinite(numeric_value):
                raise ValueError(f"weight {field.name} must be finite")
            if numeric_value < 0:
                raise ValueError(f"weight {field.name} must be non-negative")
            object.__setattr__(self, field.name, numeric_value)
            values.append(numeric_value)

        total = math.fsum(values)
        if not math.isclose(total, 1.0, rel_tol=0.0, abs_tol=1e-9):
            raise ValueError(f"importance weights must sum to 1.0; got {total:.12g}")


@dataclass(frozen=True, slots=True)
class ScoreBreakdown:
    """Normalized values and weighted contributions for one incident."""

    incident: Incident
    normalized_urgency: float
    normalized_impact: float
    normalized_service_criticality: float
    normalized_affected_users: float
    normalized_waiting_time: float
    urgency_contribution: float
    impact_contribution: float
    service_criticality_contribution: float
    affected_users_contribution: float
    waiting_time_contribution: float
    importance_score: float


@dataclass(frozen=True, slots=True)
class ScheduleStep:
    """Measured cost of one incident's position in a schedule."""

    position: int
    incident: Incident
    importance_score: float
    completion_time_min: int
    step_cost: float


@dataclass(frozen=True, slots=True)
class ScheduleResult:
    """A complete sequence evaluated with weighted completion penalty."""

    sequence: tuple[Incident, ...]
    steps: tuple[ScheduleStep, ...]
    total_cost: float


@dataclass(frozen=True, slots=True)
class SearchResult:
    """A UCS schedule and its search statistics."""

    sequence: tuple[Incident, ...]
    steps: tuple[ScheduleStep, ...]
    total_cost: float
    states_expanded: int
    execution_time_seconds: float
