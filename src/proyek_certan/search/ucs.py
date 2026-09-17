"""Uniform Cost Search for minimum weighted completion penalty."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from heapq import heappop, heappush
from itertools import count
from time import perf_counter

from proyek_certan.models import (
    ImportanceWeights,
    Incident,
    ScoreBreakdown,
    SearchResult,
)
from proyek_certan.scoring import evaluate_sequence, score_incidents, validate_score_map
from proyek_certan.validation import validate_incidents


def uniform_cost_search(
    incidents: Sequence[Incident],
    scores: Mapping[str, ScoreBreakdown] | None = None,
    weights: ImportanceWeights | None = None,
) -> SearchResult:
    """Find an optimal sequence with Uniform Cost Search."""

    batch = validate_incidents(incidents)
    active_scores = scores if scores is not None else score_incidents(batch, weights)
    validate_score_map(batch, active_scores)
    incidents_by_id = {incident.incident_id: incident for incident in batch}

    initial_remaining = tuple(sorted(incidents_by_id))
    tie_breaker = count()
    frontier: list[tuple[float, int, tuple[str, ...], tuple[str, ...], int]] = []
    heappush(
        frontier,
        (0.0, next(tie_breaker), (), initial_remaining, 0),
    )
    best_cost: dict[tuple[str, ...], float] = {initial_remaining: 0.0}
    states_expanded = 0
    start_time = perf_counter()

    while frontier:
        cumulative_cost, _, sequence_ids, remaining_ids, elapsed_time = heappop(
            frontier
        )
        if cumulative_cost > best_cost.get(remaining_ids, float("inf")):
            continue

        # UCS goal tests when the cheapest state is removed from the queue.
        if not remaining_ids:
            execution_time = perf_counter() - start_time
            sequence = tuple(incidents_by_id[item] for item in sequence_ids)
            evaluated = evaluate_sequence(sequence, active_scores)
            return SearchResult(
                sequence=evaluated.sequence,
                steps=evaluated.steps,
                total_cost=evaluated.total_cost,
                states_expanded=states_expanded,
                execution_time_seconds=execution_time,
            )

        states_expanded += 1
        for incident_id in remaining_ids:
            incident = incidents_by_id[incident_id]
            completion_time = elapsed_time + incident.estimated_handling_time_min
            step_cost = (
                active_scores[incident_id].importance_score * completion_time
            )
            next_cost = cumulative_cost + step_cost
            next_remaining = tuple(
                item for item in remaining_ids if item != incident_id
            )

            if next_cost >= best_cost.get(next_remaining, float("inf")):
                continue

            best_cost[next_remaining] = next_cost
            heappush(
                frontier,
                (
                    next_cost,
                    next(tie_breaker),
                    sequence_ids + (incident_id,),
                    next_remaining,
                    completion_time,
                ),
            )

    raise RuntimeError("UCS frontier exhausted without finding a complete sequence")
