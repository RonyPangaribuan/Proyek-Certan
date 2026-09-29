"""End-to-end orchestration for the generic CSP solver."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Generic, Literal

from proyek_certan.constraint_solver.ac3 import AC3Stats, ac3
from proyek_certan.constraint_solver.backtracking import (
    Assignment,
    BacktrackingStats,
    backtracking_search,
)
from proyek_certan.constraint_solver.csp import CSP, ValueT, VariableT


SolverStatus = Literal["solved", "no-solution"]


@dataclass(frozen=True, slots=True)
class SolverStats:
    """Statistics from propagation and search."""

    ac3: AC3Stats
    backtracking: BacktrackingStats


@dataclass(frozen=True, slots=True)
class SolverResult(Generic[VariableT, ValueT]):
    """Structured result returned by the generic solver."""

    status: SolverStatus
    solution: Assignment[VariableT, ValueT] | None
    stats: SolverStats


def solve(csp: CSP[VariableT, ValueT]) -> SolverResult[VariableT, ValueT]:
    """Run initial AC-3 propagation followed by backtracking search."""

    propagation = ac3(csp)
    if not propagation.success:
        return SolverResult(
            status="no-solution",
            solution=None,
            stats=SolverStats(
                ac3=propagation.stats,
                backtracking=BacktrackingStats(),
            ),
        )

    search = backtracking_search(csp, propagation.domains)
    status: SolverStatus = (
        "solved" if search.solution is not None else "no-solution"
    )
    return SolverResult(
        status=status,
        solution=search.solution,
        stats=SolverStats(ac3=propagation.stats, backtracking=search.stats),
    )
