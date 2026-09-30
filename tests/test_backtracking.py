from proyek_certan.constraint_solver.backtracking import (
    backtracking_search,
    is_consistent,
    order_domain_values,
    select_unassigned_variable,
)
from proyek_certan.constraint_solver.csp import CSP


def different(
    _first_variable: str,
    first_value: int,
    _second_variable: str,
    second_value: int,
) -> bool:
    return first_value != second_value


def test_mrv_selects_smallest_domain_and_uses_variable_order_for_ties() -> None:
    csp = CSP(
        ("A", "B", "C"),
        {"A": [1, 2, 3], "B": [1, 2], "C": [1, 2]},
        {"A": [], "B": [], "C": []},
        different,
    )

    first = select_unassigned_variable(csp, {}, csp.domains)
    second = select_unassigned_variable(csp, {"B": 1}, csp.domains)

    assert first == "B"
    assert second == "C"


def test_mrv_counts_values_legal_under_the_current_assignment() -> None:
    csp = CSP(
        ("A", "D", "B", "C"),
        {
            "A": [1],
            "D": [2],
            "B": [1, 2],
            "C": [1, 2, 3],
        },
        {
            "A": ["C"],
            "D": ["C"],
            "B": [],
            "C": ["A", "D"],
        },
        different,
    )

    selected = select_unassigned_variable(
        csp,
        {"A": 1, "D": 2},
        csp.domains,
    )

    assert selected == "C"


def test_lcv_orders_values_by_fewest_neighbor_eliminations() -> None:
    csp = CSP(
        ("X", "Y"),
        {"X": [1, 2, 3], "Y": [1, 2]},
        {"X": ["Y"], "Y": ["X"]},
        different,
    )

    ordered_values = order_domain_values(csp, "X", {}, csp.domains)

    assert ordered_values == [3, 1, 2]


def test_lcv_only_counts_neighbor_values_legal_under_current_assignment() -> None:
    csp = CSP(
        ("Z", "X", "Y"),
        {"Z": [1], "X": [2, 1], "Y": [1, 2, 3]},
        {"Z": ["Y"], "X": ["Y"], "Y": ["Z", "X"]},
        different,
    )

    ordered_values = order_domain_values(
        csp,
        "X",
        {"Z": 1},
        csp.domains,
    )

    assert ordered_values == [1, 2]


def test_consistency_checks_assigned_neighbors() -> None:
    csp = CSP(
        ("X", "Y"),
        {"X": [1, 2], "Y": [1, 2]},
        {"X": ["Y"], "Y": ["X"]},
        different,
    )

    assert is_consistent(csp, "Y", 2, {"X": 1}) is True
    assert is_consistent(csp, "Y", 1, {"X": 1}) is False


def test_backtracking_returns_a_complete_consistent_assignment() -> None:
    csp = CSP(
        ("A", "B", "C"),
        {variable: ["red", "blue", "green"] for variable in ("A", "B", "C")},
        {"A": ["B"], "B": ["A", "C"], "C": ["B"]},
        different,
    )

    result = backtracking_search(csp)

    assert result.solution is not None
    assert tuple(result.solution) == csp.variables
    assert set(result.solution) == set(csp.variables)
    for variable in csp.variables:
        for neighbor in csp.neighbors[variable]:
            assert csp.constraint(
                variable,
                result.solution[variable],
                neighbor,
                result.solution[neighbor],
            )
    assert result.stats.nodes_expanded > 0
    assert result.stats.assignments_tried > 0


def test_backtracking_reports_unsatisfiable_csp() -> None:
    csp = CSP(
        ("A", "B", "C"),
        {variable: [1, 2] for variable in ("A", "B", "C")},
        {
            "A": ["B", "C"],
            "B": ["A", "C"],
            "C": ["A", "B"],
        },
        different,
    )

    result = backtracking_search(csp)

    assert result.solution is None
    assert result.stats.backtracks > 0
