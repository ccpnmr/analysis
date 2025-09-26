"""
Module Documentation here
"""
from __future__ import annotations


#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (https://www.ccpn.ac.uk) 2014 - 2025"
__credits__ = ("Ed Brooksbank, Morgan Hayward, Victoria A Higman, Luca Mureddu, Eliza Płoskoń",
               "Timothy J Ragan, Brian O Smith, Daniel Thompson",
               "Gary S Thompson & Geerten W Vuister")
__licence__ = ("CCPN licence. See https://ccpn.ac.uk/software/licensing/")
__reference__ = ("Skinner, S.P., Fogh, R.H., Boucher, W., Ragan, T.J., Mureddu, L.G., & Vuister, G.W.",
                 "CcpNmr AnalysisAssign: a flexible platform for integrated NMR analysis",
                 "J.Biomol.Nmr (2016), 66, 111-124, https://doi.org/10.1007/s10858-016-0060-y")
#=========================================================================================
# Last code modification
#=========================================================================================
__modifiedBy__ = "$modifiedBy: Ed Brooksbank $"
__dateModified__ = "$dateModified: 2025-09-08 16:30:35 +0100 (Mon, September 08, 2025) $"
__version__ = "$Revision: 3.3.2.3 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: Ed Brooksbank $"
__date__ = "$Date: 2025-09-08 12:54:51 +0100 (Mon, September 08, 2025) $"
#=========================================================================================
# Start of code
#=========================================================================================

__all__ = ['deep_equal']

from collections.abc import Mapping, Sequence
from dataclasses import is_dataclass, asdict, dataclass
from datetime import datetime, timezone, timedelta
from numbers import Number
import math
import numpy as np
import pandas as pd
import pandas.testing as pdt


def _shallow_equal(a, b, **_):
    """
    Checks if two objects are equal, handling Python primitives and NumPy/Pandas arrays.
    There is a more comprehension deep_equal in CHeckEqual.
    """
    # first check that match
    if type(a) != type(b):
        return False
    elif isinstance(a, (np.ndarray, np.generic)):
        # For arrays, use np.array_equal to check for equivalence
        return np.array_equal(a, b)
    elif isinstance(a, (pd.Series, pd.DataFrame)):
        return a.equals(b)
    else:
        # For standard Python objects, the simple '==' works
        return a == b


def deep_equal(
        a, b,
        *,
        # Numeric tolerance (exact if both are 0.0)
        rtol: float = 0.0,
        atol: float = 0.0,
        # Treat NaN/NA as equal when they appear in the same position
        equal_nan: bool = True,
        # Also treat None as NA for the purpose of equal_nan
        none_equals_nan: bool = True,
        # Require the *same* concrete type? (e.g. int vs np.int64)
        strict_type: bool = False,
        # pandas options
        pandas_check_dtype: bool = True,
        pandas_check_names: bool = True,
        # If True, compare DataFrames/Series after sorting indexes (and columns for DF)
        pandas_align_index: bool = True,
        pandas_align_columns: bool = True,
        # For DataFrames only: ignore column order (True => order-agnostic)
        pandas_check_like: bool = True,
        # Container options
        sequence_unordered: bool = False,  # treat sequences as multisets (order-insensitive)
        # Datetime options
        normalize_tz: bool = True,  # compare aware datetimes in UTC
        ) -> bool:
    """
    Deep equality with rich handling for Python primitives, NumPy, pandas, and nested containers.

    Highlights
    ----------
    - Numbers: exact or tolerant (rtol/atol), with optional NaN equivalence.
    - NumPy: arrays, scalars, dtypes (object arrays recurse elementwise; numeric uses isclose).
    - pandas: Series/DataFrame/Index via pandas.testing (supports tolerance, NA, dtype/name checks).
    - Containers: dicts, lists/tuples (ordered or order-agnostic), sets/frozensets.
    - Dataclasses: compared by fields.
    - Datetime: optional timezone normalization to UTC.

    Returns
    -------
    bool
    """
    # Fast path: identical object
    if a is b:
        return True

    # Optional strict type gate
    if strict_type and (type(a) is not type(b)):
        return False

    # If both are NA-like and equal_nan permitted
    if equal_nan and _is_na(a, none_equals_nan) and _is_na(b, none_equals_nan):
        return True

    # Datetime handling (aware vs naive); dates & times compare directly
    if isinstance(a, datetime) and isinstance(b, datetime):
        if normalize_tz:
            def norm(dt):
                if dt.tzinfo is not None:
                    return dt.astimezone(timezone.utc).replace(tzinfo=timezone.utc)
                return dt

            return norm(a) == norm(b)
        return a == b

    # Create a kwargs dict for cleaner recursive calls
    kwargs = dict(rtol=rtol, atol=atol, equal_nan=equal_nan, none_equals_nan=none_equals_nan,
                  strict_type=strict_type,
                  # pandas parameters
                  pandas_check_dtype=pandas_check_dtype, pandas_check_names=pandas_check_names,
                  pandas_align_index=pandas_align_index, pandas_align_columns=pandas_align_columns,
                  pandas_check_like=pandas_check_like,
                  sequence_unordered=sequence_unordered, normalize_tz=normalize_tz)

    # Numbers: handle with (possibly) tolerance and NaN rules
    if _is_number(a) and _is_number(b):
        return _num_equal(a, b, **kwargs)

    # Bytes-like quick path
    if isinstance(a, (bytes, bytearray, memoryview)) and isinstance(b, (bytes, bytearray, memoryview)):
        return bytes(a) == bytes(b)

    # Dataclasses: compare field-by-field as dicts
    if is_dataclass(a) and is_dataclass(b):
        return deep_equal(asdict(a), asdict(b), **kwargs)  # type: ignore[arg-type]

    # NumPy arrays / scalars
    if _is_numpy(a) or _is_numpy(b):
        return _numpy_equal(a, b, **kwargs)

    # pandas objects
    if _is_pandas(a) and _is_pandas(b):
        try:
            return _pandas_equal(a, b, **kwargs)
        except AssertionError:
            return False
    # Mismatched pandas vs non-pandas: not equal (keeps semantics clear)
    if _is_pandas(a) != _is_pandas(b):
        return False

    # Mappings (dict-like)
    if isinstance(a, Mapping) and isinstance(b, Mapping):
        if set(a.keys()) != set(b.keys()):
            return False
        for k in a.keys():
            if not deep_equal(a[k], b[k], **kwargs):  # type: ignore[arg-type]
                return False
        return True

    # Sets/frozensets (unordered by definition)
    if isinstance(a, (set, frozenset)) and isinstance(b, (set, frozenset)):
        return _unordered_equal(a, b, deep_equal, **kwargs)

    # Sequences (list/tuple/range, but NOT str/bytes already handled)
    if _is_sequence(a) and _is_sequence(b):
        if not sequence_unordered:
            if len(a) != len(b):
                return False
            for x, y in zip(a, b):
                if not deep_equal(x, y, **kwargs):  # type: ignore[arg-type]
                    return False
            return True
        else:
            return _unordered_equal(a, b, deep_equal, **kwargs)

    # Fallback: try regular ==
    try:
        if a == b:
            return True
        # Handle NaN for types that bypassed earlier NA checks
        # if equal_nan and _is_na(a, none_equals_nan) and _is_na(b, none_equals_nan):
        #     return True
    except Exception:
        pass

    return False


#=========================================================================================
# helpers

# Shared NA check helper (covers None if requested)
def _is_na(x, none_equals_nan) -> bool:
    if none_equals_nan and x is None:
        return True
    try:
        val = pd.isna(x)
    except Exception:
        return False
    # If scalar, just return bool
    if np.isscalar(val):
        return bool(val)
    # If array-like, reduce to single truth value
    return bool(np.all(val))


def _is_number(x) -> bool:
    # bool is a Number, but we usually want bools compared exactly without tolerance
    return isinstance(x, Number) and not isinstance(x, bool)


def _is_sequence(x) -> bool:
    if isinstance(x, (str, bytes, bytearray, memoryview)):
        return False
    return isinstance(x, Sequence)


def _is_numpy(x) -> bool:
    return isinstance(x, (np.ndarray, np.generic))


def _is_pandas(x) -> bool:
    return isinstance(x, (pd.Series, pd.DataFrame, pd.Index))


def _num_equal(a, b, *, rtol, atol, equal_nan, **_) -> bool:
    # Handle NaN with equal_nan
    # if equal_nan and (pd.isna(a) and pd.isna(b)):
    #     return True
    if rtol == 0.0 and atol == 0.0:
        try:
            return a == b
        except Exception:
            return False
    # tolerant compare
    try:
        return math.isclose(float(a), float(b), rel_tol=rtol, abs_tol=atol)
    except Exception:
        # Fallback for extended numeric types
        try:
            return bool(np.isclose(a, b, rtol=rtol, atol=atol, equal_nan=equal_nan))
        except Exception:
            return False


def _numpy_equal(a, b, *, rtol, atol, equal_nan, **_) -> bool:
    # Scalars vs arrays are both supported by numpy utilities
    try:
        a_arr = np.asarray(a)
        b_arr = np.asarray(b)
    except Exception:
        return False

    if a_arr.shape != b_arr.shape:
        return False

    # Object dtype => elementwise deep recursion
    if a_arr.dtype == object or b_arr.dtype == object:
        for idx in np.ndindex(a_arr.shape):
            if not deep_equal(a_arr[idx], b_arr[idx], rtol=rtol, atol=atol, equal_nan=equal_nan):
                return False
        return True

    # Numeric / datetime / timedelta dtypes
    if rtol == 0.0 and atol == 0.0:
        # array_equal supports equal_nan (NumPy >= 1.19)
        return np.array_equal(a_arr, b_arr, equal_nan=equal_nan)
    else:
        try:
            return bool(np.all(np.isclose(a_arr, b_arr, rtol=rtol, atol=atol, equal_nan=equal_nan)))
        except Exception:
            return False


def _safe_can_isnan(arr: np.ndarray) -> bool:
    try:
        # Will error on non-floating types like strings/object without NaN
        np.isnan(arr)
        return True
    except Exception:
        return False


def _pandas_equal(
        a, b, *,
        rtol, atol, equal_nan,
        pandas_check_dtype, pandas_check_names,
        pandas_align_index, pandas_align_columns,
        pandas_check_like,
        **_,
        ) -> bool:
    # Normalize alignment (without modifying originals)
    def _align_df(df: pd.DataFrame) -> pd.DataFrame:
        if pandas_align_index:
            df = df.sort_index()
        if pandas_align_columns:
            df = df.sort_index(axis=1)
        return df

    def _align_s(s: pd.Series) -> pd.Series:
        if pandas_align_index:
            s = s.sort_index()
        return s

    def _align_idx(idx: pd.Index) -> pd.Index:
        if pandas_align_index:
            return idx.sort_values()
        return idx

    if isinstance(a, pd.DataFrame) and isinstance(b, pd.DataFrame):
        a2df, b2df = _align_df(a), _align_df(b)
        pdt.assert_frame_equal(
                a2df, b2df,
                check_dtype=pandas_check_dtype,
                check_exact=(rtol == 0.0 and atol == 0.0),
                rtol=rtol, atol=atol,
                check_names=pandas_check_names,
                check_like=pandas_check_like,  # ignore column order if True
                obj="DataFrame"
                )
        return True

    if isinstance(a, pd.Series) and isinstance(b, pd.Series):
        a2ps, b2ps = _align_s(a), _align_s(b)
        pdt.assert_series_equal(
                a2ps, b2ps,
                check_dtype=pandas_check_dtype,
                check_exact=(rtol == 0.0 and atol == 0.0),
                rtol=rtol, atol=atol,
                check_names=pandas_check_names,
                obj="Series"
                )
        return True

    if isinstance(a, pd.Index) and isinstance(b, pd.Index):
        a2pi, b2pi = _align_idx(a), _align_idx(b)
        pdt.assert_index_equal(
                a2pi, b2pi,
                exact=pandas_check_dtype,
                check_exact=(rtol == 0.0 and atol == 0.0),
                rtol=rtol, atol=atol,
                check_names=pandas_check_names,
                obj="Index"
                )
        return True

    # Different pandas kinds => not equal
    return False


def _unordered_equal(a, b, deep_equal_func, **kwargs) -> bool:
    """Helper for unordered sequence comparison."""
    a_list = list(a)
    b_list = list(b)
    if len(a_list) != len(b_list):
        return False
    used = [False] * len(b_list)
    for x in a_list:
        matched = False
        for i, y in enumerate(b_list):
            if not used[i] and deep_equal_func(x, y, **kwargs):
                used[i] = True
                matched = True
                break
        if not matched:
            return False
    return True


#=========================================================================================
# testing
#=========================================================================================

def _test_equal_func(equal_func):
    print(f"### {equal_func.__name__} Examples ###")

    # --- primitives ---
    print("int vs int:", equal_func(5, 5))
    print("int vs float (strict=False):", equal_func(5, 5.0))
    print("int vs float (strict=True):", equal_func(5, 5.0, strict_type=True))
    print("nan vs nan (equal_nan=True):", equal_func(float("nan"), float("nan"), equal_nan=True))
    print("nan vs nan (equal_nan=False):", equal_func(float("nan"), float("nan"), equal_nan=False))

    # --- numpy ---
    arr1 = np.array([1.0, 2.0, np.nan])
    arr2 = np.array([1.0, 2.0, np.nan])
    print("NumPy arrays with NaN:", equal_func(arr1, arr2))
    print("NumPy arrays tolerant compare:", equal_func([1.0, 2.0000001], [1.0, 2.0], rtol=1e-6))

    # numpy scalar vs Python scalar
    print("np.int64 vs int:", equal_func(np.int64(42), 42))

    # --- pandas ---
    s1 = pd.Series([1, 2, np.nan], name="x")
    s2 = pd.Series([1, 2, np.nan], name="x")
    s3 = pd.Series([1, 2, np.nan], name="y")
    print("Series equal:", equal_func(s1, s2))
    print("Series with different names (check_names=True):", equal_func(s1, s3))
    print("Series with different names (check_names=False):", equal_func(s1, s3, pandas_check_names=False))

    df1 = pd.DataFrame({"a": [1, 2], "b": [3, 4]})
    df2 = pd.DataFrame({"b": [3, 4], "a": [1, 2]})
    print("DataFrames column order ignored:", equal_func(df1, df2, pandas_check_like=True))
    print("DataFrames column order required:", equal_func(df1, df2, pandas_check_like=False))

    # --- containers ---
    print("List vs tuple:", equal_func([1, 2], (1, 2)))
    print("List vs tuple strict:", equal_func([1, 2], (1, 2), strict_type=True))
    print("Unordered sequence compare:", equal_func([1, 2, 3], [3, 2, 1], sequence_unordered=True))

    print("Dicts equal:", equal_func({"a": 1, "b": 2}, {"b": 2, "a": 1}))
    print("Sets equal:", equal_func({1, 2, 3}, {3, 2, 1}))


    # --- dataclass ---
    @dataclass
    class Point:
        x: int
        y: int


    p1 = Point(1, 2)
    p2 = Point(1, 2)
    p3 = Point(2, 3)
    print("Dataclass equal:", equal_func(p1, p2))
    print("Dataclass not equal:", equal_func(p1, p3))

    # --- datetime ---
    dt1 = datetime(2020, 1, 1, 12, tzinfo=timezone.utc)
    dt2 = datetime(2020, 1, 1, 7, tzinfo=timezone(timedelta(hours=-5)))
    print("Timezone-aware datetimes (normalize_tz=True):", equal_func(dt1, dt2))
    print("Timezone-aware datetimes (normalize_tz=False):", equal_func(dt1, dt2, normalize_tz=False))

    # --- tricky ---
    print("None vs NaN (none_equals_nan=True):", equal_func(None, float("nan")))
    print("None vs NaN (none_equals_nan=False):", equal_func(None, float("nan"), none_equals_nan=False))


#=========================================================================================
# main
#=========================================================================================

def main():
    # test the simple, and deep equality functions
    _test_equal_func(_shallow_equal)
    print('~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~')
    _test_equal_func(deep_equal)


if __name__ == "__main__":
    main()
