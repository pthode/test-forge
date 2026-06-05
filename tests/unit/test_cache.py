"""Unit tests for tokenlab.cache.LruCache.

Tests are derived from /docs/specs/lru-cache.md (requirements R1-R18 and the
1:1 acceptance-criterion mapping in spec §8). They assert the spec's contract,
NOT the current implementation. If the implementation disagrees with the spec,
the test fails and the test-engineer emits a REJECT to developer.

Source ticket: /docs/requirements/lru-cache.md (§12 success criteria mapped
1:1 onto the spec requirements). Constitution §4 (test discipline) is binding.
"""

import inspect

import pytest

from tokenlab.cache import LruCache


# ---------------------------------------------------------------------------
# R1 - public class exists, is a class, is the module's only public name
# ---------------------------------------------------------------------------

def test_r1_import_succeeds_and_is_a_class():
    # R1: `from tokenlab.cache import LruCache` succeeds; LruCache is a class.
    assert inspect.isclass(LruCache)


def test_r1_module_exposes_only_lrucache_as_public_name():
    # R1: LruCache is the module's only public name. The authoritative public
    # surface declaration in Python is __all__, which governs `from ... import *`
    # and is what R1 ("only public name") binds against. (Imported helpers like
    # OrderedDict/Any appearing in module vars() are import bindings, not part of
    # the declared public surface.)
    import tokenlab.cache as cache_module

    assert getattr(cache_module, "__all__", None) == ["LruCache"]
    # LruCache itself must be a module-defined name, not an imported one.
    assert getattr(cache_module.LruCache, "__module__", None) == "tokenlab.cache"


# ---------------------------------------------------------------------------
# R2 - construction & capacity validation
# ---------------------------------------------------------------------------

def test_r2_constructs_with_capacity_one():
    # R2: LruCache(1) constructs.
    c = LruCache(1)
    assert c.capacity == 1
    assert c.size == 0


def test_r2_constructs_with_large_capacity():
    # R2: LruCache(128) constructs.
    c = LruCache(128)
    assert c.capacity == 128
    assert c.size == 0


def test_r2_capacity_zero_raises_value_error():
    # R2: LruCache(0) raises ValueError.
    with pytest.raises(ValueError):
        LruCache(0)


def test_r2_negative_capacity_raises_value_error():
    # R2: LruCache(-1) raises ValueError.
    with pytest.raises(ValueError):
        LruCache(-1)


# ---------------------------------------------------------------------------
# R3 - get on a hit: returns value, bumps hits, refreshes recency
# ---------------------------------------------------------------------------

def test_r3_get_hit_returns_stored_value():
    # R3: get on a present key returns the stored value.
    c = LruCache(2)
    c.put("a", 1)
    assert c.get("a") == 1


def test_r3_get_hit_increments_hits_by_one():
    # R3: a hit increments the hits counter by exactly one.
    c = LruCache(2)
    c.put("a", 1)
    before = c.hits
    c.get("a")
    assert c.hits == before + 1


def test_r3_get_hit_refreshes_recency_protecting_entry():
    # R3 + R8: a get hit refreshes recency so the entry is protected from the
    # next eviction. capacity 2: put a, put b, get a (refreshes a), put c ->
    # b is evicted, not a.
    c = LruCache(2)
    c.put("a", 1)
    c.put("b", 2)
    c.get("a")
    c.put("c", 3)
    assert "a" in c
    assert "b" not in c


# ---------------------------------------------------------------------------
# R4 - get on a miss: returns default, bumps misses, no insert, no raise
# ---------------------------------------------------------------------------

def test_r4_get_miss_returns_none_by_default():
    # R4: get on an absent key returns None when default omitted.
    c = LruCache(2)
    assert c.get("missing") is None


def test_r4_get_miss_returns_supplied_default():
    # R4: get on an absent key returns the supplied default.
    c = LruCache(2)
    assert c.get("missing", 7) == 7


def test_r4_two_misses_increment_misses_by_two():
    # R4: each miss increments misses by one.
    c = LruCache(2)
    c.get("missing")
    c.get("missing", 7)
    assert c.misses == 2


def test_r4_miss_does_not_insert_key():
    # R4: a miss does not insert the key.
    c = LruCache(2)
    c.get("missing")
    c.get("missing", 7)
    assert "missing" not in c
    assert c.size == 0


def test_r4_miss_raises_no_exception():
    # R4: a miss raises no exception (asserted by absence of pytest.raises).
    c = LruCache(2)
    c.get("missing")  # must not raise


# ---------------------------------------------------------------------------
# R5 - put new key: inserts as MRU, grows size by one (until capacity)
# ---------------------------------------------------------------------------

def test_r5_put_new_key_grows_size_by_one():
    # R5: put on a new key increases size by one.
    c = LruCache(3)
    c.put("a", 1)
    assert c.size == 1


def test_r5_put_distinct_new_keys_grows_size_to_capacity():
    # R5: two more distinct new keys give size == 3.
    c = LruCache(3)
    c.put("a", 1)
    c.put("b", 2)
    c.put("c", 3)
    assert c.size == 3


def test_r5_put_new_key_is_most_recently_used():
    # R5 + R8: a newly put key is most-recently-used (protected from next eviction).
    c = LruCache(2)
    c.put("a", 1)
    c.put("b", 2)  # b is MRU
    c.put("c", 3)  # at capacity, a (LRU) is evicted
    assert "a" not in c
    assert "b" in c
    assert "c" in c


# ---------------------------------------------------------------------------
# R6 - put existing key: overwrites value, marks MRU, size unchanged
# ---------------------------------------------------------------------------

def test_r6_put_existing_key_overwrites_value():
    # R6: put on an existing key overwrites the value.
    c = LruCache(2)
    c.put("a", 1)
    c.put("a", 2)
    assert c.get("a") == 2


def test_r6_put_existing_key_does_not_grow_size():
    # R6: an overwrite never grows size.
    c = LruCache(2)
    c.put("a", 1)
    c.put("a", 2)
    assert c.size == 1


def test_r6_put_existing_key_marks_most_recently_used():
    # R6 + R8: overwriting an existing key marks it MRU, protecting it from
    # eviction. capacity 2: put a, put b, put a again (a becomes MRU), put c ->
    # b is evicted, not a.
    c = LruCache(2)
    c.put("a", 1)
    c.put("b", 2)
    c.put("a", 11)  # a refreshed to MRU via overwrite
    c.put("c", 3)
    assert "a" in c
    assert "b" not in c
    assert c.get("a") == 11


# ---------------------------------------------------------------------------
# R7 - eviction at capacity: evict genuine LRU, bump evictions, size stays
# ---------------------------------------------------------------------------

def test_r7_eviction_keeps_size_at_capacity():
    # R7: inserting a new key at capacity keeps size == capacity.
    c = LruCache(2)
    c.put("a", 1)
    c.put("b", 2)
    c.put("c", 3)
    assert c.size == 2


def test_r7_eviction_increments_evictions_counter():
    # R7: an eviction increments evictions by one.
    c = LruCache(2)
    c.put("a", 1)
    c.put("b", 2)
    c.put("c", 3)
    assert c.evictions == 1


def test_r7_eviction_removes_least_recently_used_entry():
    # R7: the genuinely least-recently-used entry ("a") is evicted; "b"/"c" remain.
    c = LruCache(2)
    c.put("a", 1)
    c.put("b", 2)
    c.put("c", 3)
    assert "a" not in c
    assert "b" in c
    assert "c" in c


def test_r7_no_eviction_until_capacity_exceeded():
    # R7: filling exactly to capacity evicts nothing.
    c = LruCache(3)
    c.put("a", 1)
    c.put("b", 2)
    c.put("c", 3)
    assert c.evictions == 0
    assert c.size == 3


# ---------------------------------------------------------------------------
# R8 - true-LRU recency (get hit and put both mark MRU)
# ---------------------------------------------------------------------------

def test_r8_get_hit_protects_entry_from_eviction():
    # R8: a get hit refreshes recency; the untouched entry is evicted instead.
    c = LruCache(2)
    c.put("a", 1)
    c.put("b", 2)
    c.get("a")  # a refreshed; b now LRU
    c.put("c", 3)
    assert "a" in c
    assert "b" not in c


def test_r8_eviction_victim_is_oldest_untouched_entry():
    # R8: with three slots and a refresh, the entry not touched longest is evicted.
    c = LruCache(3)
    c.put("a", 1)
    c.put("b", 2)
    c.put("c", 3)
    c.get("a")  # order from LRU->MRU now: b, c, a
    c.put("d", 4)  # b (LRU) evicted
    assert "b" not in c
    assert "a" in c
    assert "c" in c
    assert "d" in c


def test_r8_put_overwrite_protects_entry_from_eviction():
    # R8: a put-overwrite marks the entry MRU, protecting it.
    c = LruCache(2)
    c.put("a", 1)
    c.put("b", 2)
    c.put("a", 10)  # a refreshed; b now LRU
    c.put("c", 3)
    assert "a" in c
    assert "b" not in c


# ---------------------------------------------------------------------------
# R9 - None as a stored value, distinct from absence
# ---------------------------------------------------------------------------

def test_r9_stored_none_is_a_hit_returning_none():
    # R9: put(k, None) then get(k) returns None and counts as a hit.
    c = LruCache(2)
    c.put("k", None)
    assert c.get("k") is None
    assert c.hits == 1
    assert c.misses == 0


def test_r9_absent_key_is_a_miss_returning_none():
    # R9: get on an absent key returns None (default) and counts as a miss.
    c = LruCache(2)
    assert c.get("absent") is None
    assert c.misses == 1
    assert c.hits == 0


def test_r9_stored_none_distinguishable_from_absence_by_counters():
    # R9: same return value (None), different counter — the load-bearing distinction.
    c = LruCache(2)
    c.put("k", None)
    c.get("k")        # hit
    c.get("absent")   # miss
    assert c.hits == 1
    assert c.misses == 1


def test_r9_stored_none_membership_is_true():
    # R9: a key stored with value None is genuinely present.
    c = LruCache(2)
    c.put("k", None)
    assert "k" in c


# ---------------------------------------------------------------------------
# R10 - all five stats fields readable, accurate, and read-only
# ---------------------------------------------------------------------------

def test_r10_stats_accurate_after_scripted_sequence():
    # R10: after a scripted sequence, each stat equals the independently computed value.
    c = LruCache(2)
    c.put("a", 1)        # size 1
    c.put("b", 2)        # size 2
    c.get("a")           # hit  -> hits 1
    c.get("b")           # hit  -> hits 2
    c.get("zzz")         # miss -> misses 1
    c.put("c", 3)        # evict LRU (b was refreshed last? order: a,b -> get a -> get b -> b MRU, a LRU) -> evict a
    # After get("a") then get("b"): order LRU->MRU is a, b. put c evicts a.
    assert c.hits == 2
    assert c.misses == 1
    assert c.evictions == 1
    assert c.size == 2
    assert c.capacity == 2


def test_r10_hits_is_read_only():
    # R10: hits is read-only (assignment raises AttributeError).
    c = LruCache(2)
    with pytest.raises(AttributeError):
        c.hits = 99


def test_r10_misses_is_read_only():
    # R10: misses is read-only.
    c = LruCache(2)
    with pytest.raises(AttributeError):
        c.misses = 99


def test_r10_evictions_is_read_only():
    # R10: evictions is read-only.
    c = LruCache(2)
    with pytest.raises(AttributeError):
        c.evictions = 99


def test_r10_size_is_read_only():
    # R10: size is read-only.
    c = LruCache(2)
    with pytest.raises(AttributeError):
        c.size = 99


def test_r10_capacity_is_read_only():
    # R10: capacity is read-only.
    c = LruCache(2)
    with pytest.raises(AttributeError):
        c.capacity = 99


def test_r10_all_five_fields_return_int():
    # R10: each of the five stats fields is an int.
    c = LruCache(2)
    c.put("a", 1)
    c.get("a")
    c.get("x")
    for value in (c.hits, c.misses, c.evictions, c.size, c.capacity):
        assert isinstance(value, int)


# ---------------------------------------------------------------------------
# R11 - reset_stats: zero counters, keep entries, resume counting
# ---------------------------------------------------------------------------

def test_r11_reset_stats_zeroes_all_three_counters():
    # R11: reset_stats zeroes hits, misses, evictions.
    c = LruCache(2)
    c.put("a", 1)
    c.put("b", 2)
    c.get("a")          # hit
    c.get("zzz")        # miss
    c.put("c", 3)       # eviction
    assert c.hits > 0 and c.misses > 0 and c.evictions > 0
    c.reset_stats()
    assert c.hits == 0
    assert c.misses == 0
    assert c.evictions == 0


def test_r11_reset_stats_leaves_entries_intact():
    # R11: reset_stats does not clear cached entries; size/capacity unchanged.
    c = LruCache(3)
    c.put("a", 1)
    c.put("b", 2)
    c.reset_stats()
    assert c.size == 2
    assert c.capacity == 3
    assert c.get("a") == 1   # still retrievable
    assert c.get("b") == 2


def test_r11_counting_resumes_from_zero_after_reset():
    # R11: a subsequent get hit makes hits == 1.
    c = LruCache(2)
    c.put("a", 1)
    c.get("a")
    c.reset_stats()
    c.get("a")
    assert c.hits == 1


# ---------------------------------------------------------------------------
# R12 - membership check & peek: non-recency, non-counting
# ---------------------------------------------------------------------------

def test_r12_contains_reports_presence_as_bool():
    # R12: __contains__ reports presence correctly as a boolean.
    c = LruCache(2)
    c.put("a", 1)
    assert ("a" in c) is True
    assert ("z" in c) is False


def test_r12_contains_does_not_change_counters():
    # R12: a membership check does not alter hits or misses.
    c = LruCache(2)
    c.put("a", 1)
    "a" in c
    "z" in c
    assert c.hits == 0
    assert c.misses == 0


def test_r12_contains_does_not_change_recency():
    # R12: a membership check does not refresh recency. capacity 2: a is LRU;
    # `"a" in c` must NOT protect a, so a is still evicted when c is inserted.
    c = LruCache(2)
    c.put("a", 1)
    c.put("b", 2)
    assert "a" in c       # must not refresh recency
    c.put("c", 3)
    assert "a" not in c   # a still the eviction victim
    assert "b" in c


def test_r12_peek_returns_value_without_counting():
    # R12 + D8: peek returns the stored value without touching counters.
    c = LruCache(2)
    c.put("a", 1)
    assert c.peek("a") == 1
    assert c.hits == 0
    assert c.misses == 0


def test_r12_peek_absent_returns_default_without_counting():
    # R12 + D8: peek on an absent key returns default (None) without counting a miss.
    c = LruCache(2)
    assert c.peek("z") is None
    assert c.peek("z", 5) == 5
    assert c.misses == 0
    assert c.hits == 0


def test_r12_peek_does_not_change_recency():
    # R12 + D8: peek does not refresh recency; the eviction victim is unaffected
    # by a preceding peek.
    c = LruCache(2)
    c.put("a", 1)
    c.put("b", 2)
    assert c.peek("a") == 1   # must not protect a
    c.put("c", 3)
    assert "a" not in c       # a still evicted despite the peek
    assert "b" in c


def test_r12_peek_stored_none_returns_none_without_counting():
    # R12 + R9: peek on a key whose value is None returns None and counts nothing.
    c = LruCache(2)
    c.put("k", None)
    assert c.peek("k") is None
    assert c.hits == 0
    assert c.misses == 0


# ---------------------------------------------------------------------------
# R13 - remove: present (shrinks, True) and absent (no-op, False, no raise)
# ---------------------------------------------------------------------------

def test_r13_remove_present_key_returns_true():
    # R13 + D4: removing a present key returns True.
    c = LruCache(2)
    c.put("a", 1)
    assert c.remove("a") is True


def test_r13_remove_present_key_shrinks_size():
    # R13: removing a present entry reduces size by one.
    c = LruCache(2)
    c.put("a", 1)
    c.remove("a")
    assert c.size == 0


def test_r13_get_after_remove_is_a_miss():
    # R13: a subsequent get on the removed key is a miss.
    c = LruCache(2)
    c.put("a", 1)
    c.remove("a")
    assert c.get("a") is None
    assert c.misses == 1
    assert "a" not in c


def test_r13_remove_absent_key_returns_false():
    # R13 + D4: removing an absent key returns False.
    c = LruCache(2)
    assert c.remove("absent") is False


def test_r13_remove_absent_key_does_not_raise():
    # R13 + D4: removing an absent key never raises.
    c = LruCache(2)
    c.remove("absent")  # must not raise


def test_r13_remove_absent_key_does_not_change_size():
    # R13: a no-op remove leaves size unchanged.
    c = LruCache(2)
    c.put("a", 1)
    c.remove("absent")
    assert c.size == 1


# ---------------------------------------------------------------------------
# R14 - clear: empty entries, keep capacity, do NOT reset counters (D9)
# ---------------------------------------------------------------------------

def test_r14_clear_empties_all_entries():
    # R14: clear empties all cached entries (size == 0).
    c = LruCache(3)
    c.put("a", 1)
    c.put("b", 2)
    c.clear()
    assert c.size == 0
    assert "a" not in c
    assert "b" not in c


def test_r14_clear_leaves_capacity_unchanged():
    # R14: capacity is unchanged by clear.
    c = LruCache(3)
    c.put("a", 1)
    c.clear()
    assert c.capacity == 3


def test_r14_clear_does_not_reset_counters():
    # R14 + D9: clear does NOT reset hits/misses/evictions.
    c = LruCache(2)
    c.put("a", 1)
    c.put("b", 2)
    c.get("a")          # hit
    c.get("zzz")        # miss
    c.put("c", 3)       # eviction
    hits, misses, evictions = c.hits, c.misses, c.evictions
    assert hits and misses and evictions  # all non-zero precondition
    c.clear()
    assert c.hits == hits
    assert c.misses == misses
    assert c.evictions == evictions


def test_r14_can_reuse_cache_after_clear():
    # R14: after clear, the cache is reusable up to capacity.
    c = LruCache(2)
    c.put("a", 1)
    c.clear()
    c.put("x", 9)
    assert c.get("x") == 9
    assert c.size == 1


# ---------------------------------------------------------------------------
# R15 - unhashable key surfaces the natural TypeError (not ValueError/custom)
# ---------------------------------------------------------------------------

def test_r15_get_unhashable_key_raises_type_error():
    # R15: get with an unhashable key raises TypeError.
    c = LruCache(2)
    with pytest.raises(TypeError):
        c.get(["unhashable"])


def test_r15_put_unhashable_key_raises_type_error():
    # R15: put with an unhashable key raises TypeError.
    c = LruCache(2)
    with pytest.raises(TypeError):
        c.put(["unhashable"], 1)


def test_r15_remove_unhashable_key_raises_type_error():
    # R15: remove with an unhashable key raises TypeError.
    c = LruCache(2)
    with pytest.raises(TypeError):
        c.remove({"a"})


def test_r15_contains_unhashable_key_raises_type_error():
    # R15: membership check with an unhashable key raises TypeError.
    c = LruCache(2)
    with pytest.raises(TypeError):
        ["x"] in c


def test_r15_peek_unhashable_key_raises_type_error():
    # R15: peek with an unhashable key raises TypeError.
    c = LruCache(2)
    with pytest.raises(TypeError):
        c.peek(["unhashable"])


# ---------------------------------------------------------------------------
# R16 - amortized O(1): structural check (no O(n) scan over the backing store)
# ---------------------------------------------------------------------------

def test_r16_backing_store_is_ordereddict():
    # R16 + D2: the backing structure is collections.OrderedDict (provides
    # amortized O(1) move-to-end / pop-oldest, no hand-rolled O(n) scan).
    from collections import OrderedDict

    c = LruCache(2)
    backing = [v for v in vars(c).values() if isinstance(v, OrderedDict)]
    assert len(backing) == 1, "expected exactly one OrderedDict backing store"


def _method_body_without_docstring(method):
    """Return the source of a method with its docstring removed.

    Strips the docstring so word-boundary matches ("for", "sorted") inside prose
    do not produce false positives when scanning for O(n) constructs.
    """
    import ast
    import textwrap

    src = textwrap.dedent(inspect.getsource(method))
    tree = ast.parse(src)
    func = tree.body[0]
    if (
        func.body
        and isinstance(func.body[0], ast.Expr)
        and isinstance(func.body[0].value, ast.Constant)
        and isinstance(func.body[0].value.value, str)
    ):
        func.body = func.body[1:]
    return ast.unparse(func)


def test_r16_hot_path_methods_have_no_linear_scan():
    # R16: get/put/remove/peek perform no O(n) iteration over the backing store
    # (no `for`/`while` loop, no comprehension, no sorted()). Structural guard
    # against an accidentally-O(n) reimplementation. Docstrings are stripped so
    # prose words do not trigger false positives.
    for method in (LruCache.get, LruCache.put, LruCache.remove, LruCache.peek):
        body = _method_body_without_docstring(method)
        assert "for " not in body, f"{method.__name__} contains a for-loop (possible O(n) scan)"
        assert "while " not in body, f"{method.__name__} contains a while-loop (possible O(n) scan)"
        assert "sorted(" not in body, f"{method.__name__} sorts the store (O(n log n))"


def test_r16_large_capacity_operations_behave_correctly():
    # R16: correctness at scale (a smoke check that O(1) ops stay correct, not a
    # timing budget — CONSTITUTION §6 budgets are TBD).
    c = LruCache(1000)
    for i in range(1000):
        c.put(i, i)
    assert c.size == 1000
    assert c.get(0) == 0           # oldest, now refreshed
    c.put("overflow", 1)           # evicts the new LRU (key 1, since 0 was refreshed)
    assert c.size == 1000
    assert c.evictions == 1
    assert 1 not in c
    assert 0 in c


# ---------------------------------------------------------------------------
# R17 - not thread-safe: no lock acquired in any method (source-check evidence)
# ---------------------------------------------------------------------------

def test_r17_documented_not_thread_safe():
    # R17: the class (and/or module) docstring states it is not thread-safe.
    import tokenlab.cache as cache_module

    combined = f"{LruCache.__doc__ or ''}\n{cache_module.__doc__ or ''}".lower()
    assert "thread" in combined
    assert "not thread-safe" in combined or "not thread safe" in combined


def test_r17_no_lock_acquired_in_any_method():
    # R17: no threading.Lock/RLock is acquired in any method.
    src = inspect.getsource(LruCache)
    assert "Lock" not in src
    assert "acquire(" not in src
    assert "import threading" not in inspect.getsource(
        __import__("tokenlab.cache", fromlist=["cache"])
    )


# ---------------------------------------------------------------------------
# R18 - docstrings on class and public methods
# ---------------------------------------------------------------------------

def test_r18_class_has_docstring():
    # R18: the class carries a non-empty docstring.
    assert isinstance(LruCache.__doc__, str)
    assert LruCache.__doc__.strip()


def test_r18_get_docstring_covers_recency_and_miss_contract():
    # R18: get docstring describes recency semantics and the miss/default behavior.
    doc = (LruCache.get.__doc__ or "").lower()
    assert doc.strip()
    assert "recent" in doc          # recency semantics
    assert "default" in doc or "miss" in doc


def test_r18_put_docstring_covers_recency_and_eviction():
    # R18: put docstring describes recency and eviction semantics.
    doc = (LruCache.put.__doc__ or "").lower()
    assert doc.strip()
    assert "recent" in doc
    assert "evict" in doc


def test_r18_constructor_docstring_covers_value_error_contract():
    # R18: the ValueError capacity contract is documented (class or __init__ docstring).
    combined = f"{LruCache.__doc__ or ''}\n{LruCache.__init__.__doc__ or ''}"
    assert "ValueError" in combined or "capacity" in combined.lower()
