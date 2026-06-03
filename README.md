# tokenlab

A small, dependency-free Python library of token- and string-parsing primitives.
Pure standard library, Python 3.12+, no external runtime dependencies.

The first primitive is `parse_duration`, which converts a compact human-readable
duration string such as `"1h30m"` into a total count of whole seconds.

## Install

tokenlab is a standard-library-only module. There is nothing to install beyond
CPython 3.12 or newer. Make the `src/` directory importable (for example by
running from the project root or adding `src/` to `PYTHONPATH`):

```bash
export PYTHONPATH=src   # PowerShell: $env:PYTHONPATH = "src"
```

```python
from tokenlab.duration import parse_duration
```

## Usage

### `parse_duration(s: str) -> int`

Converts a compact duration string to a total count of whole seconds. Returns a
non-negative `int` equal to `hours * 3600 + minutes * 60 + seconds`. Raises
`ValueError` for any input that does not match the grammar below.

#### Grammar

A valid input is **one or more `<integer><unit>` components** concatenated with
no separators. The rules are:

- **Units are exactly `h` (hours), `m` (minutes), `s` (seconds)** — lowercase
  only. No other suffix is accepted.
- **Units must appear in strict descending order** — `h` before `m` before `s`.
- **Each unit appears at most once.** Repeats are invalid.
- **Each integer is a non-negative base-10 number** — no sign, no decimal point.
  Leading zeros are accepted (`"01h"` is `3600`).
- **No bare integers.** Every number needs a unit (`"90"` is invalid).
- **No negatives** (`"-1h"` is invalid).
- **Leading and trailing whitespace is trimmed**, but whitespace *between*
  components is invalid (`"1h 30m"` is invalid).
- **`"0s"` returns `0`.** There is no per-component cap and no clock-range
  validation — `"90m"` is `5400`, not rejected.

#### Examples

```python
from tokenlab.duration import parse_duration

parse_duration("1h30m")      # 5400
parse_duration("2h15m30s")   # 8130
parse_duration("45s")        # 45
parse_duration("0s")         # 0
parse_duration("90m")        # 5400  (no clock-range cap)
parse_duration("01h")        # 3600  (leading zeros allowed)
parse_duration("  1h  ")     # 3600  (outer whitespace trimmed)
```

Invalid input raises `ValueError`:

```python
parse_duration("")        # ValueError — empty
parse_duration("90")      # ValueError — bare integer, no unit
parse_duration("1H")      # ValueError — uppercase suffix
parse_duration("1d")      # ValueError — unsupported unit
parse_duration("-1h")     # ValueError — negative
parse_duration("1.5h")    # ValueError — decimal component
parse_duration("30m1h")   # ValueError — out of order
parse_duration("1h1h")    # ValueError — repeated unit
parse_duration("1h 30m")  # ValueError — whitespace between components
parse_duration("PT1H30M") # ValueError — ISO-8601 not supported
```

The function is total over `str`: for any string it either returns a
non-negative `int` or raises `ValueError`. It never raises another exception
type for a malformed string, and it never returns a sentinel or silent default.

## Run the tests

```bash
PYTHONPATH=src pytest        # PowerShell: $env:PYTHONPATH = "src"; pytest
```

## Troubleshooting

- **`ModuleNotFoundError: No module named 'tokenlab'`** — `src/` is not on the
  import path. Set `PYTHONPATH=src` (or run from the project root with that set).
- **`ValueError: invalid duration string: ...`** — the input does not match the
  grammar above. The most common causes are uppercase units (`"1H"`), bare
  integers with no unit (`"90"`), out-of-order or repeated units (`"30m1h"`,
  `"1h1h"`), and whitespace between components (`"1h 30m"`). The message echoes
  the trimmed input so you can see exactly what was parsed.

## Contributing

For the development workflow, see [CONTRIBUTING.md](CONTRIBUTING.md).
