from proyek_certan.constraint_solver.backtracking import (
    backtracking_search,
    forward_check,
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


def restoration_constraint(
    first_variable: str,
    first_value: int,
    second_variable: str,
    second_value: int,
) -> bool:
    variables = frozenset((first_variable, second_variable))
    if variables == {"X", "Z"}:
        z_value = first_value if first_variable == "Z" else second_value
        return z_value == 2
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


def test_forward_check_prunes_incompatible_neighbor_values() -> None:
    csp = CSP(
        ("X", "Y"),
        {"X": [1, 2], "Y": [1, 2]},
        {"X": ["Y"], "Y": ["X"]},
        different,
    )
    original_domains = csp.copy_domains()

    result = forward_check(csp, "X", 1, {"X": 1}, original_domains)

    assert result.success is True
    assert result.domains["Y"] == [2]
    assert result.values_pruned == 1
    assert original_domains == {"X": [1, 2], "Y": [1, 2]}


def test_forward_check_detects_an_empty_neighbor_domain() -> None:
    csp = CSP(
        ("X", "Y"),
        {"X": [1], "Y": [1]},
        {"X": ["Y"], "Y": ["X"]},
        different,
    )

    result = forward_check(csp, "X", 1, {"X": 1}, csp.domains)

    assert result.success is False
    assert result.domains["Y"] == []
    assert result.values_pruned == 1


def test_backtracking_restores_domains_after_a_failed_branch() -> None:
    csp = CSP(
        ("X", "Y", "Z"),
        {variable: [1, 2] for variable in ("X", "Y", "Z")},
        {
            "X": ["Y", "Z"],
            "Y": ["X", "Z"],
            "Z": ["X", "Y"],
        },
        restoration_constraint,
    )
    supplied_domains = csp.copy_domains()
    original_domains = {
        variable: list(values)
        for variable, values in supplied_domains.items()
    }

    result = backtracking_search(csp, supplied_domains)

    assert result.solution == {"X": 2, "Y": 1, "Z": 2}
    assert result.stats.backtracks > 0
    assert result.stats.forward_checks > 0
    assert result.stats.fc_values_pruned > 0
    assert supplied_domains == original_domains


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
    assert result.stats.forward_checks > 0


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
    assert result.stats.forward_checks > 0
