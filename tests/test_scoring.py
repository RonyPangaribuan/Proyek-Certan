import math

import pytest

from proyek_certan.models import ImportanceWeights, Incident
from proyek_certan.scoring import evaluate_sequence, score_incidents


def incident(
    incident_id: str,
    *,
    urgency: int = 3,
    impact: int = 3,
    users: int = 10,
    criticality: int = 3,
    waiting: int = 10,
    handling: int = 10,
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


def test_default_weights_sum_to_one() -> None:
    weights = ImportanceWeights()

    assert math.fsum(
        (
            weights.urgency,
            weights.impact,
            weights.service_criticality,
            weights.affected_users,
            weights.waiting_time,
        )
    ) == pytest.approx(1.0)


def test_weights_must_sum_to_one() -> None:
    with pytest.raises(ValueError, match="sum to 1.0"):
        ImportanceWeights(urgency=0.20)


@pytest.mark.parametrize("value", [-0.1, float("nan"), float("inf")])
def test_weights_must_be_non_negative_and_finite(value: float) -> None:
    with pytest.raises(ValueError):
        ImportanceWeights(
            urgency=value,
            impact=1.0 - value if math.isfinite(value) else 0.25,
            service_criticality=0.0,
            affected_users=0.0,
            waiting_time=0.0,
        )


def test_importance_score_and_contributions_match_formula() -> None:
    item = incident(
        "INC001",
        urgency=5,
        impact=4,
        users=50,
        criticality=3,
        waiting=25,
    )

    breakdown = score_incidents([item])["INC001"]

    assert breakdown.normalized_urgency == pytest.approx(1.0)
    assert breakdown.normalized_impact == pytest.approx(0.8)
    assert breakdown.normalized_service_criticality == pytest.approx(0.6)
    assert breakdown.normalized_affected_users == pytest.approx(1.0)
    assert breakdown.normalized_waiting_time == pytest.approx(1.0)
    assert breakdown.importance_score == pytest.approx(0.87)
    assert breakdown.importance_score == pytest.approx(
        math.fsum(
            (
                breakdown.urgency_contribution,
                breakdown.impact_contribution,
                breakdown.service_criticality_contribution,
                breakdown.affected_users_contribution,
                breakdown.waiting_time_contribution,
            )
        )
    )


def test_importance_scores_are_between_zero_and_one() -> None:
    incidents = [
        incident("INC001", urgency=1, impact=1, users=0, criticality=1, waiting=0),
        incident("INC002", urgency=5, impact=5, users=100, criticality=5, waiting=50),
    ]

    scores = score_incidents(incidents)

    assert all(0.0 <= item.importance_score <= 1.0 for item in scores.values())


def test_normalization_is_safe_when_batch_maxima_are_zero() -> None:
    item = incident("INC001", users=0, waiting=0)

    breakdown = score_incidents([item])["INC001"]

    assert breakdown.normalized_affected_users == 0.0
    assert breakdown.normalized_waiting_time == 0.0
    assert breakdown.affected_users_contribution == 0.0
    assert breakdown.waiting_time_contribution == 0.0


def test_evaluate_sequence_uses_weighted_completion_penalty() -> None:
    first = incident("INC001", handling=10)
    second = incident("INC002", handling=20, urgency=5)
    sequence = [first, second]
    scores = score_incidents(sequence)

    result = evaluate_sequence(sequence, scores)

    assert [step.completion_time_min for step in result.steps] == [10, 30]
    expected = (
        scores["INC001"].importance_score * 10
        + scores["INC002"].importance_score * 30
    )
    assert result.total_cost == pytest.approx(expected)
    assert all(step.step_cost >= 0 for step in result.steps)


def test_evaluate_sequence_rejects_incomplete_explicit_score_map() -> None:
    with pytest.raises(ValueError, match="missing scores"):
        evaluate_sequence([incident("INC001")], {})
