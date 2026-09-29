"""Backtracking search with MRV and LCV for generic binary CSPs."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass

from proyek_certan.constraint_solver.csp import CSP, DomainMap, ValueT, VariableT


Assignment = dict[VariableT, ValueT]


@dataclass(frozen=True, slots=True)
class BacktrackingStats:
    """Operation counts collected during recursive backtracking."""

    nodes_expanded: int = 0
    assignments_tried: int = 0
    backtracks: int = 0


@dataclass(frozen=True, slots=True)
class BacktrackingResult:
    """Backtracking outcome and its operation counts."""

    solution: Assignment[VariableT, ValueT] | None
    stats: BacktrackingStats


def _copy_domains(
    csp: CSP[VariableT, ValueT],
    domains: Mapping[VariableT, Sequence[ValueT]] | None,
) -> DomainMap[VariableT, ValueT]:
    if domains is None:
        return csp.copy_domains()

    missing = [variable for variable in csp.variables if variable not in domains]
    known_variables = set(csp.variables)
    extra = [variable for variable in domains if variable not in known_variables]
    if missing or extra:
        raise ValueError("working domains must match CSP variables")

    return {variable: list(domains[variable]) for variable in csp.variables}


def _pair_is_consistent(
    csp: CSP[VariableT, ValueT],
    variable: VariableT,
    value: ValueT,
    other: VariableT,
    other_value: ValueT,
) -> bool:
    if other in csp.neighbors[variable] and not csp.constraint(
        variable, value, other, other_value
    ):
        return False
    if variable in csp.neighbors[other] and not csp.constraint(
        other, other_value, variable, value
    ):
        return False
    return True


def is_consistent(
    csp: CSP[VariableT, ValueT],
    variable: VariableT,
    value: ValueT,
    assignment: Mapping[VariableT, ValueT],
) -> bool:
    """Return whether a proposed value satisfies all assigned neighbors."""

    return all(
        other == variable
        or other not in assignment
        or _pair_is_consistent(
            csp, variable, value, other, assignment[other]
        )
        for other in csp.variables
    )


def select_unassigned_variable(
    csp: CSP[VariableT, ValueT],
    assignment: Mapping[VariableT, ValueT],
    domains: Mapping[VariableT, Sequence[ValueT]],
) -> VariableT:
    """Select an unassigned variable by MRV and declared variable order."""

    candidates = [
        variable for variable in csp.variables if variable not in assignment
    ]
    if not candidates:
        raise ValueError("cannot select a variable from a complete assignment")
    return min(candidates, key=lambda variable: len(domains[variable]))


def order_domain_values(
    csp: CSP[VariableT, ValueT],
    variable: VariableT,
    assignment: Mapping[VariableT, ValueT],
    domains: Mapping[VariableT, Sequence[ValueT]],
) -> list[ValueT]:
    """Order values by how few neighbor-domain values they eliminate."""

    related_unassigned = [
        other
        for other in csp.variables
        if other != variable
        and other not in assignment
        and (
            other in csp.neighbors[variable]
            or variable in csp.neighbors[other]
        )
    ]

    def eliminated_values(value: ValueT) -> int:
        return sum(
            not _pair_is_consistent(csp, variable, value, other, other_value)
            for other in related_unassigned
            for other_value in domains[other]
        )

    return sorted(domains[variable], key=eliminated_values)


def backtracking_search(
    csp: CSP[VariableT, ValueT],
    domains: Mapping[VariableT, Sequence[ValueT]] | None = None,
) -> BacktrackingResult:
    """Find one complete assignment using backtracking, MRV, and LCV."""

    working_domains = _copy_domains(csp, domains)
    assignment: Assignment[VariableT, ValueT] = {}
    nodes_expanded = 0
    assignments_tried = 0
    backtracks = 0

    def search() -> Assignment[VariableT, ValueT] | None:
        nonlocal nodes_expanded, assignments_tried, backtracks

        if len(assignment) == len(csp.variables):
            return dict(assignment)

        variable = select_unassigned_variable(csp, assignment, working_domains)
        nodes_expanded += 1
        for value in order_domain_values(
            csp, variable, assignment, working_domains
        ):
            assignments_tried += 1
            if not is_consistent(csp, variable, value, assignment):
                continue

            assignment[variable] = value
            solution = search()
            if solution is not None:
                return solution
            del assignment[variable]

        backtracks += 1
        return None

    solution = search()
    ordered_solution = (
        {variable: solution[variable] for variable in csp.variables}
        if solution is not None
        else None
    )
    return BacktrackingResult(
        ordered_solution,
        BacktrackingStats(nodes_expanded, assignments_tried, backtracks),
    )
