import re
from typing import TypeVar

T = TypeVar("T")


def OneOf(*allowed: T):
    allowed_set = set(allowed)

    def _check(value: T):
        if value not in allowed_set:
            raise ValueError(f"`{value}` is not one of {allowed_set}")

    return _check


def Matches(expr: str | re.Pattern[str], flags: int = 0):
    pattern = re.compile(expr) if isinstance(expr, str) else expr

    def _check(value: str):
        if not pattern.match(value):
            raise ValueError(
                f"`{value}` must match regular expression: {pattern.pattern}"
            )

    return _check
