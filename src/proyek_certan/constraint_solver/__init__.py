"""Generic constraint-satisfaction algorithms."""

from proyek_certan.constraint_solver.ac3 import (
    AC3Result,
    AC3Stats,
    ReviseResult,
    ac3,
    revise,
)
from proyek_certan.constraint_solver.backtracking import (
    BacktrackingResult,
    BacktrackingStats,
    backtracking_search,
    is_consistent,
    order_domain_values,
    select_unassigned_variable,
)
from proyek_certan.constraint_solver.csp import CSP, ConstraintFunction

__all__ = [
    "AC3Result",
    "AC3Stats",
    "BacktrackingResult",
    "BacktrackingStats",
    "CSP",
    "ConstraintFunction",
    "ReviseResult",
    "ac3",
    "backtracking_search",
    "is_consistent",
    "order_domain_values",
    "revise",
    "select_unassigned_variable",
]
