"""Parse compact human-readable duration strings into whole seconds."""

import re

# Whole-input shape: one or more <digits><unit> components, no separators,
# with only outer whitespace permitted (stripped before this matches).
_DURATION_PATTERN = re.compile(r"\A(?:[0-9]+[hms])+\Z")

# Single component: a base-10 integer (leading zeros allowed) plus its unit.
_COMPONENT_PATTERN = re.compile(r"([0-9]+)([hms])")

_UNIT_SECONDS = {"h": 3600, "m": 60, "s": 1}

# Strict descending magnitude order: h before m before s, each at most once.
_UNIT_ORDER = {"h": 0, "m": 1, "s": 2}


def parse_duration(s: str) -> int:
    """Convert a compact duration string to a total count of whole seconds.

    Accepted grammar: one or more ``<integer><unit>`` components concatenated
    with no separators, where ``integer`` is a non-negative base-10 number
    (leading zeros allowed, no sign, no decimal point) and ``unit`` is one of
    ``h`` (hours), ``m`` (minutes), or ``s`` (seconds), lowercase only. Each
    unit may appear at most once, and present units must be in strict
    descending magnitude order (``h`` before ``m`` before ``s``). Leading and
    trailing whitespace is trimmed; whitespace between components is invalid.

    Returns the total duration as a non-negative ``int`` equal to
    ``hours * 3600 + minutes * 60 + seconds``. There is no per-component cap
    and no clock-range validation (``"90m"`` is 5400), and ``"0s"`` is 0.

    Raises ``ValueError`` for any invalid input, including empty or
    whitespace-only strings, bare integers, unknown or uppercase suffixes,
    negative or decimal components, repeated units, and out-of-order units.

    Examples:
        >>> parse_duration("1h30m")
        5400
        >>> parse_duration("2h15m30s")
        8130
        >>> parse_duration("45s")
        45
        >>> parse_duration("90")  # bare integer, no unit
        Traceback (most recent call last):
        ValueError: invalid duration string: '90'
    """
    trimmed = s.strip()
    if not _DURATION_PATTERN.match(trimmed):
        raise ValueError(f"invalid duration string: {trimmed!r}")

    total = 0
    previous_rank = -1
    for value, unit in _COMPONENT_PATTERN.findall(trimmed):
        rank = _UNIT_ORDER[unit]
        # Strict descending order also rules out a repeated unit (equal rank).
        if rank <= previous_rank:
            raise ValueError(f"invalid duration string: {trimmed!r}")
        previous_rank = rank
        total += int(value) * _UNIT_SECONDS[unit]

    return total
