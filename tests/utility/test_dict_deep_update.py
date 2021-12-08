from hypothesis.strategies._internal.core import recursive
import pytest
from hypothesis import given, strategies as st
from string import printable
from typing import Dict, Any, List, Tuple
import json
from pyconfme.utility.dict_deep_update import (
    dict_deep_update,
    MAX_RECURSION_DEPTH,
)

key_strategies = (
    st.none() | st.booleans() | st.integers() | st.floats() | st.text(printable)
)
value_strategies = (
    st.none()
    | st.booleans()
    | st.integers()
    | st.floats()
    | st.text(printable)
    | st.lists(
        st.none() | st.booleans() | st.integers() | st.floats() | st.text(printable)
    )
    | st.dictionaries(
        st.text(printable),
        st.none() | st.booleans() | st.integers() | st.floats() | st.text(printable),
    )
)
value_no_lists_strategies = (
    st.none()
    | st.booleans()
    | st.integers()
    | st.floats()
    | st.text(printable)
)



@st.composite
def dict_deep_update_strategy(draw, keys=key_strategies, values=value_strategies, values_no_lists=value_no_lists_strategies):

    k1 = draw(keys)
    v1 = draw(values)
    k2 = draw(keys)
    v2 = draw(values)
    k3 = draw(keys)
    v3 = draw(values)
    vp1 = draw(keys)
    vp2 = draw(keys)
    vp3 = draw(keys)
    vnl1 = draw(values_no_lists)
    vnl2 = draw(values_no_lists)

    return (k1,v1,k2,v2,k3,v3,vp1,vp2,vp3,vnl1,vnl2)



def _check_test_case_dict(test_case_dict):
    merged_dict = test_case_dict["target"]
    dict_deep_update(merged_dict, test_case_dict["source"])
    assert merged_dict == test_case_dict["result"]


def _inner_test_dict_deep_merge(test_case_dict):
    if test_case_dict["target"] is None or test_case_dict["source"] is None:
        with pytest.raises(ValueError):
            _check_test_case_dict(test_case_dict)
        return None

    if test_case_dict["should_raise_recursion_exception"] == True:
        with pytest.raises(RecursionError):
            _check_test_case_dict(test_case_dict)
        return None

    _check_test_case_dict(test_case_dict)




@given(dict_keys_values=dict_deep_update_strategy())
def test_dict_deep_update_001(dict_keys_values):
    k1,v1,k2,v2,k3,v3,vp1,vp2,vp3,vnl1,vnl2 = dict_keys_values
    test_case_dict = {
        "should_raise_recursion_exception": False,
        "target": {k1: v1, k2: vnl1},
        "source": {k3: vnl2},
        "result": {k1: v1, k2: vnl1, k3: vnl2},
    }
    _inner_test_dict_deep_merge(test_case_dict)
    

@given(dict_keys_values=dict_deep_update_strategy())
def test_dict_deep_update_002(dict_keys_values):
    k1,v1,k2,v2,k3,v3,vp1,vp2,vp3,vnl1,vnl2 = dict_keys_values
    test_case_dict = {
        "should_raise_recursion_exception": False,
        "target": {k1: v1, k2: vp2},
        "source": {k2: vp3},
        "result": {k1: v1, k2: vp3},
    }
    _inner_test_dict_deep_merge(test_case_dict)


@given(dict_keys_values=dict_deep_update_strategy())
def test_dict_deep_update_003(dict_keys_values):
    k1,v1,k2,v2,k3,v3,vp1,vp2,vp3,vnl1,vnl2 = dict_keys_values
    test_case_dict = {
        "should_raise_recursion_exception": False,
        "target": {k1: v1, k2: [vp2]},
        "source": {k2: [v2, vp3]},
        "result": {k1: v1, k2: [vp2, v2, vp3]},
    }
    _inner_test_dict_deep_merge(test_case_dict)


@given(dict_keys_values=dict_deep_update_strategy())
def test_dict_deep_update_004(dict_keys_values):
    k1,v1,k2,v2,k3,v3,vp1,vp2,vp3,vnl1,vnl2 = dict_keys_values
    test_case_dict = {
        "should_raise_recursion_exception": False,
        "target": {k1: v1, k2: [vp2]},
        "source": {k2: vp3},
        "result": {k1: v1, k2: vp3},
    }
    _inner_test_dict_deep_merge(test_case_dict)

@given(dict_keys_values=dict_deep_update_strategy())
def test_dict_deep_update_005(dict_keys_values):
    k1,v1,k2,v2,k3,v3,vp1,vp2,vp3,vnl1,vnl2 = dict_keys_values
    test_case_dict = {
        "should_raise_recursion_exception": False,
        "target": {k1: v1, k2: {k3: vp2} },
        "source": {k2: [v2, vp3]},
        "result": {k1: v1, k2: [v2, vp3]},
    }
    _inner_test_dict_deep_merge(test_case_dict)

@given(dict_keys_values=dict_deep_update_strategy())
def test_dict_deep_update_006(dict_keys_values):
    k1,v1,k2,v2,k3,v3,vp1,vp2,vp3,vnl1,vnl2 = dict_keys_values
    test_case_dict = {
        "should_raise_recursion_exception": False,
        "target": {k1: v1, k2: {k3: vp2}},
        "source": {k2: vp3},
        "result": {k1: v1, k2: vp3},
    }
    _inner_test_dict_deep_merge(test_case_dict)


@given(dict_keys_values=dict_deep_update_strategy())
def test_dict_deep_update_007(dict_keys_values):
    k1,v1,k2,v2,k3,v3,vp1,vp2,vp3,vnl1,vnl2 = dict_keys_values
    test_case_dict = {
        "should_raise_recursion_exception": False,
        "target": {k1: v1, k2: {k3: vp2}},
        "source": {k2: {k3: vp3}},
        "result": {k1: v1, k2: {k3: vp3}},
    }
    _inner_test_dict_deep_merge(test_case_dict)


@given(dict_keys_values=dict_deep_update_strategy())
def test_dict_deep_update_008(dict_keys_values):
    k1,v1,k2,v2,k3,v3,vp1,vp2,vp3,vnl1,vnl2 = dict_keys_values
    test_case_dict = {
        "should_raise_recursion_exception": False,
        "target": {k1: v1, k2: {k3: vp2}},
        "source": {k2: {k2: v3}},
        "result": {k1: v1, k2: {k3: vp2, k2: v3}},
    }
    _inner_test_dict_deep_merge(test_case_dict)


@given(dict_keys_values=dict_deep_update_strategy())
def test_dict_deep_update_009(dict_keys_values):
    k1,v1,k2,v2,k3,v3,vp1,vp2,vp3,vnl1,vnl2 = dict_keys_values
    test_case_dict = {
        "should_raise_recursion_exception": False,
        "target": {k1: v1, k2: {k3: vp2}},
        "source": {k2: {k2: v3}},
        "result": {k1: v1, k2: {k3: vp2, k2: v3}},
    }
    _inner_test_dict_deep_merge(test_case_dict)


@given(dict_keys_values=dict_deep_update_strategy())
def test_dict_deep_update_010(dict_keys_values):
    k1,v1,k2,v2,k3,v3,vp1,vp2,vp3,vnl1,vnl2 = dict_keys_values
    test_case_dict = {
        "should_raise_recursion_exception": False,
        "target": {k1: v1, k2: {k3: vp2}},
        "source": {k2: {k2: v3}},
        "result": {k1: v1, k2: {k3: vp2, k2: v3}},
    }
    _inner_test_dict_deep_merge(test_case_dict)


@given(dict_keys_values=dict_deep_update_strategy())
def test_dict_deep_update_011(dict_keys_values):
    k1,v1,k2,v2,k3,v3,vp1,vp2,vp3,vnl1,vnl2 = dict_keys_values
    test_case_dict = {
        "should_raise_recursion_exception": False,
        "target": {k1: v1, k2: vnl1},
        "source": {k2: vnl2},
        "result": {k1: v1, k2: vnl2},
    }
    _inner_test_dict_deep_merge(test_case_dict)


@given(dict_keys_values=dict_deep_update_strategy())
def test_dict_deep_update_012(dict_keys_values):
    k1,v1,k2,v2,k3,v3,vp1,vp2,vp3,vnl1,vnl2 = dict_keys_values
    assert MAX_RECURSION_DEPTH == 8
    test_case_dict = {
        "should_raise_recursion_exception": False,
        "target": {k1: v1, k2: vnl2},
        "source": {k2: {k1: {k1: {k1: {k1: {k1: {k1: { k1: { k1: {k1: [v1, v2]}}}}}}}}}},
        "result": {k1: v1, k2: {k1: {k1: {k1: {k1: {k1: {k1: { k1: { k1: {k1: [v1, v2]}}}}}}}}}},
    }
    _inner_test_dict_deep_merge(test_case_dict)


@given(dict_keys_values=dict_deep_update_strategy())
def test_dict_deep_update_013(dict_keys_values):
    k1,v1,k2,v2,k3,v3,vp1,vp2,vp3,vnl1,vnl2 = dict_keys_values
    assert MAX_RECURSION_DEPTH == 8
    test_case_dict = {
        "should_raise_recursion_exception": True,
        "target": {k1: v1, k2: {k1: {k1: {k1: {k1: {k1: {k1: { k1: { k1: {k1: [v1, v3]}}}}}}}}}},
        "source": {k2: {k1: {k1: {k1: {k1: {k1: {k1: { k1: { k1: {k1: [v1, v2]}}}}}}}}}},
        "result": {k1: v1, k2: {k1: {k1: {k1: {k1: {k1: {k1: { k1: { k1: {k1: [v1, v2]}}}}}}}}}},
    }
    assert test_case_dict["should_raise_recursion_exception"] == True
    _inner_test_dict_deep_merge(test_case_dict)


