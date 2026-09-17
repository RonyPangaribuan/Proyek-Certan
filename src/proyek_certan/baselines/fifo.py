"""First In, First Out comparison baseline."""

from __future__ import annotations

from collections.abc import Mapping, Sequence

from proyek_certan.models import (
    ImportanceWeights,
    Incident,
    ScheduleResult,
    ScoreBreakdown,
)
from proyek_certan.scoring import evaluate_sequence, score_incidents, validate_score_map
from proyek_certan.validation import validate_incidents


def fifo_schedule(
    incidents: Sequence[Incident],
    scores: Mapping[str, ScoreBreakdown] | None = None,
    weights: ImportanceWeights | None = None,
) -> ScheduleResult:
    """Schedule oldest reports first, with incident ID as the tie-breaker."""

    batch = validate_incidents(incidents)
    active_scores = scores if scores is not None else score_incidents(batch, weights)
    validate_score_map(batch, active_scores)
    ordered = tuple(
        sorted(
            batch,
            key=lambda incident: (-incident.waiting_time_min, incident.incident_id),
        )
    )
    return evaluate_sequence(ordered, active_scores)
