from itertools import permutations

import pytest

from proyek_certan.baselines.fifo import fifo_schedule
from proyek_certan.models import Incident, ScoreBreakdown
from proyek_certan.scoring import score_incidents
from proyek_certan.search.ucs import uniform_cost_search


def incident(
    incident_id: str,
    urgency: int,
    impact: int,
    users: int,
    criticality: int,
    waiting: int,
    handling: int,
) -> Incident:
    return Incident(
        incident_id=incident_id,
        category="test",
        location="test-location",
        urgency=urgency,
        impact=impact,
        affected_users=users,
        service_criticality=criticality,
        waiting_time_min=waiting,
        estimated_handling_time_min=handling,
    )


def brute_force_oracle(
    incidents: list[Incident], scores: dict[str, ScoreBreakdown]
) -> tuple[tuple[str, ...], float]:
    """Independent exhaustive oracle used only by this test module."""

    best_sequence: tuple[str, ...] | None = None
    best_cost = float("inf")
    for candidate in permutations(incidents):
        elapsed = 0
        candidate_cost = 0.0
        for item in candidate:
            elapsed += item.estimated_handling_time_min
            candidate_cost += scores[item.incident_id].importance_score * elapsed
        candidate_ids = tuple(item.incident_id for item in candidate)
        if candidate_cost < best_cost:
            best_sequence = candidate_ids
            best_cost = candidate_cost

    assert best_sequence is not None
    return best_sequence, best_cost


@pytest.fixture
def small_batch() -> list[Incident]:
    return [
        incident("INC001", 2, 2, 5, 2, 60, 10),
        incident("INC002", 5, 5, 60, 5, 5, 30),
        incident("INC003", 4, 3, 20, 4, 20, 15),
        incident("INC004", 3, 4, 40, 3, 30, 25),
    ]


def test_ucs_matches_brute_force_oracle(small_batch: list[Incident]) -> None:
    scores = score_incidents(small_batch)
    expected_sequence, expected_cost = brute_force_oracle(small_batch, scores)

    result = uniform_cost_search(small_batch, scores)

    assert result.total_cost == pytest.approx(expected_cost)
    assert tuple(item.incident_id for item in result.sequence) == expected_sequence


def test_ucs_cost_is_not_greater_than_fifo(small_batch: list[Incident]) -> None:
    scores = score_incidents(small_batch)

    ucs = uniform_cost_search(small_batch, scores)
    fifo = fifo_schedule(small_batch, scores)

    assert ucs.total_cost <= fifo.total_cost


def test_ucs_is_deterministic(small_batch: list[Incident]) -> None:
    scores = score_incidents(small_batch)

    first = uniform_cost_search(small_batch, scores)
    second = uniform_cost_search(small_batch, scores)

    assert first.sequence == second.sequence
    assert first.steps == second.steps
    assert first.total_cost == second.total_cost
    assert first.states_expanded == second.states_expanded


def test_ucs_reports_search_statistics_and_non_negative_costs(
    small_batch: list[Incident],
) -> None:
    result = uniform_cost_search(small_batch)

    assert result.states_expanded > 0
    assert result.execution_time_seconds >= 0.0
    assert all(step.step_cost >= 0.0 for step in result.steps)
    assert len(result.sequence) == len(small_batch)
