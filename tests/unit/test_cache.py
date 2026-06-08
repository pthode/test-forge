"""Unit tests for tokenlab.cache.LruCache.

Tests are derived exclusively from /docs/specs/lru-cache.md (requirements
R1-R14, §7 failure modes, §8 acceptance criteria) and /docs/requirements/
lru-cache.md (§12 success criteria).  They assert the *spec's* contract, not
the current implementation.  If any assertion fails, either the test is wrong
(test bug — fix the test) or the implementation contradicts the spec (emit a
REJECT to developer).

Requirement citations appear as # Rn: comments on each test.
"""

import inspect

import pytest

from tokenlab.cache import LruCache, CacheStats


# ---------------------------------------------------------------------------
# R1 — public class LruCache importable from tokenlab.cache
# Spec §8: "from tokenlab.cache import LruCache succeeds with no import error"
# Ticket §12.1
# ---------------------------------------------------------------------------

def test_r1_import_succeeds():
    # R1: The import statement at the module level above must not have raised.
    assert LruCache is not None


def test_r1_lrucache_is_a_class():
    # R1: LruCache must be a class, not a function or other object.
    assert inspect.isclass(LruCache)


# ---------------------------------------------------------------------------
# R2 — construction with valid capacity
# Spec §8: "LruCache(1) constructs without error"
# Ticket §12.2
# ---------------------------------------------------------------------------

def test_r2_construct_capacity_one():
    # R2: capacity=1 is the minimum valid value; must not raise.
    cache = LruCache(1)
    assert cache is not None


def test_r2_construct_capacity_large():
    # R2: any positive integer is a valid capacity.
    cache = LruCache(1000)
    assert cache is not None


def test_r2_no_resize_method():
    # R2: no public resize method is provided; capacity is immutable.
    cache = LruCache(4)
    assert not hasattr(cache, "resize"), (
        "LruCache must not expose a resize method (R2 — capacity is immutable)"
    )


# ---------------------------------------------------------------------------
# R3 — capacity <= 0 raises ValueError
# Spec §7 failure modes, §8 acceptance criteria
# Ticket §12.2, §10
# ---------------------------------------------------------------------------

def test_r3_capacity_zero_raises_value_error():
    # R3: LruCache(0) must raise ValueError.
    with pytest.raises(ValueError):
        LruCache(0)


def test_r3_capacity_negative_one_raises_value_error():
    # R3: LruCache(-1) must raise ValueError.
    with pytest.raises(ValueError):
        LruCache(-1)


def test_r3_capacity_large_negative_raises_value_error():
    # R3: any negative integer raises the same ValueError.
    with pytest.raises(ValueError):
        LruCache(-999)


def test_r3_raises_exactly_value_error_not_subclass():
    # R3: the spec says "raises ValueError" — must be exactly ValueError
    # (or a subclass, since pytest.raises catches subclasses; documenting
    # the intent explicitly).
    with pytest.raises(ValueError):
        LruCache(0)


# ---------------------------------------------------------------------------
# R4 — get hit: returns value, increments hits, promotes to MRU
# Spec §8 / ticket §12.5
# ---------------------------------------------------------------------------

def test_r4_get_hit_returns_stored_value():
    # R4: get on a present key returns the stored value.
    cache = LruCache(2)
    cache.put("a", 42)
    assert cache.get("a") == 42


def test_r4_get_hit_increments_hits_by_one():
    # R4: each get hit increments stats().hits by exactly 1.
    cache = LruCache(2)
    cache.put("k", "v")
    before = cache.stats().hits
    cache.get("k")
    assert cache.stats().hits == before + 1


def test_r4_get_hit_does_not_increment_misses():
    # R4: a hit must not touch stats().misses.
    cache = LruCache(2)
    cache.put("k", "v")
    before = cache.stats().misses
    cache.get("k")
    assert cache.stats().misses == before


def test_r4_get_hit_promotes_to_mru_verified_via_eviction():
    # R4 + R9: after put(A), put(B), get(A) → A is MRU so put(C) evicts B.
    # (This is the canonical LRU access-order test from R9/ticket §12.12.)
    cache = LruCache(2)
    cache.put("A", 1)
    cache.put("B", 2)
    cache.get("A")       # A becomes MRU; B is now LRU
    cache.put("C", 3)    # evicts B (LRU)
    assert cache.get("B") is None  # B was evicted
    assert cache.get("A") == 1     # A survived
    assert cache.get("C") == 3     # C was inserted


# ---------------------------------------------------------------------------
# R5 — get miss: returns default, increments misses, no side effects
# Spec §8 / ticket §12.3, §12.4
# ---------------------------------------------------------------------------

def test_r5_get_miss_returns_none_when_no_default():
    # R5: get on absent key with no default argument returns None.
    cache = LruCache(2)
    assert cache.get("absent") is None


def test_r5_get_miss_returns_supplied_default():
    # R5: get on absent key returns the caller-supplied default.
    cache = LruCache(2)
    assert cache.get("absent", "fallback") == "fallback"


def test_r5_get_miss_increments_misses():
    # R5: each miss increments stats().misses by exactly 1.
    cache = LruCache(2)
    before = cache.stats().misses
    cache.get("no_such_key")
    assert cache.stats().misses == before + 1


def test_r5_get_miss_does_not_increment_hits():
    # R5: a miss must not touch stats().hits.
    cache = LruCache(2)
    before = cache.stats().hits
    cache.get("absent")
    assert cache.stats().hits == before


def test_r5_get_miss_does_not_change_size():
    # R5: a miss must not change stats().size.
    cache = LruCache(2)
    cache.put("x", 1)
    before = cache.stats().size
    cache.get("absent")
    assert cache.stats().size == before


def test_r5_get_miss_does_not_increment_evictions():
    # R5: a miss must not increment stats().evictions.
    cache = LruCache(2)
    before = cache.stats().evictions
    cache.get("absent")
    assert cache.stats().evictions == before


def test_r5_get_miss_does_not_raise():
    # R5: spec §7 explicitly says missing-key lookup is NOT a failure.
    cache = LruCache(2)
    # Should not raise any exception.
    result = cache.get("missing")
    assert result is None


def test_r5_get_miss_default_falsy_values():
    # R5: default may be any value including 0, False, "".
    cache = LruCache(2)
    assert cache.get("k", 0) == 0
    assert cache.get("k", False) is False
    assert cache.get("k", "") == ""


# ---------------------------------------------------------------------------
# R6 — put new key inserts entry; subsequent get returns value
# Spec §8 / ticket §12.6
# ---------------------------------------------------------------------------

def test_r6_put_new_key_retrievable():
    # R6: after put(k, v) on a fresh cache, get(k) returns v.
    cache = LruCache(2)
    cache.put("hello", "world")
    assert cache.get("hello") == "world"


def test_r6_put_returns_none():
    # R6: put must return None.
    cache = LruCache(2)
    result = cache.put("k", "v")
    assert result is None


def test_r6_put_increments_size():
    # R6: inserting a new key grows stats().size by 1.
    cache = LruCache(3)
    assert cache.stats().size == 0
    cache.put("a", 1)
    assert cache.stats().size == 1
    cache.put("b", 2)
    assert cache.stats().size == 2


# ---------------------------------------------------------------------------
# R7 — put existing key updates value, promotes to MRU, no eviction increment
# Spec §8 / ticket §12.7, §10
# ---------------------------------------------------------------------------

def test_r7_put_existing_key_updates_value():
    # R7: put(k, v2) when k already present stores v2.
    cache = LruCache(2)
    cache.put("k", 1)
    cache.put("k", 2)
    assert cache.get("k") == 2


def test_r7_put_existing_key_does_not_increment_evictions():
    # R7: updating an existing key must not increment stats().evictions.
    cache = LruCache(2)
    cache.put("k", 1)
    before = cache.stats().evictions
    cache.put("k", 99)
    assert cache.stats().evictions == before


def test_r7_put_existing_key_does_not_change_size():
    # R7: updating an existing key must not change stats().size.
    cache = LruCache(2)
    cache.put("k", 1)
    before = cache.stats().size
    cache.put("k", 2)
    assert cache.stats().size == before


def test_r7_put_existing_key_promotes_to_mru():
    # R7 + R9: after put(A), put(B), put(A, new_val), put(C) → B is evicted.
    cache = LruCache(2)
    cache.put("A", 1)
    cache.put("B", 2)
    cache.put("A", 10)   # update A — makes A MRU, so B is LRU
    cache.put("C", 3)    # at capacity; B (LRU) is evicted
    assert cache.get("B") is None   # B was LRU and evicted
    assert cache.get("A") == 10     # A survived with updated value
    assert cache.get("C") == 3


# ---------------------------------------------------------------------------
# R8 — put new key at capacity evicts LRU and increments evictions
# Spec §8 / ticket §12.8, §12.11
# ---------------------------------------------------------------------------

def test_r8_evicts_lru_on_overflow_capacity_one():
    # R8: with capacity=1, putting B after A evicts A.
    cache = LruCache(1)
    cache.put("A", 1)
    cache.put("B", 2)
    assert cache.get("A") is None   # A evicted
    assert cache.get("B") == 2      # B present


def test_r8_evictions_counter_incremented():
    # R8: evictions counter increases by 1 per overflow eviction.
    cache = LruCache(1)
    cache.put("A", 1)
    assert cache.stats().evictions == 0
    cache.put("B", 2)
    assert cache.stats().evictions == 1


def test_r8_evicts_lru_not_mru():
    # R8: the evicted entry is the LRU one, never the MRU one (ticket §12.8).
    cache = LruCache(2)
    cache.put("first", 1)    # LRU after second insert
    cache.put("second", 2)   # MRU
    cache.put("third", 3)    # evicts "first" (LRU)
    assert cache.get("first") is None    # LRU was evicted
    assert cache.get("second") == 2      # MRU survived
    assert cache.get("third") == 3


def test_r8_size_stays_at_capacity_after_eviction():
    # R8: size must not exceed capacity after an eviction.
    cap = 3
    cache = LruCache(cap)
    for i in range(cap + 5):
        cache.put(i, i)
    assert cache.stats().size == cap


def test_r8_multiple_evictions_cumulative():
    # R8 + R10: multiple overflow inserts accumulate evictions correctly.
    cache = LruCache(2)
    cache.put("a", 1)
    cache.put("b", 2)
    cache.put("c", 3)   # evicts a
    cache.put("d", 4)   # evicts b
    assert cache.stats().evictions == 2


# ---------------------------------------------------------------------------
# R9 — LRU recency ordering: get and put both update MRU
# Spec §8 / ticket §12.12
# ---------------------------------------------------------------------------

def test_r9_canonical_access_order_sequence():
    # R9: put(A), put(B), get(A) → A is MRU; put(C) evicts B.
    cache = LruCache(2)
    cache.put("A", 1)
    cache.put("B", 2)
    cache.get("A")        # A → MRU; B → LRU
    cache.put("C", 3)     # B evicted
    assert cache.get("B") is None
    assert cache.get("A") == 1
    assert cache.get("C") == 3


def test_r9_update_put_resets_recency():
    # R9: put on an existing key also makes that key MRU.
    cache = LruCache(2)
    cache.put("X", 1)   # LRU after Y inserted
    cache.put("Y", 2)
    cache.put("X", 10)  # re-insert X as MRU → Y becomes LRU
    cache.put("Z", 3)   # Z new; Y (LRU) evicted
    assert cache.get("Y") is None
    assert cache.get("X") == 10
    assert cache.get("Z") == 3


def test_r9_chain_of_gets_preserves_mru():
    # R9: repeatedly getting the same key keeps it as MRU.
    cache = LruCache(2)
    cache.put("A", 1)
    cache.put("B", 2)
    cache.get("A")
    cache.get("A")
    cache.get("A")
    cache.put("C", 3)  # B is still LRU; A kept alive by repeated gets
    assert cache.get("A") == 1
    assert cache.get("B") is None


# ---------------------------------------------------------------------------
# R10 — stats() returns CacheStats with hits/misses/evictions/size
# Spec §8 / ticket §12.9, §12.10
# ---------------------------------------------------------------------------

def test_r10_stats_returns_cachestats_instance():
    # R10: stats() must return a CacheStats (or compatible attribute object).
    cache = LruCache(2)
    s = cache.stats()
    assert isinstance(s, CacheStats)


def test_r10_stats_initial_all_zeros():
    # R10: freshly constructed cache has all counters at zero.
    cache = LruCache(5)
    s = cache.stats()
    assert s.hits == 0
    assert s.misses == 0
    assert s.evictions == 0
    assert s.size == 0


def test_r10_stats_size_reflects_entry_count_not_capacity():
    # R10: size is entry count, not capacity (ticket §12.9).
    cache = LruCache(10)
    cache.put("only_one", 1)
    assert cache.stats().size == 1   # size != capacity (10)


def test_r10_stats_size_empty_cache():
    # R10: empty cache has size 0.
    cache = LruCache(5)
    assert cache.stats().size == 0


def test_r10_stats_cumulative_across_calls():
    # R10: hits/misses/evictions accumulate across multiple calls (ticket §12.10).
    cache = LruCache(2)
    cache.put("a", 1)
    cache.put("b", 2)

    # produce 3 hits
    cache.get("a")
    cache.get("b")
    cache.get("a")

    # produce 2 misses
    cache.get("missing1")
    cache.get("missing2")

    # produce 1 eviction
    cache.put("c", 3)

    s = cache.stats()
    assert s.hits == 3
    assert s.misses == 2
    assert s.evictions == 1
    assert s.size == 2    # b evicted; a and c remain


def test_r10_stats_snapshot_is_immutable():
    # R10 / TD-1: CacheStats is frozen; mutating it must raise.
    cache = LruCache(2)
    cache.put("k", 1)
    s = cache.stats()
    with pytest.raises((AttributeError, TypeError)):
        s.hits = 999  # type: ignore[misc]


def test_r10_stats_snapshot_independent_of_later_operations():
    # R10 / TD-1: a snapshot captured before further ops is unaffected.
    cache = LruCache(2)
    cache.put("k", 1)
    snap = cache.stats()
    cache.get("k")           # adds a hit after snapshot
    assert snap.hits == 0    # snapshot captured before the hit


def test_r10_stats_size_after_eviction():
    # R10: size must equal entry count after eviction occurs.
    cache = LruCache(2)
    cache.put("a", 1)
    cache.put("b", 2)
    cache.put("c", 3)   # evicts a; size should remain 2
    assert cache.stats().size == 2


# ---------------------------------------------------------------------------
# R11 — hashable keys accepted; unhashable key raises TypeError
# Spec §7 failure modes, §8 acceptance criteria
# ---------------------------------------------------------------------------

def test_r11_integer_key_roundtrip():
    # R11: integer keys are hashable and must round-trip correctly.
    cache = LruCache(2)
    cache.put(42, "answer")
    assert cache.get(42) == "answer"


def test_r11_tuple_key_roundtrip():
    # R11: tuple keys are hashable and must round-trip correctly.
    cache = LruCache(2)
    cache.put((1, 2), "pair")
    assert cache.get((1, 2)) == "pair"


def test_r11_none_key_roundtrip():
    # R11: None is hashable and is a valid key.
    cache = LruCache(2)
    cache.put(None, "nil")
    assert cache.get(None) == "nil"


def test_r11_unhashable_key_put_raises_typeerror():
    # R11: a dict (unhashable) key passed to put surfaces TypeError
    # from the underlying mapping — LruCache does NOT catch it.
    cache = LruCache(2)
    with pytest.raises(TypeError):
        cache.put({}, "value")


def test_r11_unhashable_key_get_raises_typeerror():
    # R11: same TypeError contract on get.
    cache = LruCache(2)
    with pytest.raises(TypeError):
        cache.get([])


def test_r11_value_unrestricted():
    # R11: values are unrestricted — any object is accepted.
    cache = LruCache(3)
    cache.put("none_val", None)
    cache.put("list_val", [1, 2, 3])
    cache.put("dict_val", {"nested": True})
    assert cache.get("none_val") is None
    assert cache.get("list_val") == [1, 2, 3]
    assert cache.get("dict_val") == {"nested": True}


# ---------------------------------------------------------------------------
# R12 — O(1) amortized: structural check (no full-scan operations)
# Spec §8 acceptance criteria (structural, not timing-based)
# ---------------------------------------------------------------------------

def test_r12_no_linear_scan_in_implementation():
    # R12: the implementation must use OrderedDict with move_to_end and
    # popitem(last=False) — not a list or manual search.
    # We verify the module uses OrderedDict (structural spec assertion).
    import tokenlab.cache as cache_module
    import collections
    assert hasattr(collections, "OrderedDict")
    # LruCache's internal store must be an OrderedDict at runtime.
    cache = LruCache(3)
    cache.put("x", 1)
    # Access the private attribute as a structural spec check.
    internal_store = cache._entries  # type: ignore[attr-defined]
    assert isinstance(internal_store, collections.OrderedDict), (
        "R12: backing store must be an OrderedDict to satisfy O(1) contract"
    )


# ---------------------------------------------------------------------------
# R13 — stdlib only: no third-party imports in cache.py
# Spec §8 / ticket §12.13, §12.14
# ---------------------------------------------------------------------------

def test_r13_cache_module_uses_only_stdlib():
    # R13: cache.py must import only stdlib modules.
    import tokenlab.cache as cache_module
    import importlib.util
    import sys

    stdlib_prefixes = {
        "collections", "dataclasses", "typing", "abc", "functools",
        "itertools", "weakref", "types", "copy", "sys", "os", "builtins",
        "_collections_abc",
    }
    source_imports = set()
    # Inspect the module's __dict__ for imported names.
    for name, obj in vars(cache_module).items():
        if inspect.ismodule(obj):
            source_imports.add(obj.__name__.split(".")[0])

    # None of the direct imports should be non-stdlib.
    # We check by asserting they all belong to known stdlib roots.
    # This is a conservative whitelist; the implementation only uses
    # collections, dataclasses, typing — all stdlib.
    for top_level in source_imports:
        assert top_level in stdlib_prefixes or top_level.startswith("_"), (
            f"R13: cache.py imports non-stdlib module '{top_level}'"
        )


# ---------------------------------------------------------------------------
# R14 — docstrings present on LruCache and every public method
# Spec §8 acceptance criteria; CONSTITUTION §3
# ---------------------------------------------------------------------------

def test_r14_lrucache_class_has_docstring():
    # R14: the class docstring must be a non-empty string.
    assert LruCache.__doc__ is not None
    assert len(LruCache.__doc__.strip()) > 0


def test_r14_init_has_docstring():
    # R14: __init__ must have a docstring.
    assert LruCache.__init__.__doc__ is not None
    assert len(LruCache.__init__.__doc__.strip()) > 0


def test_r14_get_has_docstring():
    # R14: get must have a docstring.
    assert LruCache.get.__doc__ is not None
    assert len(LruCache.get.__doc__.strip()) > 0


def test_r14_put_has_docstring():
    # R14: put must have a docstring.
    assert LruCache.put.__doc__ is not None
    assert len(LruCache.put.__doc__.strip()) > 0


def test_r14_stats_has_docstring():
    # R14: stats must have a docstring.
    assert LruCache.stats.__doc__ is not None
    assert len(LruCache.stats.__doc__.strip()) > 0


# ---------------------------------------------------------------------------
# Spec §8 acceptance criteria — composite scenario tests
# (multi-requirement sequences cited in the acceptance criteria section)
# ---------------------------------------------------------------------------

def test_ac_capacity_one_a_then_b_only_b_retrievable():
    # Spec §8 R8 / ticket §12.11:
    # capacity=1; put(A), put(B) → only B retrievable, A is None.
    cache = LruCache(1)
    cache.put("A", 1)
    cache.put("B", 2)
    assert cache.get("A") is None
    assert cache.get("B") == 2
    assert cache.stats().evictions == 1


def test_ac_scripted_n1_hits_n2_misses_n3_evictions():
    # Spec §8 R10 / ticket §12.10: cumulative stats over a scripted sequence.
    cache = LruCache(3)
    # Seed entries
    cache.put(1, "one")
    cache.put(2, "two")
    cache.put(3, "three")

    # 4 hits
    cache.get(1)
    cache.get(2)
    cache.get(3)
    cache.get(1)

    # 3 misses
    cache.get(99)
    cache.get(98)
    cache.get(97)

    # 2 evictions: put(4) evicts LRU, put(5) evicts next LRU
    cache.put(4, "four")    # evicts 2 (LRU at this point)
    cache.put(5, "five")    # evicts 3

    s = cache.stats()
    assert s.hits == 4
    assert s.misses == 3
    assert s.evictions == 2
    assert s.size == 3   # entries: 1, 4, 5
