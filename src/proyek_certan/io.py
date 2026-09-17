"""JSON input for synthetic incident batches."""

from __future__ import annotations

import json
from pathlib import Path

from proyek_certan.models import Incident
from proyek_certan.validation import validate_incidents


INCIDENT_FIELDS = frozenset(
    {
        "incident_id",
        "category",
        "location",
        "urgency",
        "impact",
        "affected_users",
        "service_criticality",
        "waiting_time_min",
        "estimated_handling_time_min",
    }
)


def load_incidents(path: str | Path) -> tuple[Incident, ...]:
    """Load and validate a non-empty JSON array of incident objects."""

    input_path = Path(path)
    try:
        with input_path.open("r", encoding="utf-8") as input_file:
            payload = json.load(input_file)
    except json.JSONDecodeError as error:
        raise ValueError(
            f"invalid JSON in {input_path}: line {error.lineno}, column {error.colno}"
        ) from error

    if not isinstance(payload, list):
        raise ValueError("input root must be a JSON array")
    if not payload:
        raise ValueError("input JSON array must not be empty")

    incidents: list[Incident] = []
    for index, item in enumerate(payload):
        if not isinstance(item, dict):
            raise ValueError(f"incident at index {index} must be a JSON object")

        keys = set(item)
        missing = sorted(INCIDENT_FIELDS - keys)
        extra = sorted(keys - INCIDENT_FIELDS)
        if missing or extra:
            details: list[str] = []
            if missing:
                details.append(f"missing fields: {', '.join(missing)}")
            if extra:
                details.append(f"unexpected fields: {', '.join(extra)}")
            raise ValueError(f"incident at index {index} has {'; '.join(details)}")

        try:
            incidents.append(Incident(**item))
        except (TypeError, ValueError) as error:
            raise type(error)(f"incident at index {index}: {error}") from error

    return validate_incidents(incidents)
