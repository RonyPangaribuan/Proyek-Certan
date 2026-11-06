from proyek_certan.constraint_solver.ac3 import ac3
from proyek_certan.constraint_solver.csp import CSP
from proyek_certan.constraint_solver.solver import solve


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


def test_solver_runs_ac3_then_backtracking_end_to_end() -> None:
    csp = CSP(
        ("X", "Y"),
        {"X": [1, 2, 3], "Y": [1, 2, 3]},
        {"X": ["Y"], "Y": ["X"]},
        ordered,
    )
    initial_domains = csp.copy_domains()

    result = solve(csp)

    assert result.status == "solved"
    assert result.solution is not None
    assert result.solution["X"] < result.solution["Y"]
    assert result.stats.ac3.values_pruned == 2
    assert result.stats.backtracking.nodes_expanded > 0
    assert csp.copy_domains() == initial_domains


def test_solver_stops_when_ac3_detects_no_solution() -> None:
    csp = CSP(
        ("X", "Y"),
        {"X": [1], "Y": [1]},
        {"X": ["Y"], "Y": ["X"]},
        different,
    )

    result = solve(csp)

    assert result.status == "no-solution"
    assert result.solution is None
    assert result.stats.ac3.values_pruned == 1
    assert result.stats.backtracking.nodes_expanded == 0
    assert result.stats.backtracking.assignments_tried == 0
    assert result.stats.backtracking.backtracks == 0


def test_solver_reports_no_solution_found_by_backtracking() -> None:
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

    propagation = ac3(csp)
    result = solve(csp)

    assert propagation.success is True
    assert result.status == "no-solution"
    assert result.solution is None
    assert result.stats.backtracking.nodes_expanded > 0
    assert result.stats.backtracking.backtracks > 0
