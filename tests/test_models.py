import json

import pytest

from proyek_certan.io import load_incidents
from proyek_certan.models import Incident
from proyek_certan.validation import validate_incidents


def make_incident(**overrides: object) -> Incident:
    values = {
        "incident_id": "INC001",
        "category": "network_down",
        "location": "Laboratorium",
        "urgency": 4,
        "impact": 5,
        "affected_users": 40,
        "service_criticality": 4,
        "waiting_time_min": 15,
        "estimated_handling_time_min": 30,
    }
    values.update(overrides)
    return Incident(**values)


def test_valid_incident_can_be_created() -> None:
    incident = make_incident()

    assert incident.incident_id == "INC001"
    assert incident.estimated_handling_time_min == 30


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("urgency", 0),
        ("urgency", 6),
        ("impact", 0),
        ("impact", 6),
        ("service_criticality", 0),
        ("service_criticality", 6),
    ],
)
def test_scale_outside_one_to_five_is_rejected(field: str, value: int) -> None:
    with pytest.raises(ValueError, match="between 1 and 5"):
        make_incident(**{field: value})


@pytest.mark.parametrize("field", ["affected_users", "waiting_time_min"])
def test_negative_values_are_rejected(field: str) -> None:
    with pytest.raises(ValueError, match="greater than or equal to 0"):
        make_incident(**{field: -1})


def test_zero_handling_time_is_rejected() -> None:
    with pytest.raises(ValueError, match="greater than 0"):
        make_incident(estimated_handling_time_min=0)


@pytest.mark.parametrize("incident_id", ["001", "INC01", "INC0001", "inc001"])
def test_invalid_incident_id_is_rejected(incident_id: str) -> None:
    with pytest.raises(ValueError, match="INCxxx"):
        make_incident(incident_id=incident_id)


@pytest.mark.parametrize("field", ["category", "location"])
def test_blank_context_field_is_rejected(field: str) -> None:
    with pytest.raises(ValueError, match="must not be empty"):
        make_incident(**{field: "  "})


def test_boolean_is_not_accepted_as_an_integer() -> None:
    with pytest.raises(TypeError, match="must be an integer"):
        make_incident(urgency=True)


def test_duplicate_incident_ids_are_rejected() -> None:
    with pytest.raises(ValueError, match="duplicate incident_id: INC001"):
        validate_incidents([make_incident(), make_incident()])


def test_empty_batch_is_rejected() -> None:
    with pytest.raises(ValueError, match="must not be empty"):
        validate_incidents([])


def test_load_incidents_accepts_valid_json(tmp_path) -> None:
    path = tmp_path / "incidents.json"
    path.write_text(
        json.dumps(
            [
                {
                    "incident_id": "INC001",
                    "category": "network_down",
                    "location": "Laboratorium",
                    "urgency": 4,
                    "impact": 5,
                    "affected_users": 40,
                    "service_criticality": 4,
                    "waiting_time_min": 15,
                    "estimated_handling_time_min": 30,
                }
            ]
        ),
        encoding="utf-8",
    )

    incidents = load_incidents(path)

    assert [incident.incident_id for incident in incidents] == ["INC001"]


@pytest.mark.parametrize("payload", [{}, [], ["not-an-object"]])
def test_load_incidents_rejects_invalid_root_or_entries(tmp_path, payload) -> None:
    path = tmp_path / "incidents.json"
    path.write_text(json.dumps(payload), encoding="utf-8")

    with pytest.raises(ValueError):
        load_incidents(path)


def test_load_incidents_reports_missing_and_unexpected_fields(tmp_path) -> None:
    path = tmp_path / "incidents.json"
    payload = {
        "incident_id": "INC001",
        "category": "network_down",
        "location": "Laboratorium",
        "urgency": 4,
        "impact": 5,
        "affected_users": 40,
        "service_criticality": 4,
        "waiting_time_min": 15,
        "unexpected": "value",
    }
    path.write_text(json.dumps([payload]), encoding="utf-8")

    with pytest.raises(ValueError, match="missing fields.*unexpected fields"):
        load_incidents(path)


def test_load_incidents_reports_invalid_json(tmp_path) -> None:
    path = tmp_path / "incidents.json"
    path.write_text("[{", encoding="utf-8")

    with pytest.raises(ValueError, match="invalid JSON"):
        load_incidents(path)
