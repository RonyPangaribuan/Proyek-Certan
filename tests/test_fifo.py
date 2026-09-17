import pytest

from proyek_certan.baselines.fifo import fifo_schedule
from proyek_certan.models import Incident
from proyek_certan.scoring import evaluate_sequence, score_incidents


def incident(incident_id: str, waiting: int, handling: int = 10) -> Incident:
    return Incident(
        incident_id=incident_id,
        category="test",
        location="test-location",
        urgency=3,
        impact=3,
        affected_users=10,
        service_criticality=3,
        waiting_time_min=waiting,
        estimated_handling_time_min=handling,
    )


def test_fifo_orders_largest_waiting_time_first() -> None:
    incidents = [
        incident("INC001", 10),
        incident("INC002", 30),
        incident("INC003", 20),
    ]

    result = fifo_schedule(incidents)

    assert [item.incident_id for item in result.sequence] == [
        "INC002",
        "INC003",
        "INC001",
    ]


def test_fifo_uses_incident_id_as_tie_breaker() -> None:
    incidents = [incident("INC003", 20), incident("INC001", 20)]

    result = fifo_schedule(incidents)

    assert [item.incident_id for item in result.sequence] == ["INC001", "INC003"]


def test_fifo_uses_shared_cost_evaluator() -> None:
    incidents = [incident("INC001", 10, 20), incident("INC002", 30, 10)]
    scores = score_incidents(incidents)

    fifo = fifo_schedule(incidents, scores)
    evaluated = evaluate_sequence(fifo.sequence, scores)

    assert fifo.total_cost == pytest.approx(evaluated.total_cost)
    assert fifo.steps == evaluated.steps
