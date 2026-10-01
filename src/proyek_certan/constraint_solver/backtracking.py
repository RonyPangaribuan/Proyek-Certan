"""Backtracking search with MRV and LCV for generic binary CSPs."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Generic

from proyek_certan.constraint_solver.csp import CSP, DomainMap, ValueT, VariableT


Assignment = dict[VariableT, ValueT]


@dataclass(frozen=True, slots=True)
class BacktrackingStats:
    """Operation counts collected during recursive backtracking."""

    nodes_expanded: int = 0
    assignments_tried: int = 0
    backtracks: int = 0
    forward_checks: int = 0
    fc_values_pruned: int = 0


@dataclass(frozen=True, slots=True)
class ForwardCheckResult(Generic[VariableT, ValueT]):
    """Branch-local domains produced by one forward-checking step."""

    success: bool
    domains: DomainMap[VariableT, ValueT]
    values_pruned: int


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


def forward_check(
    csp: CSP[VariableT, ValueT],
    variable: VariableT,
    value: ValueT,
    assignment: Mapping[VariableT, ValueT],
    domains: Mapping[VariableT, Sequence[ValueT]],
) -> ForwardCheckResult[VariableT, ValueT]:
    """Prune incompatible values from unassigned neighboring domains."""

    branch_domains = _copy_domains(csp, domains)
    values_pruned = 0

    for other in csp.variables:
        if other == variable or other in assignment:
            continue
        if (
            other not in csp.neighbors[variable]
            and variable not in csp.neighbors[other]
        ):
            continue

        original_values = branch_domains[other]
        supported_values = [
            other_value
            for other_value in original_values
            if _pair_is_consistent(
                csp,
                variable,
                value,
                other,
                other_value,
            )
        ]
        values_pruned += len(original_values) - len(supported_values)
        branch_domains[other] = supported_values
        if not supported_values:
            return ForwardCheckResult(
                success=False,
                domains=branch_domains,
                values_pruned=values_pruned,
            )

    return ForwardCheckResult(
        success=True,
        domains=branch_domains,
        values_pruned=values_pruned,
    )


def select_unassigned_variable(
    csp: CSP[VariableT, ValueT],
    assignment: Mapping[VariableT, ValueT],
    domains: Mapping[VariableT, Sequence[ValueT]],
) -> VariableT:
    """Select by currently legal values, then declared variable order."""

    candidates = [
        variable for variable in csp.variables if variable not in assignment
    ]
    if not candidates:
        raise ValueError("cannot select a variable from a complete assignment")

    def legal_value_count(variable: VariableT) -> int:
        return sum(
            is_consistent(csp, variable, value, assignment)
            for value in domains[variable]
        )

    return min(candidates, key=legal_value_count)


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
            if is_consistent(csp, other, other_value, assignment)
        )

    return sorted(
        domains[variable],
        key=lambda value: (
            not is_consistent(csp, variable, value, assignment),
            eliminated_values(value),
        ),
    )


def backtracking_search(
    csp: CSP[VariableT, ValueT],
    domains: Mapping[VariableT, Sequence[ValueT]] | None = None,
) -> BacktrackingResult:
    """Find an assignment with MRV, LCV, and branch-local forward checking."""

    working_domains = _copy_domains(csp, domains)
    assignment: Assignment[VariableT, ValueT] = {}
    nodes_expanded = 0
    assignments_tried = 0
    backtracks = 0
    forward_checks = 0
    fc_values_pruned = 0

    def search(
        current_domains: Mapping[VariableT, Sequence[ValueT]],
    ) -> Assignment[VariableT, ValueT] | None:
        nonlocal nodes_expanded, assignments_tried, backtracks
        nonlocal forward_checks, fc_values_pruned

        if len(assignment) == len(csp.variables):
            return dict(assignment)

        variable = select_unassigned_variable(csp, assignment, current_domains)
        nodes_expanded += 1
        for value in order_domain_values(
            csp, variable, assignment, current_domains
        ):
            assignments_tried += 1
            if not is_consistent(csp, variable, value, assignment):
                continue

            assignment[variable] = value
            forward_checks += 1
            check = forward_check(
                csp,
                variable,
                value,
                assignment,
                current_domains,
            )
            fc_values_pruned += check.values_pruned
            if check.success:
                solution = search(check.domains)
                if solution is not None:
                    return solution
            del assignment[variable]

        backtracks += 1
        return None

    solution = search(working_domains)
    ordered_solution = (
        {variable: solution[variable] for variable in csp.variables}
        if solution is not None
        else None
    )
    return BacktrackingResult(
        ordered_solution,
        BacktrackingStats(
            nodes_expanded=nodes_expanded,
            assignments_tried=assignments_tried,
            backtracks=backtracks,
            forward_checks=forward_checks,
            fc_values_pruned=fc_values_pruned,
        ),
    )
