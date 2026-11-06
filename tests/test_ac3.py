from proyek_certan.constraint_solver.ac3 import ac3, revise
from proyek_certan.constraint_solver.csp import CSP


def different(
    _first_variable: str,
    first_value: int,
    _second_variable: str,
    second_value: int,
) -> bool:
    return first_value != second_value


def ordered(
    first_variable: str,
    first_value: int,
    _second_variable: str,
    second_value: int,
) -> bool:
    if first_variable == "X":
        return first_value < second_value
    return first_value > second_value


def test_revise_prunes_values_without_support() -> None:
    csp = CSP(
        ("X", "Y"),
        {"X": [1, 2], "Y": [2]},
        {"X": ["Y"], "Y": ["X"]},
        different,
    )
    domains = csp.copy_domains()

    result = revise(csp, domains, "X", "Y")

    assert result.revised is True
    assert result.values_pruned == 1
    assert domains["X"] == [1]


def test_ac3_produces_arc_consistent_domains() -> None:
    csp = CSP(
        ("X", "Y"),
        {"X": [1, 2, 3], "Y": [1, 2, 3]},
        {"X": ["Y"], "Y": ["X"]},
        ordered,
    )

    result = ac3(csp)

    assert result.success is True
    assert result.domains == {"X": [1, 2], "Y": [2, 3]}
    assert result.stats.revised_arcs == 2
    assert result.stats.values_pruned == 2
    for xi in csp.variables:
        for xj in csp.neighbors[xi]:
            assert all(
                any(
                    csp.constraint(xi, value_i, xj, value_j)
                    for value_j in result.domains[xj]
                )
                for value_i in result.domains[xi]
            )


def test_ac3_detects_an_empty_domain() -> None:
    csp = CSP(
        ("X", "Y"),
        {"X": [1], "Y": [1]},
        {"X": ["Y"], "Y": ["X"]},
        different,
    )

    result = ac3(csp)

    assert result.success is False
    assert any(not domain for domain in result.domains.values())
    assert result.stats.values_pruned == 1


def test_ac3_does_not_mutate_supplied_domains() -> None:
    csp = CSP(
        ("X", "Y"),
        {"X": [1, 2], "Y": [2]},
        {"X": ["Y"], "Y": ["X"]},
        different,
    )
    supplied_domains = {"X": [1, 2], "Y": [2]}

    ac3(csp, supplied_domains)

    assert supplied_domains == {"X": [1, 2], "Y": [2]}
