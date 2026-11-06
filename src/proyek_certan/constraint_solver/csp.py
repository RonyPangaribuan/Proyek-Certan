"""Generic representation for a binary constraint satisfaction problem."""

from __future__ import annotations

from collections.abc import Callable, Hashable, Mapping
from dataclasses import dataclass
from types import MappingProxyType
from typing import Generic, TypeVar


VariableT = TypeVar("VariableT", bound=Hashable)
ValueT = TypeVar("ValueT")
ConstraintFunction = Callable[[VariableT, ValueT, VariableT, ValueT], bool]
DomainMap = dict[VariableT, list[ValueT]]


@dataclass(frozen=True, slots=True)
class CSP(Generic[VariableT, ValueT]):
    """A generic binary CSP with ordered variables and domain values.

    Each entry in ``neighbors`` declares a directed arc. For a conventional
    undirected constraint graph, callers should list each relationship in both
    directions.
    """

    variables: tuple[VariableT, ...]
    domains: Mapping[VariableT, tuple[ValueT, ...]]
    neighbors: Mapping[VariableT, tuple[VariableT, ...]]
    constraint: ConstraintFunction[VariableT, ValueT]

    def __post_init__(self) -> None:
        variables = tuple(self.variables)
        try:
            variable_set = set(variables)
        except TypeError as error:
            raise TypeError("CSP variables must be hashable") from error

        if len(variable_set) != len(variables):
            raise ValueError("CSP variables must be unique")
        if not callable(self.constraint):
            raise TypeError("constraint must be callable")

        self._validate_mapping_keys("domains", self.domains, variables, variable_set)
        self._validate_mapping_keys(
            "neighbors", self.neighbors, variables, variable_set
        )

        normalized_domains = {
            variable: tuple(self.domains[variable]) for variable in variables
        }
        normalized_neighbors: dict[VariableT, tuple[VariableT, ...]] = {}
        for variable in variables:
            neighbor_values = tuple(self.neighbors[variable])
            unknown = [item for item in neighbor_values if item not in variable_set]
            if unknown:
                raise ValueError(
                    f"neighbors for {variable!r} reference unknown variables: "
                    f"{unknown!r}"
                )
            if variable in neighbor_values:
                raise ValueError(f"variable {variable!r} cannot be its own neighbor")
            if len(set(neighbor_values)) != len(neighbor_values):
                raise ValueError(f"neighbors for {variable!r} must be unique")
            normalized_neighbors[variable] = neighbor_values

        object.__setattr__(self, "variables", variables)
        object.__setattr__(self, "domains", MappingProxyType(normalized_domains))
        object.__setattr__(
            self, "neighbors", MappingProxyType(normalized_neighbors)
        )

    @staticmethod
    def _validate_mapping_keys(
        name: str,
        mapping: Mapping[VariableT, object],
        variables: tuple[VariableT, ...],
        variable_set: set[VariableT],
    ) -> None:
        missing = [variable for variable in variables if variable not in mapping]
        extra = [variable for variable in mapping if variable not in variable_set]
        if missing or extra:
            details: list[str] = []
            if missing:
                details.append(f"missing variables: {missing!r}")
            if extra:
                details.append(f"unknown variables: {extra!r}")
            raise ValueError(f"{name} must match CSP variables; " + "; ".join(details))

    def copy_domains(self) -> DomainMap[VariableT, ValueT]:
        """Return mutable copies of all domains in declared variable order."""

        return {
            variable: list(self.domains[variable]) for variable in self.variables
        }
