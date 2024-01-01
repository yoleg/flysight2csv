from dataclasses import dataclass
import re
from typing import Iterable, Optional, Pattern


@dataclass
class StringSelection:
    """A dataclass that can be used to define filters on string-like values."""

    case_insensitive: bool = False
    exclude_values: set[str] | list[str] | None = None
    include_values: set[str] | list[str] | None = None
    exclude_patterns: list[Pattern[str]] | None = None
    include_patterns: list[Pattern[str]] | None = None

    def __init__(
        self,
        case_insensitive: bool = False,
        exclude_values: Iterable[str] | None = None,
        include_values: Iterable[str] | None = None,
        exclude_patterns: Iterable[str] | None = None,
        include_patterns: Iterable[str] | None = None,
    ):
        super().__init__()
        """Normalize the values and compile the patterns for performance."""
        self.case_insensitive = case_insensitive  # TODO: make this a property
        self.exclude_values = None if exclude_values is None else {self._normalize(x) for x in exclude_values}
        self.include_values = None if include_values is None else {self._normalize(x) for x in include_values}
        self.exclude_patterns = None if exclude_patterns is None else self.compile_patterns(exclude_patterns)
        self.include_patterns = None if include_patterns is None else self.compile_patterns(include_patterns)

    def __bool__(self) -> bool:
        """Returns True if any of the filters are set."""
        return (
            self.exclude_values is not None
            or self.include_values is not None
            or self.exclude_patterns is not None
            or self.include_patterns is not None
        )

    @classmethod
    def compile_patterns(self, patterns: Iterable[str]) -> list[Pattern[str]]:
        """Compile the patterns for performance."""
        return [re.compile(x, re.IGNORECASE if self.case_insensitive else 0) for x in patterns]

    def _normalize(self, string: str) -> str:
        if self.case_insensitive:
            return string.lower()
        return string

    def matches(self, column: str) -> bool:
        """Returns True if the column should be included in the output."""
        if self.case_insensitive:
            column = column.lower()
        if self.exclude_values is not None and column in self.exclude_values:
            return False
        if self.include_values is not None and column not in self.include_values:
            return False
        if self.exclude_patterns is not None and any(x.match(column) for x in self.exclude_patterns):
            return False
        if self.include_patterns is not None and not any(x.match(column) for x in self.include_patterns):
            return False
        return True

    def filter_strings(self, strings: Iterable[str]) -> Iterable[str]:
        """Returns the strings that match the selection."""
        return (x for x in strings if self.matches(x))


def filter_strings(strings: Iterable[str], selection: Optional[StringSelection] = None) -> Iterable[str]:
    """Filters the columns by the selection."""
    if not selection:
        return strings
    return selection.filter_strings(strings)
