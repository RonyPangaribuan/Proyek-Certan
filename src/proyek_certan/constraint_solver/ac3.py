"""AC-3 constraint propagation for generic binary CSPs."""

from __future__ import annotations

from collections import deque
from collections.abc import Mapping, Sequence
from dataclasses import dataclass

from proyek_certan.constraint_solver.csp import CSP, DomainMap, ValueT, VariableT


@dataclass(frozen=True, slots=True)
class ReviseResult:
    """Outcome of revising one directed arc."""

    revised: bool
    values_pruned: int


@dataclass(frozen=True, slots=True)
class AC3Stats:
    """Operation counts collected during AC-3 propagation."""

    arcs_processed: int = 0
    revised_arcs: int = 0
    values_pruned: int = 0


@dataclass(frozen=True, slots=True)
class AC3Result:
    """Arc-consistency result and the independent working domains."""

    success: bool
    domains: DomainMap[VariableT, ValueT]
    stats: AC3Stats


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


def revise(
    csp: CSP[VariableT, ValueT],
    domains: DomainMap[VariableT, ValueT],
    xi: VariableT,
    xj: VariableT,
) -> ReviseResult:
    """Remove values of Xi with no supporting value in Xj."""

    if xi not in csp.neighbors or xj not in csp.neighbors[xi]:
        raise ValueError(f"({xi!r}, {xj!r}) is not a directed CSP arc")

    original_values = domains[xi]
    supported_values = [
        value_i
        for value_i in original_values
        if any(
            csp.constraint(xi, value_i, xj, value_j)
            for value_j in domains[xj]
        )
    ]
    values_pruned = len(original_values) - len(supported_values)
    if values_pruned:
        domains[xi] = supported_values

    return ReviseResult(revised=values_pruned > 0, values_pruned=values_pruned)


def ac3(
    csp: CSP[VariableT, ValueT],
    domains: Mapping[VariableT, Sequence[ValueT]] | None = None,
) -> AC3Result:
    """Enforce arc consistency without mutating the supplied domains."""

    working_domains = _copy_domains(csp, domains)
    if any(not working_domains[variable] for variable in csp.variables):
        return AC3Result(False, working_domains, AC3Stats())

    queue = deque(
        (xi, xj)
        for xi in csp.variables
        for xj in csp.neighbors[xi]
    )
    predecessors = {
        variable: tuple(
            candidate
            for candidate in csp.variables
            if variable in csp.neighbors[candidate]
        )
        for variable in csp.variables
    }
    arcs_processed = 0
    revised_arcs = 0
    values_pruned = 0

    while queue:
        xi, xj = queue.popleft()
        arcs_processed += 1
        revision = revise(csp, working_domains, xi, xj)
        values_pruned += revision.values_pruned

        if not revision.revised:
            continue

        revised_arcs += 1
        if not working_domains[xi]:
            return AC3Result(
                False,
                working_domains,
                AC3Stats(arcs_processed, revised_arcs, values_pruned),
            )

        for xk in predecessors[xi]:
            if xk != xj:
                queue.append((xk, xi))

    return AC3Result(
        True,
        working_domains,
        AC3Stats(arcs_processed, revised_arcs, values_pruned),
    )
