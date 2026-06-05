# tokenlab

A small, dependency-free Python library of token- and string-parsing primitives.
Pure standard library, Python 3.12+, no external runtime dependencies.

The primitives so far are:

- `parse_duration` — converts a compact human-readable duration string such as
  `"1h30m"` into a total count of whole seconds.
- `LruCache` — a bounded, in-memory least-recently-used cache class.

## Install

tokenlab is a standard-library-only module. There is nothing to install beyond
CPython 3.12 or newer. Make the `src/` directory importable (for example by
running from the project root or adding `src/` to `PYTHONPATH`):

```bash
export PYTHONPATH=src   # PowerShell: $env:PYTHONPATH = "src"
```

```python
from tokenlab.duration import parse_duration
from tokenlab.cache import LruCache
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

### `LruCache(capacity: int)`

A fixed-capacity, in-memory cache that evicts the least-recently-used entry when
inserting a new key would exceed `capacity`. Recency is **true-LRU**: a `get`
hit and any `put` mark the touched entry most-recently-used, and the entry left
untouched the longest is the one evicted. `None` is a storable value, distinct
from an absent key.

```python
from tokenlab.cache import LruCache

cache = LruCache(capacity=2)
```

Constructing with a `capacity` below `1` raises `ValueError`:

```python
LruCache(0)    # ValueError
LruCache(-1)   # ValueError
```

#### `LruCache` public surface

| Member | Returns | Effect on recency | Effect on counters |
| --- | --- | --- | --- |
| `get(key, default=None)` | stored value on a hit, else `default` | hit refreshes to most-recently-used | hit `+1` `hits`; miss `+1` `misses` |
| `put(key, value)` | `None` | inserts/overwrites as most-recently-used | new key at capacity `+1` `evictions` |
| `peek(key, default=None)` | stored value if present, else `default` | none | none |
| `remove(key)` | `True` if it was present, else `False` | n/a | none |
| `clear()` | `None` | drops all entries | counters left unchanged |
| `reset_stats()` | `None` | entries left intact | zeroes `hits`/`misses`/`evictions` |
| `key in cache` (`__contains__`) | `bool` | none | none |
| `len(cache)` (`__len__`) | current entry count | none | none |

Five read-only `int` properties expose lifetime statistics. Assigning to any of
them raises `AttributeError`:

| Property | Meaning |
| --- | --- |
| `hits` | cumulative `get` hits since construction or the last `reset_stats` |
| `misses` | cumulative `get` misses since construction or the last `reset_stats` |
| `evictions` | cumulative evictions since construction or the last `reset_stats` |
| `size` | current number of cached entries (also `len(cache)`) |
| `capacity` | maximum entries before a new insert evicts; never changes after construction |

#### `LruCache` semantics

- **Hit vs. miss.** `get` on a present key returns its value (which may itself be
  `None`) and counts a hit; `get` on an absent key returns `default` (`None` when
  omitted), counts a miss, and does **not** insert the key.
- **`put` on an existing key** overwrites the value and refreshes recency without
  growing `size`.
- **Eviction** happens only when inserting a *new* key while `size == capacity`;
  it removes the genuinely least-recently-used entry, increments `evictions`, and
  keeps `size == capacity`. Filling exactly to capacity evicts nothing.
- **`peek` and `in` are inspection-only.** Neither refreshes recency nor touches
  the hit/miss counters, so they never protect an entry from eviction.
- **`clear` and `reset_stats` are orthogonal.** `clear` drops entries but keeps
  the lifetime counters; `reset_stats` zeroes the counters but keeps the entries.
  Call both to reset everything.
- **`remove` is forgiving.** Removing an absent key is a no-op that returns
  `False` and never raises.
- **Keys must be hashable.** Passing an unhashable key (e.g. a `list` or `set`)
  to any key-accepting method surfaces the underlying mapping's natural
  `TypeError`, unwrapped — no custom validation is layered on top.
- **Not thread-safe.** `LruCache` acquires no internal lock. A caller sharing one
  instance across threads must serialize access itself.

#### `LruCache` examples

```python
from tokenlab.cache import LruCache

cache = LruCache(2)
cache.put("a", 1)
cache.put("b", 2)
cache.get("a")            # 1 — hit; "a" is now most-recently-used
cache.put("c", 3)         # at capacity: evicts "b" (least recently used)
"b" in cache              # False — evicted
"a" in cache              # True  — protected by the earlier get
cache.evictions           # 1

# None is a stored value, distinct from an absent key:
cache.put("k", None)
cache.get("k")            # None — but this is a HIT (cache.hits increments)
cache.get("absent")      # None — this is a MISS (cache.misses increments)

# Inspection without side effects:
cache.peek("k")           # None — does not count, does not refresh recency
len(cache)                # current entry count

# Mutation:
cache.remove("k")         # True  — was present and removed
cache.remove("gone")      # False — absent, no-op, no exception
cache.clear()             # drops all entries; counters retained
cache.reset_stats()       # zeroes hits/misses/evictions; entries retained
```

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
- **`ValueError: capacity must be >= 1`** — `LruCache` was constructed with a
  capacity of `0` or a negative number. Pass an integer of at least `1`.
- **`TypeError: unhashable type: ...`** — a `list`, `dict`, `set`, or other
  unhashable object was passed as a cache key. Keys must be hashable; this is the
  underlying mapping's own error, surfaced unwrapped.
- **`AttributeError` when assigning to `cache.hits` (or another stat)** — the five
  statistics fields (`hits`, `misses`, `evictions`, `size`, `capacity`) are
  read-only. Use `reset_stats()` to zero the counters; the cache manages `size`
  and `capacity` itself.
- **An entry you expected to survive was evicted** — recency is true-LRU, and only
  `get`, `put`, and overwriting a key refresh recency. `peek` and `key in cache`
  are inspection-only and do **not** protect an entry. Inspect `cache.evictions`
  to confirm an eviction occurred.

## Contributing

For the development workflow, see [CONTRIBUTING.md](CONTRIBUTING.md).
