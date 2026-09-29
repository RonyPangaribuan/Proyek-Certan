import pytest

from proyek_certan.constraint_solver.csp import CSP


def different(
    _first_variable: str,
    first_value: int,
    _second_variable: str,
    second_value: int,
) -> bool:
    return first_value != second_value


def test_csp_copies_initial_data_and_provides_independent_working_domains() -> None:
    source_domains = {"X": [1, 2], "Y": [1, 2]}
    source_neighbors = {"X": ["Y"], "Y": ["X"]}
    csp = CSP(("X", "Y"), source_domains, source_neighbors, different)

    source_domains["X"].append(3)
    source_neighbors["X"].clear()
    copied_domains = csp.copy_domains()
    copied_domains["X"].remove(1)

    assert csp.variables == ("X", "Y")
    assert csp.domains["X"] == (1, 2)
    assert csp.neighbors["X"] == ("Y",)
    assert copied_domains["X"] == [2]


def test_csp_requires_domains_for_every_variable() -> None:
    with pytest.raises(ValueError, match="domains must match CSP variables"):
        CSP(
            ("X", "Y"),
            {"X": [1]},
            {"X": ["Y"], "Y": ["X"]},
            different,
        )


def test_csp_rejects_unknown_neighbor() -> None:
    with pytest.raises(ValueError, match="unknown variables"):
        CSP(
            ("X",),
            {"X": [1]},
            {"X": ["Y"]},
            different,
        )
