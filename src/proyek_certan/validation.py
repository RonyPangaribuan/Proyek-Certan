"""Batch-level validation helpers."""

from __future__ import annotations

from collections.abc import Iterable

from proyek_certan.models import Incident


def validate_incidents(incidents: Iterable[Incident]) -> tuple[Incident, ...]:
    """Validate a non-empty incident batch and enforce unique IDs."""

    batch = tuple(incidents)
    if not batch:
        raise ValueError("incident batch must not be empty")

    seen_ids: set[str] = set()
    for index, incident in enumerate(batch):
        if not isinstance(incident, Incident):
            raise TypeError(f"incident at index {index} must be an Incident")
        if incident.incident_id in seen_ids:
            raise ValueError(f"duplicate incident_id: {incident.incident_id}")
        seen_ids.add(incident.incident_id)

    return batch
