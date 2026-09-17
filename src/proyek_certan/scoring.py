"""Importance scoring and shared schedule-cost evaluation."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
import math

from proyek_certan.models import (
    ImportanceWeights,
    Incident,
    ScheduleResult,
    ScheduleStep,
    ScoreBreakdown,
)
from proyek_certan.validation import validate_incidents


def score_incidents(
    incidents: Sequence[Incident],
    weights: ImportanceWeights | None = None,
) -> dict[str, ScoreBreakdown]:
    """Calculate normalized importance scores for one incident snapshot."""

    batch = validate_incidents(incidents)
    active_weights = weights or ImportanceWeights()
    max_affected_users = max(incident.affected_users for incident in batch)
    max_waiting_time = max(incident.waiting_time_min for incident in batch)

    scores: dict[str, ScoreBreakdown] = {}
    for incident in batch:
        normalized_urgency = incident.urgency / 5
        normalized_impact = incident.impact / 5
        normalized_criticality = incident.service_criticality / 5
        normalized_users = (
            incident.affected_users / max_affected_users
            if max_affected_users > 0
            else 0.0
        )
        normalized_waiting = (
            incident.waiting_time_min / max_waiting_time
            if max_waiting_time > 0
            else 0.0
        )

        urgency_contribution = active_weights.urgency * normalized_urgency
        impact_contribution = active_weights.impact * normalized_impact
        criticality_contribution = (
            active_weights.service_criticality * normalized_criticality
        )
        users_contribution = active_weights.affected_users * normalized_users
        waiting_contribution = active_weights.waiting_time * normalized_waiting
        importance_score = min(
            1.0,
            max(
                0.0,
                math.fsum(
                    (
                        urgency_contribution,
                        impact_contribution,
                        criticality_contribution,
                        users_contribution,
                        waiting_contribution,
                    )
                ),
            ),
        )

        scores[incident.incident_id] = ScoreBreakdown(
            incident=incident,
            normalized_urgency=normalized_urgency,
            normalized_impact=normalized_impact,
            normalized_service_criticality=normalized_criticality,
            normalized_affected_users=normalized_users,
            normalized_waiting_time=normalized_waiting,
            urgency_contribution=urgency_contribution,
            impact_contribution=impact_contribution,
            service_criticality_contribution=criticality_contribution,
            affected_users_contribution=users_contribution,
            waiting_time_contribution=waiting_contribution,
            importance_score=importance_score,
        )

    return scores


def validate_score_map(
    incidents: Sequence[Incident], scores: Mapping[str, ScoreBreakdown]
) -> None:
    """Ensure score details match a complete incident batch."""

    expected_ids = {incident.incident_id for incident in incidents}
    actual_ids = set(scores)
    if actual_ids != expected_ids:
        missing = sorted(expected_ids - actual_ids)
        extra = sorted(actual_ids - expected_ids)
        details: list[str] = []
        if missing:
            details.append(f"missing scores: {', '.join(missing)}")
        if extra:
            details.append(f"unexpected scores: {', '.join(extra)}")
        raise ValueError("score map does not match incidents; " + "; ".join(details))

    for incident in incidents:
        breakdown = scores[incident.incident_id]
        if not isinstance(breakdown, ScoreBreakdown):
            raise TypeError(
                f"score for {incident.incident_id} must be a ScoreBreakdown"
            )
        if breakdown.incident != incident:
            raise ValueError(f"score for {incident.incident_id} belongs to another incident")
        score = breakdown.importance_score
        if not math.isfinite(score) or not 0.0 <= score <= 1.0:
            raise ValueError(f"importance score for {incident.incident_id} must be in 0..1")


def evaluate_sequence(
    sequence: Sequence[Incident],
    scores: Mapping[str, ScoreBreakdown] | None = None,
    weights: ImportanceWeights | None = None,
) -> ScheduleResult:
    """Evaluate a complete sequence using weighted completion penalty."""

    incidents = validate_incidents(sequence)
    active_scores = scores if scores is not None else score_incidents(incidents, weights)
    validate_score_map(incidents, active_scores)

    elapsed_time = 0
    total_cost = 0.0
    steps: list[ScheduleStep] = []
    for position, incident in enumerate(incidents, start=1):
        elapsed_time += incident.estimated_handling_time_min
        importance_score = active_scores[incident.incident_id].importance_score
        step_cost = importance_score * elapsed_time
        total_cost += step_cost
        steps.append(
            ScheduleStep(
                position=position,
                incident=incident,
                importance_score=importance_score,
                completion_time_min=elapsed_time,
                step_cost=step_cost,
            )
        )

    return ScheduleResult(
        sequence=incidents,
        steps=tuple(steps),
        total_cost=total_cost,
    )
