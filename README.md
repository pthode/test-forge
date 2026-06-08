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

Constructor:

```python
from tokenlab.cache import LruCache, CacheStats

cache = LruCache(capacity=2)  # capacity: positive int
```

Constructing with a `capacity` below `1` raises `ValueError`:

```python
LruCache(0)    # ValueError: capacity must be a positive integer
LruCache(-1)   # ValueError: capacity must be a positive integer
```

#### Public API

**`get(key: Any, default: Any = None) -> Any`**

Returns the stored value for `key` if present and increments `hits`; promotes the key to most-recently-used. Returns `default` (or `None` if not supplied) and increments `misses` if the key is absent; does not insert or reorder entries.

**`put(key: Any, value: Any) -> None`**

Inserts a new key/value pair or updates an existing key, promoting it to most-recently-used in both cases. If inserting a new key causes the cache to exceed `capacity`, the least-recently-used entry is evicted and `evictions` increments by 1. Updating an existing key does not evict and does not increment `evictions`.

**`stats` property**

Returns a fresh frozen dataclass snapshot `CacheStats(hits: int, misses: int, evictions: int, size: int)` on each access:

- `hits` — count of successful `get` calls (non-negative, monotonic)
- `misses` — count of unsuccessful `get` calls (non-negative, monotonic)
- `evictions` — count of automatic evictions due to capacity overflow (non-negative, monotonic)
- `size` — current number of entries in the cache (0 ≤ size ≤ capacity)

All counters start at 0 and only increase; there is no method to reset them.

#### Semantics and examples

```python
from tokenlab.cache import LruCache

cache = LruCache(capacity=2)
cache.put("a", 1)
cache.put("b", 2)
cache.get("a")            # 1 — hit; "a" promoted to most-recently-used
cache.put("c", 3)         # at capacity: evicts "b" (least recently used)
cache.get("b")            # None — miss; "b" was evicted
cache.stats               # CacheStats(hits=1, misses=1, evictions=1, size=2)

# None is a storable value, distinct from an absent key:
cache.put("null_key", None)
cache.get("null_key")     # None — HIT (cache.stats.hits increments)
cache.get("absent")       # None — MISS (cache.stats.misses increments)

# Updating an existing key does not evict:
cache = LruCache(capacity=2)
cache.put("x", 10)
cache.put("y", 20)
cache.put("x", 100)       # update x; size stays 2, no eviction
cache.stats               # CacheStats(hits=0, misses=0, evictions=0, size=2)
```

#### Constraints

- **Keys must be hashable.** Passing an unhashable key (e.g. `list`, `dict`, `set`)
  to `get()` or `put()` raises `TypeError` from the underlying mapping, unwrapped.
- **Single-threaded only.** `LruCache` does not acquire internal locks. Concurrent
  access from multiple threads will corrupt state; the caller must serialize if needed.

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
- **`ValueError: capacity must be a positive integer`** — `LruCache` was constructed with a
  capacity of `0` or a negative number. Pass a positive integer.
- **`TypeError: unhashable type: ...`** — a `list`, `dict`, `set`, or other
  unhashable object was passed as a cache key. Keys must be hashable; this is the
  underlying mapping's own error, surfaced unwrapped.
- **An entry you expected to survive was evicted** — recency is true-LRU. Only
  `get` (on a hit) and `put` mark an entry as most-recently-used. On overflow,
  the true least-recently-used entry (not accessed in the longest time) is evicted.
  Check `cache.stats.evictions` to confirm an eviction occurred.

## Contributing

For the development workflow, see [CONTRIBUTING.md](CONTRIBUTING.md).
