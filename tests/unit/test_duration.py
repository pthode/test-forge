"""Unit tests for tokenlab.duration.parse_duration.

Tests are derived from /docs/specs/parse-duration.md (requirements R1-R11 and
the 1:1 acceptance criteria in spec §8). They assert the spec's contract, NOT
the current implementation. If the implementation disagrees with the spec, the
test fails and the test-engineer emits a REJECT to developer.
"""

import inspect

import pytest

from tokenlab.duration import parse_duration


# ---------------------------------------------------------------------------
# R1 - public function exists, is callable, is the module's only public name
# ---------------------------------------------------------------------------

def test_r1_import_and_callable():
    # R1: importing parse_duration succeeds and it is callable.
    assert callable(parse_duration)


def test_r1_signature_takes_single_str_arg():
    # R1/R2: signature is parse_duration(s) -> int (one positional parameter).
    sig = inspect.signature(parse_duration)
    params = list(sig.parameters.values())
    assert len(params) == 1


def test_r1_only_public_name_is_parse_duration():
    # R1: the module's only public name is parse_duration.
    import tokenlab.duration as mod

    public = [name for name in vars(mod) if not name.startswith("_")]
    # Module-level imports (e.g. `re`) are not "public names" of the API in the
    # spec's sense, but the spec is explicit that parse_duration is the only
    # public *name*. Anything else exposed without an underscore is a finding.
    public_non_imports = [
        name
        for name in public
        if not inspect.ismodule(getattr(mod, name))
    ]
    assert public_non_imports == ["parse_duration"]


# ---------------------------------------------------------------------------
# R2 - valid input returns non-negative int = hours*3600 + minutes*60 + seconds
# ---------------------------------------------------------------------------

def test_r2_combined_value_is_correct():
    # R2/§8: parse_duration("2h15m30s") == 8130.
    assert parse_duration("2h15m30s") == 8130


def test_r2_return_type_is_int_not_bool():
    result = parse_duration("2h15m30s")
    assert isinstance(result, int)
    # bool is a subclass of int; the spec says "Python int". Guard against a
    # degenerate bool result for completeness.
    assert not isinstance(result, bool)


def test_r2_return_value_non_negative():
    assert parse_duration("2h15m30s") >= 0


# ---------------------------------------------------------------------------
# R3 - supported suffixes are exactly lowercase h/m/s; anything else invalid
# ---------------------------------------------------------------------------

def test_r3_seconds_only_valid():
    # R3/§8: parse_duration("45s") == 45.
    assert parse_duration("45s") == 45


@pytest.mark.parametrize("bad", ["1H", "30M", "1S", "1x", "1d", "1w", "1y"])
def test_r3_unknown_or_uppercase_suffix_raises(bad):
    # R3/§8: uppercase suffixes and unknown units are invalid.
    with pytest.raises(ValueError):
        parse_duration(bad)


# ---------------------------------------------------------------------------
# R4 - components concatenated, each unit at most once, strict descending order
# ---------------------------------------------------------------------------

def test_r4_two_components_valid():
    # R4/§8: parse_duration("1h30m") == 5400.
    assert parse_duration("1h30m") == 5400


def test_r4_out_of_order_raises():
    # R4/§8: parse_duration("30m1h") raises ValueError.
    with pytest.raises(ValueError):
        parse_duration("30m1h")


def test_r4_repeated_unit_raises():
    # R4/§8: parse_duration("1h1h") raises ValueError.
    with pytest.raises(ValueError):
        parse_duration("1h1h")


@pytest.mark.parametrize("bad", ["1s1m", "30s1h", "2m1h", "5s5s", "1m1m"])
def test_r4_additional_order_and_repeat_violations_raise(bad):
    with pytest.raises(ValueError):
        parse_duration(bad)


# ---------------------------------------------------------------------------
# R5 - each integer is non-negative base-10, no sign, no decimal; leading zeros OK
# ---------------------------------------------------------------------------

def test_r5_negative_sign_raises():
    # R5/§8: parse_duration("-1h") raises ValueError.
    with pytest.raises(ValueError):
        parse_duration("-1h")


def test_r5_decimal_component_raises():
    # R5/§8: parse_duration("1.5h") raises ValueError.
    with pytest.raises(ValueError):
        parse_duration("1.5h")


def test_r5_leading_zeros_accepted():
    # R5/§8: parse_duration("01h") == 3600.
    assert parse_duration("01h") == 3600


@pytest.mark.parametrize("bad", ["+1h", "1,5h", "1e3s"])
def test_r5_other_non_integer_forms_raise(bad):
    with pytest.raises(ValueError):
        parse_duration(bad)


# ---------------------------------------------------------------------------
# R6 - outer whitespace trimmed; inter-component whitespace invalid; empty invalid
# ---------------------------------------------------------------------------

def test_r6_outer_whitespace_trimmed():
    # R6/§8: parse_duration("  1h  ") == 3600.
    assert parse_duration("  1h  ") == 3600


def test_r6_inter_component_whitespace_raises():
    # R6/§8: parse_duration("1h 30m") raises ValueError.
    with pytest.raises(ValueError):
        parse_duration("1h 30m")


def test_r6_empty_string_raises():
    # R6/§8: parse_duration("") raises ValueError.
    with pytest.raises(ValueError):
        parse_duration("")


def test_r6_whitespace_only_raises():
    # R6/§8: parse_duration("   ") raises ValueError.
    with pytest.raises(ValueError):
        parse_duration("   ")


@pytest.mark.parametrize("bad", ["\t", "\n", "1h\t30m", "1 h", "1h 30m 15s"])
def test_r6_additional_whitespace_violations_raise(bad):
    with pytest.raises(ValueError):
        parse_duration(bad)


# ---------------------------------------------------------------------------
# R7 - zero allowed; no per-component cap; no clock-range validation
# ---------------------------------------------------------------------------

def test_r7_zero_seconds():
    # R7/§8: parse_duration("0s") == 0.
    assert parse_duration("0s") == 0


def test_r7_uncapped_minutes():
    # R7/§8: parse_duration("90m") == 5400 (no clock-range validation).
    assert parse_duration("90m") == 5400


def test_r7_uncapped_hours_large():
    # R7: components carry no upper cap.
    assert parse_duration("100h") == 360000


def test_r7_zero_components_combined():
    assert parse_duration("0h0m0s") == 0


# ---------------------------------------------------------------------------
# R8 - every invalid input raises exactly ValueError; function is total over str
# ---------------------------------------------------------------------------

_INVALID_INPUTS = [
    "",            # empty
    "   ",         # whitespace-only
    "90",          # bare integer
    "1",           # bare integer
    "1H",          # uppercase suffix
    "30M",         # uppercase suffix
    "1x",          # unknown suffix
    "1d",          # day unit out of scope
    "-1h",         # negative sign
    "30m1h",       # out of order
    "1h1h",        # repeated unit
    "1.5h",        # decimal
    "1h 30m",      # inter-component whitespace
    "abc",         # garbage
    "h",           # unit with no integer
    "PT1H30M",     # ISO-8601 syntax
    "1mo",         # multi-char unit
    "1h2x",        # trailing unknown unit
    "s",           # bare unit
]


@pytest.mark.parametrize("bad", _INVALID_INPUTS)
def test_r8_invalid_inputs_raise_exactly_valueerror(bad):
    # R8/§8: the raised type is exactly ValueError, not a subclass and not
    # another exception type. No malformed str leaks IndexError/AttributeError/
    # TypeError.
    with pytest.raises(ValueError) as exc_info:
        parse_duration(bad)
    assert type(exc_info.value) is ValueError


@pytest.mark.parametrize("bad", _INVALID_INPUTS)
def test_r8_no_other_exception_type_leaks(bad):
    # R8: totality - for any str the function returns a non-negative int or
    # raises ValueError; it must not leak any other exception type.
    try:
        result = parse_duration(bad)
    except ValueError:
        pass  # the only permitted failure
    except Exception as exc:  # noqa: BLE001 - intentionally catching to assert
        pytest.fail(
            f"parse_duration({bad!r}) leaked {type(exc).__name__}, "
            "spec R8 permits only ValueError"
        )
    else:
        # If it did not raise, it must be a non-negative int (also R8/R2).
        assert isinstance(result, int) and result >= 0


# ---------------------------------------------------------------------------
# R9 - ValueError message is a non-empty string for a representative input
# ---------------------------------------------------------------------------

def test_r9_error_message_non_empty():
    # R9/§8: the ValueError for an invalid input carries a non-empty message.
    with pytest.raises(ValueError) as exc_info:
        parse_duration("90")
    assert str(exc_info.value)  # non-empty; exact wording not asserted


# ---------------------------------------------------------------------------
# R10 - no eval/exec in the implementation source
# ---------------------------------------------------------------------------

def test_r10_no_eval_or_exec_in_source():
    # R10/§8: parsing uses re or manual scanning only; no dynamic code exec.
    import tokenlab.duration as mod

    source = inspect.getsource(mod)
    assert "eval(" not in source
    assert "exec(" not in source


# ---------------------------------------------------------------------------
# R11 - docstring describes purpose, grammar, return value, ValueError contract
# ---------------------------------------------------------------------------

def test_r11_docstring_non_empty():
    # R11/§8: parse_duration.__doc__ is a non-empty string.
    assert isinstance(parse_duration.__doc__, str)
    assert parse_duration.__doc__.strip()
