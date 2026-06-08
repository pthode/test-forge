"""Unit tests for tokenlab.cache.LruCache and CacheStats.

Tests are derived from /docs/specs/lru-cache.md requirements R1–R12 and the
1:1 acceptance criteria in spec §8.  They assert the spec's contract, NOT the
current implementation.  If the implementation disagrees with the spec, the
test fails and the test-engineer emits a REJECT to developer.

Requirement map:
  R1  — capacity validation (ValueError on capacity <= 0)
  R2  — successful construction, counters at 0
  R3  — get hit: value returned, key promoted to MRU, hits incremented
  R4  — get miss: default returned, misses incremented, stored entries unchanged
  R5  — put insert/update round-trip
  R6  — eviction on overflow, LRU ordering correctness
  R7  — put on existing key: value updated, MRU promoted, NO eviction
  R8  — stats property: CacheStats snapshot, frozen, correct size derivation
  R9  — counters start at 0, never decrement, no reset mechanism
  R10 — O(1) structural check: implementation uses OrderedDict with move_to_end
  R11 — hashable key types accepted; unhashable key raises TypeError
  R12 — CacheStats importable as a frozen dataclass from tokenlab.cache
"""

import dataclasses
import sys
from collections import OrderedDict

import pytest

from tokenlab.cache import CacheStats, LruCache


# ---------------------------------------------------------------------------
# R1: capacity validation
# ---------------------------------------------------------------------------


class TestCapacityValidation:
    """R1: Any capacity <= 0 must raise ValueError; instance must NOT be created."""

    def test_r1_zero_capacity_raises(self):
        # R1: capacity=0 is not positive
        with pytest.raises(ValueError, match="capacity must be a positive integer"):
            LruCache(capacity=0)

    def test_r1_negative_one_capacity_raises(self):
        # R1: capacity=-1 is not positive
        with pytest.raises(ValueError, match="capacity must be a positive integer"):
            LruCache(capacity=-1)

    def test_r1_large_negative_capacity_raises(self):
        # R1: any negative value raises ValueError
        with pytest.raises(ValueError):
            LruCache(capacity=-100)

    def test_r1_instance_not_created_on_zero(self):
        # R1: no partially-constructed instance leaks on ValueError
        result = None
        try:
            result = LruCache(capacity=0)
        except ValueError:
            pass
        assert result is None

    def test_r1_instance_not_created_on_negative(self):
        # R1: same for negative
        result = None
        try:
            result = LruCache(capacity=-5)
        except ValueError:
            pass
        assert result is None


# ---------------------------------------------------------------------------
# R2: successful construction, initial state
# ---------------------------------------------------------------------------


class TestConstruction:
    """R2: LruCache(capacity=N) for N >= 1 constructs; all counters start at 0."""

    @pytest.mark.parametrize("cap", [1, 2, 100])
    def test_r2_constructs_without_error(self, cap):
        # R2: capacity >= 1 never raises
        cache = LruCache(capacity=cap)
        assert cache is not None

    @pytest.mark.parametrize("cap", [1, 2, 100])
    def test_r2_initial_stats_all_zero(self, cap):
        # R2, R9: fresh instance has all counters at 0 and size 0
        cache = LruCache(capacity=cap)
        s = cache.stats
        assert s == CacheStats(hits=0, misses=0, evictions=0, size=0)

    def test_r2_initial_size_is_zero(self):
        # R2, R8: stats.size == 0 on fresh instance
        cache = LruCache(capacity=5)
        assert cache.stats.size == 0


# ---------------------------------------------------------------------------
# R3: get hit — value returned, hits incremented
# ---------------------------------------------------------------------------


class TestGetHit:
    """R3: get on a present key returns the value and increments hits by 1."""

    def test_r3_get_returns_stored_value(self):
        # R3
        cache = LruCache(capacity=3)
        cache.put("a", 42)
        assert cache.get("a") == 42

    def test_r3_get_increments_hits(self):
        # R3
        cache = LruCache(capacity=3)
        cache.put("x", "hello")
        cache.get("x")
        assert cache.stats.hits == 1

    def test_r3_multiple_hits_accumulate(self):
        # R3: hits are cumulative
        cache = LruCache(capacity=3)
        cache.put("k", 1)
        cache.get("k")
        cache.get("k")
        cache.get("k")
        assert cache.stats.hits == 3

    def test_r3_hit_does_not_increment_misses(self):
        # R3: a hit must not touch the miss counter
        cache = LruCache(capacity=3)
        cache.put("a", 1)
        cache.get("a")
        assert cache.stats.misses == 0

    def test_r3_get_hit_returns_value_not_none(self):
        # R3: even a stored None value is a hit
        cache = LruCache(capacity=2)
        cache.put("key", None)
        result = cache.get("key", default="sentinel")
        assert result is None
        assert cache.stats.hits == 1


# ---------------------------------------------------------------------------
# R4: get miss — default returned, misses incremented
# ---------------------------------------------------------------------------


class TestGetMiss:
    """R4: get on an absent key returns default, increments misses, leaves stored entries unchanged."""

    def test_r4_miss_returns_none_by_default(self):
        # R4
        cache = LruCache(capacity=3)
        assert cache.get("absent") is None

    def test_r4_miss_returns_supplied_default(self):
        # R4: caller-supplied default is returned verbatim
        cache = LruCache(capacity=3)
        assert cache.get("absent", "fallback") == "fallback"

    def test_r4_miss_on_empty_cache_returns_default(self):
        # R4
        cache = LruCache(capacity=1)
        assert cache.get("anything", 99) == 99

    def test_r4_miss_increments_misses(self):
        # R4
        cache = LruCache(capacity=3)
        cache.get("missing")
        assert cache.stats.misses == 1

    def test_r4_multiple_misses_accumulate(self):
        # R4
        cache = LruCache(capacity=3)
        cache.get("a")
        cache.get("b")
        cache.get("c")
        assert cache.stats.misses == 3

    def test_r4_miss_does_not_increment_hits(self):
        # R4: a miss must not touch the hit counter
        cache = LruCache(capacity=3)
        cache.get("no")
        assert cache.stats.hits == 0

    def test_r4_miss_does_not_alter_stored_entries(self):
        # R4: a miss on key "b" must not affect the stored value for key "a"
        cache = LruCache(capacity=3)
        cache.put("a", 7)
        cache.get("b")
        assert cache.get("a") == 7
        assert cache.stats.size == 1

    def test_r4_miss_does_not_store_key(self):
        # R4: a miss must not insert the queried key into the cache
        cache = LruCache(capacity=3)
        cache.get("ghost")
        assert cache.stats.size == 0


# ---------------------------------------------------------------------------
# R5: put insert and update round-trips
# ---------------------------------------------------------------------------


class TestPut:
    """R5: put inserts a new entry or updates an existing one; always returns None."""

    def test_r5_put_returns_none(self):
        # R5
        cache = LruCache(capacity=3)
        result = cache.put("k", 1)
        assert result is None

    def test_r5_put_then_get_returns_value(self):
        # R5
        cache = LruCache(capacity=3)
        cache.put("key", "value")
        assert cache.get("key") == "value"

    def test_r5_second_put_updates_value(self):
        # R5: update existing key
        cache = LruCache(capacity=3)
        cache.put("k", 1)
        cache.put("k", 2)
        assert cache.get("k") == 2

    def test_r5_put_various_value_types(self):
        # R5: any Python object is a valid value (R11)
        cache = LruCache(capacity=10)
        cache.put("list", [1, 2, 3])
        cache.put("dict", {"a": 1})
        cache.put("none", None)
        cache.put("int", 0)
        assert cache.get("list") == [1, 2, 3]
        assert cache.get("dict") == {"a": 1}
        assert cache.get("none") is None
        assert cache.get("int") == 0


# ---------------------------------------------------------------------------
# R6: eviction on overflow and LRU ordering correctness
# ---------------------------------------------------------------------------


class TestEviction:
    """R6: when a new key is put into a full cache, the LRU entry is evicted, evictions incremented."""

    def test_r6_eviction_increments_counter(self):
        # R6: capacity=2; inserting third key must evict and increment evictions
        cache = LruCache(capacity=2)
        cache.put("a", 1)
        cache.put("b", 2)
        cache.put("c", 3)
        assert cache.stats.evictions == 1

    def test_r6_size_stays_at_capacity_after_eviction(self):
        # R6: spec §8 acceptance — size == capacity after overflow
        cache = LruCache(capacity=2)
        cache.put("a", 1)
        cache.put("b", 2)
        cache.put("c", 3)
        assert cache.stats.size == 2

    def test_r6_lru_entry_evicted_not_recent_ones(self):
        # R6 (LRU correctness): after put("a"), put("b"), put("c"),
        # "a" (inserted first, never accessed again) must be evicted.
        cache = LruCache(capacity=2)
        cache.put("a", 1)
        cache.put("b", 2)
        cache.put("c", 3)
        # "a" should be gone
        assert cache.get("a") is None
        # "b" and "c" should survive
        assert cache.get("b") == 2
        assert cache.get("c") == 3

    def test_r6_get_promotes_key_away_from_lru_position(self):
        # R6 (LRU correctness): accessing "a" after "b" is inserted makes "b"
        # the LRU; the next overflow must evict "b", not "a".
        # spec §8: put("a",1); put("b",2); get("a"); put("c",3) evicts "b"
        cache = LruCache(capacity=2)
        cache.put("a", 1)
        cache.put("b", 2)
        cache.get("a")       # promotes "a" to MRU; "b" is now LRU
        cache.put("c", 3)    # should evict "b"
        assert cache.get("b") is None  # "b" was LRU and should be evicted
        assert cache.get("a") == 1     # "a" survives
        assert cache.get("c") == 3     # "c" was just inserted

    def test_r6_multiple_evictions_accumulate(self):
        # R6: each overflow triggers exactly one eviction
        cache = LruCache(capacity=1)
        cache.put("a", 1)
        cache.put("b", 2)
        cache.put("c", 3)
        assert cache.stats.evictions == 2

    def test_r6_evicted_entry_not_present(self):
        # R6: verifies the evicted key is absent (miss on get)
        cache = LruCache(capacity=1)
        cache.put("old", "x")
        cache.put("new", "y")
        assert cache.get("old") is None
        assert cache.get("new") == "y"

    def test_r6_new_key_itself_is_not_evicted(self):
        # R6 (D2 insert-then-trim): the newly inserted key must never be
        # its own eviction candidate — only the LRU entry is evicted.
        cache = LruCache(capacity=1)
        cache.put("existing", "old")
        cache.put("new_key", "new_value")
        assert cache.get("new_key") == "new_value"


# ---------------------------------------------------------------------------
# R7: put on existing key — no eviction, value updated, MRU promoted
# ---------------------------------------------------------------------------


class TestUpdateInPlace:
    """R7: updating an existing key must NOT evict, must NOT grow size, must promote to MRU."""

    def test_r7_update_does_not_evict(self):
        # R7
        cache = LruCache(capacity=2)
        cache.put("a", 1)
        cache.put("b", 2)
        cache.put("a", 99)   # update, not insert
        assert cache.stats.evictions == 0

    def test_r7_update_does_not_grow_size(self):
        # R7
        cache = LruCache(capacity=2)
        cache.put("a", 1)
        cache.put("b", 2)
        cache.put("a", 99)
        assert cache.stats.size == 2

    def test_r7_update_stores_new_value(self):
        # R7
        cache = LruCache(capacity=2)
        cache.put("a", 1)
        cache.put("a", 42)
        assert cache.get("a") == 42

    def test_r7_update_promotes_key_to_mru(self):
        # R7: after updating "a" at capacity=2 with "b" present,
        # a third put should evict "b" (LRU), not "a" (MRU after update).
        # spec §8 acceptance for R7: put("a",1); put("b",2); put("a",9)
        # leaves size==2, evictions==0, get("a")==9.
        cache = LruCache(capacity=2)
        cache.put("a", 1)
        cache.put("b", 2)
        cache.put("a", 9)    # update + promote "a" to MRU
        assert cache.stats.size == 2
        assert cache.stats.evictions == 0
        assert cache.get("a") == 9
        # "b" should still be present (only 2 entries, no eviction)
        assert cache.get("b") == 2

    def test_r7_update_then_overflow_evicts_other_key(self):
        # R7 MRU promotion: after updating "a", overflow should evict "b" (LRU)
        cache = LruCache(capacity=2)
        cache.put("a", 1)
        cache.put("b", 2)
        cache.put("a", 99)   # update — "a" is MRU, "b" is LRU
        cache.put("c", 3)    # overflow — must evict "b"
        assert cache.stats.evictions == 1
        assert cache.get("b") is None
        assert cache.get("a") == 99
        assert cache.get("c") == 3


# ---------------------------------------------------------------------------
# R8: stats property — snapshot, frozen, correct fields
# ---------------------------------------------------------------------------


class TestStats:
    """R8: stats returns a fresh frozen CacheStats snapshot with correct integer fields."""

    def test_r8_stats_returns_cachestats_instance(self):
        # R8
        cache = LruCache(capacity=3)
        assert isinstance(cache.stats, CacheStats)

    def test_r8_stats_fields_are_integers(self):
        # R8
        cache = LruCache(capacity=3)
        cache.put("a", 1)
        cache.get("a")
        s = cache.stats
        assert isinstance(s.hits, int)
        assert isinstance(s.misses, int)
        assert isinstance(s.evictions, int)
        assert isinstance(s.size, int)

    def test_r8_stats_size_equals_entry_count(self):
        # R8: size reflects the live count, not a historical max
        cache = LruCache(capacity=5)
        assert cache.stats.size == 0
        cache.put("a", 1)
        assert cache.stats.size == 1
        cache.put("b", 2)
        assert cache.stats.size == 2

    def test_r8_stats_is_snapshot_not_live_view(self):
        # R8: a captured snapshot must NOT change when subsequent ops run
        cache = LruCache(capacity=3)
        cache.put("a", 1)
        snapshot = cache.stats
        cache.put("b", 2)
        cache.get("a")
        # snapshot must be unchanged
        assert snapshot.size == 1
        assert snapshot.hits == 0

    def test_r8_frozen_dataclass_raises_on_mutation(self):
        # R8: CacheStats is frozen — assignment must raise FrozenInstanceError
        cache = LruCache(capacity=3)
        s = cache.stats
        with pytest.raises(dataclasses.FrozenInstanceError):
            s.hits = 999  # type: ignore[misc]

    def test_r8_size_bounded_by_capacity(self):
        # R8: 0 <= size <= capacity
        cache = LruCache(capacity=2)
        for i in range(10):
            cache.put(i, i)
        assert 0 <= cache.stats.size <= 2


# ---------------------------------------------------------------------------
# R9: counters start at 0, only increase, no reset
# ---------------------------------------------------------------------------


class TestCounterMonotonicity:
    """R9: counters start at 0, never decrement, no public reset API exists."""

    def test_r9_all_counters_start_at_zero(self):
        # R9
        cache = LruCache(capacity=5)
        s = cache.stats
        assert s.hits == 0
        assert s.misses == 0
        assert s.evictions == 0

    def test_r9_counters_only_increase(self):
        # R9: iterate through ops and verify each counter is non-decreasing
        cache = LruCache(capacity=2)
        prev_hits, prev_misses, prev_evictions = 0, 0, 0
        ops = [
            lambda: cache.put("a", 1),
            lambda: cache.put("b", 2),
            lambda: cache.get("a"),
            lambda: cache.get("missing"),
            lambda: cache.put("c", 3),
            lambda: cache.get("a"),
        ]
        for op in ops:
            op()
            s = cache.stats
            assert s.hits >= prev_hits
            assert s.misses >= prev_misses
            assert s.evictions >= prev_evictions
            prev_hits, prev_misses, prev_evictions = s.hits, s.misses, s.evictions

    def test_r9_no_reset_stats_method(self):
        # R9: no reset mechanism must exist on the public surface
        cache = LruCache(capacity=3)
        assert not hasattr(cache, "reset_stats")
        assert not hasattr(cache, "clear_stats")
        assert not hasattr(cache, "reset")

    def test_r9_stats_field_hits_never_decrements(self):
        # R9: once hits is > 0 it can only grow
        cache = LruCache(capacity=3)
        cache.put("a", 1)
        cache.get("a")
        hits_after_one = cache.stats.hits
        cache.get("missing")
        assert cache.stats.hits >= hits_after_one


# ---------------------------------------------------------------------------
# R10: O(1) structural check — implementation uses OrderedDict
# ---------------------------------------------------------------------------


class TestStructuralO1:
    """R10: O(1) is structural; verify the implementation uses OrderedDict with
    move_to_end / popitem(last=False) rather than timing tests (which are flaky)."""

    def test_r10_internal_store_is_ordered_dict(self):
        # R10: the internal store must be an OrderedDict to guarantee O(1)
        cache = LruCache(capacity=5)
        cache.put("a", 1)
        assert isinstance(cache._store, OrderedDict)

    def test_r10_get_hit_calls_move_to_end(self):
        # R10: after a get hit, the key must be at the MRU end of the OrderedDict
        cache = LruCache(capacity=3)
        cache.put("a", 1)
        cache.put("b", 2)
        cache.put("c", 3)
        cache.get("a")  # "a" was LRU; after get it must be MRU
        # The last key in the OrderedDict is MRU
        last_key = next(reversed(cache._store))
        assert last_key == "a"

    def test_r10_new_put_at_end(self):
        # R10 (D2): a newly inserted key is placed at the MRU (end) position
        cache = LruCache(capacity=3)
        cache.put("x", 1)
        cache.put("y", 2)
        last_key = next(reversed(cache._store))
        assert last_key == "y"

    def test_r10_lru_is_first_in_ordered_dict(self):
        # R10: the first key in the OrderedDict must be the LRU candidate
        cache = LruCache(capacity=3)
        cache.put("a", 1)
        cache.put("b", 2)
        cache.put("c", 3)
        first_key = next(iter(cache._store))
        assert first_key == "a"


# ---------------------------------------------------------------------------
# R11: key types — hashable accepted, unhashable raises TypeError
# ---------------------------------------------------------------------------


class TestKeyTypes:
    """R11: any hashable key works; unhashable keys raise TypeError (not caught)."""

    def test_r11_string_key(self):
        # R11
        cache = LruCache(capacity=3)
        cache.put("hello", 1)
        assert cache.get("hello") == 1

    def test_r11_integer_key(self):
        # R11
        cache = LruCache(capacity=3)
        cache.put(42, "forty-two")
        assert cache.get(42) == "forty-two"

    def test_r11_tuple_key(self):
        # R11: tuples are hashable
        cache = LruCache(capacity=3)
        cache.put((1, 2), "pair")
        assert cache.get((1, 2)) == "pair"

    def test_r11_frozenset_key(self):
        # R11: frozensets are hashable
        cache = LruCache(capacity=3)
        cache.put(frozenset({1, 2, 3}), "frozen")
        assert cache.get(frozenset({1, 2, 3})) == "frozen"

    def test_r11_none_key(self):
        # R11: None is hashable
        cache = LruCache(capacity=3)
        cache.put(None, "null_value")
        assert cache.get(None) == "null_value"

    def test_r11_unhashable_key_put_raises_typeerror(self):
        # R11: list keys are unhashable; TypeError must propagate, NOT be swallowed
        cache = LruCache(capacity=3)
        with pytest.raises(TypeError):
            cache.put([1, 2, 3], "value")

    def test_r11_unhashable_key_get_raises_typeerror(self):
        # R11: same for get
        cache = LruCache(capacity=3)
        with pytest.raises(TypeError):
            cache.get([1, 2, 3])

    def test_r11_unhashable_key_does_not_increment_misses(self):
        # R11: TypeError is a caller error; misses must NOT be incremented
        cache = LruCache(capacity=3)
        try:
            cache.get(["bad_key"])
        except TypeError:
            pass
        assert cache.stats.misses == 0


# ---------------------------------------------------------------------------
# R12: CacheStats importability and frozen-dataclass contract
# ---------------------------------------------------------------------------


class TestCacheStatsContract:
    """R12: CacheStats is importable from tokenlab.cache and is a frozen dataclass."""

    def test_r12_cachestats_importable(self):
        # R12: import must not fail (covered by module-level import above)
        import tokenlab.cache as mod  # noqa: F401 — explicit re-import check
        assert hasattr(mod, "CacheStats")
        assert hasattr(mod, "LruCache")

    def test_r12_cachestats_is_dataclass(self):
        # R12
        assert dataclasses.is_dataclass(CacheStats)

    def test_r12_cachestats_is_frozen(self):
        # R12: frozen=True — a frozen dataclass raises FrozenInstanceError on
        # normal attribute assignment.  object.__setattr__ bypasses the guard
        # on some Python versions, so we use a direct attribute write instead.
        s = CacheStats(hits=1, misses=2, evictions=3, size=4)
        with pytest.raises(dataclasses.FrozenInstanceError):
            s.hits = 0  # type: ignore[misc]

    def test_r12_cachestats_has_required_fields(self):
        # R12
        field_names = {f.name for f in dataclasses.fields(CacheStats)}
        assert field_names == {"hits", "misses", "evictions", "size"}

    def test_r12_cachestats_fields_are_int_annotated(self):
        # R12: all four fields carry an int annotation
        for f in dataclasses.fields(CacheStats):
            assert f.type is int or f.type == "int", (
                f"Field '{f.name}' expected int annotation, got {f.type!r}"
            )

    def test_r12_cachestats_value_semantics(self):
        # R12: two CacheStats with equal fields compare equal (dataclass __eq__)
        s1 = CacheStats(hits=1, misses=2, evictions=3, size=4)
        s2 = CacheStats(hits=1, misses=2, evictions=3, size=4)
        assert s1 == s2


# ---------------------------------------------------------------------------
# §12 Success-criteria tests (ticket §12.1–§12.10)
# Additional tests that map directly to the requirements ticket success criteria
# to ensure every bullet is exercised.
# ---------------------------------------------------------------------------


class TestSuccessCriteria:
    """Ticket §12 success criteria — each bullet numbered SC-N."""

    def test_sc1_capacity_zero_raises(self):
        # SC-1: LruCache(capacity=0) raises ValueError
        with pytest.raises(ValueError):
            LruCache(capacity=0)

    def test_sc1_capacity_negative_raises(self):
        # SC-1: negative capacity raises ValueError
        with pytest.raises(ValueError):
            LruCache(capacity=-1)

    def test_sc2_capacity_1_constructs(self):
        # SC-2
        assert LruCache(capacity=1) is not None

    def test_sc3_get_miss_increments_misses_and_returns_default(self):
        # SC-3
        cache = LruCache(capacity=3)
        result = cache.get("k", "default_val")
        assert result == "default_val"
        assert cache.stats.misses == 1

    def test_sc3_get_miss_none_when_default_not_supplied(self):
        # SC-3
        cache = LruCache(capacity=3)
        assert cache.get("k") is None
        assert cache.stats.misses == 1

    def test_sc4_put_then_get_returns_value_and_increments_hits(self):
        # SC-4
        cache = LruCache(capacity=3)
        cache.put("x", 55)
        result = cache.get("x")
        assert result == 55
        assert cache.stats.hits == 1

    def test_sc5_n_plus_1_inserts_size_n_evictions_1(self):
        # SC-5: N=2; put 3 entries; size==2, evictions==1
        cache = LruCache(capacity=2)
        cache.put("a", 1)
        cache.put("b", 2)
        cache.put("c", 3)
        s = cache.stats
        assert s.size == 2
        assert s.evictions == 1

    def test_sc6_accessed_key_not_evicted(self):
        # SC-6: key accessed before subsequent puts is NOT the evicted one
        cache = LruCache(capacity=2)
        cache.put("a", 1)
        cache.put("b", 2)
        cache.get("a")           # access "a" — it's now MRU
        cache.put("c", 3)        # overflow — must evict "b", not "a"
        assert cache.get("a") == 1   # "a" survived
        assert cache.get("b") is None  # "b" was evicted

    def test_sc7_update_key_no_eviction(self):
        # SC-7: capacity=2; put("a",1); put("b",2); put("a",9);
        # evictions==0, size==2, get("a")==9
        cache = LruCache(capacity=2)
        cache.put("a", 1)
        cache.put("b", 2)
        cache.put("a", 9)
        assert cache.stats.evictions == 0
        assert cache.stats.size == 2
        assert cache.get("a") == 9

    def test_sc8_stats_is_cachestats_instance_with_int_fields(self):
        # SC-8
        cache = LruCache(capacity=3)
        cache.put("a", 1)
        s = cache.stats
        assert isinstance(s, CacheStats)
        assert isinstance(s.hits, int)
        assert isinstance(s.misses, int)
        assert isinstance(s.evictions, int)
        assert isinstance(s.size, int)

    def test_sc8_size_equals_current_entry_count(self):
        # SC-8
        cache = LruCache(capacity=5)
        cache.put("a", 1)
        cache.put("b", 2)
        assert cache.stats.size == 2

    def test_sc9_counters_start_at_zero(self):
        # SC-9
        cache = LruCache(capacity=5)
        s = cache.stats
        assert s.hits == 0
        assert s.misses == 0
        assert s.evictions == 0

    def test_sc10_structural_ordered_dict(self):
        # SC-10: structural O(1) check via OrderedDict presence
        cache = LruCache(capacity=3)
        assert isinstance(cache._store, OrderedDict)
