// AUTO-GENERATED FILE. DO NOT EDIT.
// source: src/pytra/built_in/type_id.py
// generated-by: tools/gen_runtime_from_manifest.py

mod py_runtime;
pub use crate::py_runtime::{math, pytra, time};
use crate::py_runtime::*;

fn py_register_generated_type_info() {
    static INIT: ::std::sync::Once = ::std::sync::Once::new();
    INIT.call_once(|| {
        py_register_type_info(0, 0, 0, 0);
        py_register_type_info(1, 3, 3, 3);
        py_register_type_info(2, 2, 2, 3);
        py_register_type_info(3, 4, 4, 4);
        py_register_type_info(4, 5, 5, 5);
        py_register_type_info(5, 6, 6, 6);
        py_register_type_info(6, 7, 7, 7);
        py_register_type_info(7, 8, 8, 8);
        py_register_type_info(8, 1, 1, 8);
    });
}

fn _tid_none() -> i64 {
    return 0;
}

fn _tid_bool() -> i64 {
    return 1;
}

fn _tid_int() -> i64 {
    return 2;
}

fn _tid_float() -> i64 {
    return 3;
}

fn _tid_str() -> i64 {
    return 4;
}

fn _tid_list() -> i64 {
    return 5;
}

fn _tid_dict() -> i64 {
    return 6;
}

fn _tid_set() -> i64 {
    return 7;
}

fn _tid_object() -> i64 {
    return 8;
}

fn _tid_user_base() -> i64 {
    return 1000;
}

fn _make_int_list_0() -> Vec<i64> {
    let out: Vec<i64> = vec![];
    return out;
}

fn _make_int_list_1(a0: i64) -> Vec<i64> {
    let mut out: Vec<i64> = vec![];
    out.push(a0);
    return out;
}

fn _contains_int(items: &[i64], value: i64) -> bool {
    let mut i = 0;
    while i < items.len() as i64 {
        if items[((i) as usize)] == value {
            return true;
        }
        i += 1;
    }
    return false;
}

fn _copy_int_list(items: &[i64]) -> Vec<i64> {
    let mut out: Vec<i64> = vec![];
    let mut i = 0;
    while i < items.len() as i64 {
        out.push(items[((i) as usize)]);
        i += 1;
    }
    return out;
}

fn _sorted_ints(items: &[i64]) -> Vec<i64> {
    let mut out = _copy_int_list(items);
    let mut i = 0;
    while i < out.len() as i64 {
        let mut j = i + 1;
        while j < out.len() as i64 {
            if out[((j) as usize)] < out[((i) as usize)] {
                let tmp = out[((i) as usize)];
                let __idx_1 = ((i) as usize);
                out[__idx_1] = out[((j) as usize)];
                let __idx_2 = ((j) as usize);
                out[__idx_2] = tmp;
            }
            j += 1;
        }
        i += 1;
    }
    return out;
}

fn _register_type_node(type_id: i64, base_type_id: i64) {
    if !_contains_int(&(_TYPE_IDS), type_id) {
        _TYPE_IDS.append(type_id);
    }
    let __idx_i64_4 = ((type_id) as i64);
    let __idx_3 = if __idx_i64_4 < 0 { (_TYPE_BASE.len() as i64 + __idx_i64_4) as usize } else { __idx_i64_4 as usize };
    _TYPE_BASE[__idx_3] = base_type_id;
    if !(type_id == _TYPE_CHILDREN) {
        let __idx_i64_6 = ((type_id) as i64);
        let __idx_5 = if __idx_i64_6 < 0 { (_TYPE_CHILDREN.len() as i64 + __idx_i64_6) as usize } else { __idx_i64_6 as usize };
        _TYPE_CHILDREN[__idx_5] = _make_int_list_0();
    }
    if base_type_id < 0 {
        return;
    }
    if !(base_type_id == _TYPE_CHILDREN) {
        let __idx_i64_8 = ((base_type_id) as i64);
        let __idx_7 = if __idx_i64_8 < 0 { (_TYPE_CHILDREN.len() as i64 + __idx_i64_8) as usize } else { __idx_i64_8 as usize };
        _TYPE_CHILDREN[__idx_7] = _make_int_list_0();
    }
    let mut children = _TYPE_CHILDREN[((if ((base_type_id) as i64) < 0 { (_TYPE_CHILDREN.len() as i64 + ((base_type_id) as i64)) } else { ((base_type_id) as i64) }) as usize)];
    if !_contains_int(&(children), type_id) {
        children.append(type_id);
        let __idx_i64_10 = ((base_type_id) as i64);
        let __idx_9 = if __idx_i64_10 < 0 { (_TYPE_CHILDREN.len() as i64 + __idx_i64_10) as usize } else { __idx_i64_10 as usize };
        _TYPE_CHILDREN[__idx_9] = children;
    }
}

fn _sorted_child_type_ids(type_id: i64) -> Vec<i64> {
    let mut children = _make_int_list_0();
    if type_id == _TYPE_CHILDREN {
        children = _TYPE_CHILDREN[((if ((type_id) as i64) < 0 { (_TYPE_CHILDREN.len() as i64 + ((type_id) as i64)) } else { ((type_id) as i64) }) as usize)];
    }
    return _sorted_ints(&(children));
}

fn _collect_root_type_ids() -> Vec<i64> {
    let mut roots: Vec<i64> = vec![];
    let mut i = 0;
    while i < _TYPE_IDS.len() as i64 {
        let tid = _TYPE_IDS[((i) as usize)];
        let mut base_tid = -1;
        if tid == _TYPE_BASE {
            base_tid = py_any_to_i64(&_TYPE_BASE[((if ((tid) as i64) < 0 { (_TYPE_BASE.len() as i64 + ((tid) as i64)) } else { ((tid) as i64) }) as usize)]);
        }
        if (base_tid < 0) || (!(base_tid == _TYPE_BASE)) {
            roots.push(tid);
        }
        i += 1;
    }
    return _sorted_ints(&(roots));
}

fn _assign_type_ranges_dfs(type_id: i64, next_order: i64) -> i64 {
    let __idx_i64_12 = ((type_id) as i64);
    let __idx_11 = if __idx_i64_12 < 0 { (_TYPE_ORDER.len() as i64 + __idx_i64_12) as usize } else { __idx_i64_12 as usize };
    _TYPE_ORDER[__idx_11] = next_order;
    let __idx_i64_14 = ((type_id) as i64);
    let __idx_13 = if __idx_i64_14 < 0 { (_TYPE_MIN.len() as i64 + __idx_i64_14) as usize } else { __idx_i64_14 as usize };
    _TYPE_MIN[__idx_13] = next_order;
    let mut cur = next_order + 1;
    let children = _sorted_child_type_ids(type_id);
    let mut i = 0;
    while i < children.len() as i64 {
        cur = _assign_type_ranges_dfs(children[((i) as usize)], cur);
        i += 1;
    }
    let __idx_i64_16 = ((type_id) as i64);
    let __idx_15 = if __idx_i64_16 < 0 { (_TYPE_MAX.len() as i64 + __idx_i64_16) as usize } else { __idx_i64_16 as usize };
    _TYPE_MAX[__idx_15] = cur - 1;
    return cur;
}

fn _recompute_type_ranges() {
    _TYPE_ORDER.clear();
    _TYPE_MIN.clear();
    _TYPE_MAX.clear();
    
    let mut next_order = 0;
    let roots = _collect_root_type_ids();
    let mut i = 0;
    while i < roots.len() as i64 {
        next_order = _assign_type_ranges_dfs(roots[((i) as usize)], next_order);
        i += 1;
    }
    let all_ids = _sorted_ints(&(_TYPE_IDS));
    i = 0;
    while i < all_ids.len() as i64 {
        let tid = all_ids[((i) as usize)];
        if !(tid == _TYPE_ORDER) {
            next_order = _assign_type_ranges_dfs(tid, next_order);
        }
        i += 1;
    }
}

fn _mark_type_ranges_dirty() {
    let __idx_i64_18 = ((("ranges_dirty").to_string()) as i64);
    let __idx_17 = if __idx_i64_18 < 0 { (_TYPE_STATE.len() as i64 + __idx_i64_18) as usize } else { __idx_i64_18 as usize };
    _TYPE_STATE[__idx_17] = 1;
}

fn _mark_type_ranges_clean() {
    let __idx_i64_20 = ((("ranges_dirty").to_string()) as i64);
    let __idx_19 = if __idx_i64_20 < 0 { (_TYPE_STATE.len() as i64 + __idx_i64_20) as usize } else { __idx_i64_20 as usize };
    _TYPE_STATE[__idx_19] = 0;
}

fn _is_type_ranges_dirty() -> bool {
    return (_TYPE_STATE.get(("ranges_dirty").to_string(), 1) != 0);
}

fn _ensure_type_ranges() {
    if _is_type_ranges_dirty() {
        _recompute_type_ranges();
        _mark_type_ranges_clean();
    }
}

fn _ensure_builtins() {
    if !(("next_user_type_id").to_string() == _TYPE_STATE) {
        let __idx_i64_22 = ((("next_user_type_id").to_string()) as i64);
        let __idx_21 = if __idx_i64_22 < 0 { (_TYPE_STATE.len() as i64 + __idx_i64_22) as usize } else { __idx_i64_22 as usize };
        _TYPE_STATE[__idx_21] = _tid_user_base();
    }
    if !(("ranges_dirty").to_string() == _TYPE_STATE) {
        let __idx_i64_24 = ((("ranges_dirty").to_string()) as i64);
        let __idx_23 = if __idx_i64_24 < 0 { (_TYPE_STATE.len() as i64 + __idx_i64_24) as usize } else { __idx_i64_24 as usize };
        _TYPE_STATE[__idx_23] = 1;
    }
    if _TYPE_IDS.len() as i64 > 0 {
        return;
    }
    _register_type_node(_tid_none(), -1);
    _register_type_node(_tid_object(), -1);
    _register_type_node(_tid_int(), _tid_object());
    _register_type_node(_tid_bool(), _tid_int());
    _register_type_node(_tid_float(), _tid_object());
    _register_type_node(_tid_str(), _tid_object());
    _register_type_node(_tid_list(), _tid_object());
    _register_type_node(_tid_dict(), _tid_object());
    _register_type_node(_tid_set(), _tid_object());
    _recompute_type_ranges();
    _mark_type_ranges_clean();
}

fn _normalize_base_type_id(base_type_id: i64) -> i64 {
    _ensure_builtins();
    if !(({ py_register_generated_type_info(); py_runtime_value_isinstance(&base_type_id, PYTRA_TID_INT) })) {
        panic!("{}", ("base type_id must be int").to_string());
    }
    if !(base_type_id == _TYPE_BASE) {
        panic!("{}", format!("{}{}", ("unknown base type_id: ").to_string(), (base_type_id).to_string()));
    }
    return base_type_id;
}

fn py_tid_register_class_type(base_type_id: i64) -> i64 {
    _ensure_builtins();
    let base_tid = _normalize_base_type_id(base_type_id);
    
    let mut tid = _TYPE_STATE[((if ((("next_user_type_id").to_string()) as i64) < 0 { (_TYPE_STATE.len() as i64 + ((("next_user_type_id").to_string()) as i64)) } else { ((("next_user_type_id").to_string()) as i64) }) as usize)];
    while tid == _TYPE_BASE {
        tid += 1;
    }
    let __idx_i64_26 = ((("next_user_type_id").to_string()) as i64);
    let __idx_25 = if __idx_i64_26 < 0 { (_TYPE_STATE.len() as i64 + __idx_i64_26) as usize } else { __idx_i64_26 as usize };
    _TYPE_STATE[__idx_25] = tid + 1;
    
    _register_type_node(tid, base_tid);
    _mark_type_ranges_dirty();
    return tid;
}

fn py_tid_register_known_class_type(type_id: i64, base_type_id: i64) -> i64 {
    _ensure_builtins();
    if !(({ py_register_generated_type_info(); py_runtime_value_isinstance(&type_id, PYTRA_TID_INT) })) {
        panic!("{}", ("type_id must be int").to_string());
    }
    if type_id < _tid_user_base() {
        panic!("{}", format!("{}{}", ("user type_id must be >= ").to_string(), (_tid_user_base()).to_string()));
    }
    let base_tid = _normalize_base_type_id(base_type_id);
    if type_id == _TYPE_BASE {
        if _TYPE_BASE[((if ((type_id) as i64) < 0 { (_TYPE_BASE.len() as i64 + ((type_id) as i64)) } else { ((type_id) as i64) }) as usize)] != base_tid {
            panic!("{}", ("type_id already registered with different base").to_string());
        }
        return type_id;
    }
    _register_type_node(type_id, base_tid);
    let next_user_type_id = _TYPE_STATE[((if ((("next_user_type_id").to_string()) as i64) < 0 { (_TYPE_STATE.len() as i64 + ((("next_user_type_id").to_string()) as i64)) } else { ((("next_user_type_id").to_string()) as i64) }) as usize)];
    if type_id >= next_user_type_id {
        let __idx_i64_28 = ((("next_user_type_id").to_string()) as i64);
        let __idx_27 = if __idx_i64_28 < 0 { (_TYPE_STATE.len() as i64 + __idx_i64_28) as usize } else { __idx_i64_28 as usize };
        _TYPE_STATE[__idx_27] = type_id + 1;
    }
    _mark_type_ranges_dirty();
    return type_id;
}

fn _try_runtime_tagged_type_id(value: PyAny) -> i64 {
    let tagged = py_runtime_value_type_id(&value);
    if { py_register_generated_type_info(); py_runtime_value_isinstance(&tagged, PYTRA_TID_INT) } {
        let tagged_id = ((tagged) as i64);
        if tagged_id == _TYPE_BASE {
            return tagged_id;
        }
    }
    return -1;
}

fn py_tid_runtime_type_id(value: PyAny) -> i64 {
    _ensure_builtins();
    if value == () {
        return _tid_none();
    }
    if { py_register_generated_type_info(); py_runtime_value_isinstance(&value, PYTRA_TID_BOOL) } {
        return _tid_bool();
    }
    if { py_register_generated_type_info(); py_runtime_value_isinstance(&value, PYTRA_TID_INT) } {
        return _tid_int();
    }
    if { py_register_generated_type_info(); py_runtime_value_isinstance(&value, PYTRA_TID_FLOAT) } {
        return _tid_float();
    }
    if { py_register_generated_type_info(); py_runtime_value_isinstance(&value, PYTRA_TID_STR) } {
        return _tid_str();
    }
    if { py_register_generated_type_info(); py_runtime_value_isinstance(&value, PYTRA_TID_LIST) } {
        return _tid_list();
    }
    if { py_register_generated_type_info(); py_runtime_value_isinstance(&value, PYTRA_TID_DICT) } {
        return _tid_dict();
    }
    if { py_register_generated_type_info(); py_runtime_value_isinstance(&value, PYTRA_TID_SET) } {
        return _tid_set();
    }
    let tagged = _try_runtime_tagged_type_id(value);
    if tagged >= 0 {
        return tagged;
    }
    return _tid_object();
}

fn py_tid_is_subtype(actual_type_id: i64, expected_type_id: i64) -> bool {
    _ensure_builtins();
    _ensure_type_ranges();
    if !(actual_type_id == _TYPE_ORDER) {
        return false;
    }
    if !(expected_type_id == _TYPE_ORDER) {
        return false;
    }
    let actual_order = _TYPE_ORDER[((if ((actual_type_id) as i64) < 0 { (_TYPE_ORDER.len() as i64 + ((actual_type_id) as i64)) } else { ((actual_type_id) as i64) }) as usize)];
    let expected_min = _TYPE_MIN[((if ((expected_type_id) as i64) < 0 { (_TYPE_MIN.len() as i64 + ((expected_type_id) as i64)) } else { ((expected_type_id) as i64) }) as usize)];
    let expected_max = _TYPE_MAX[((if ((expected_type_id) as i64) < 0 { (_TYPE_MAX.len() as i64 + ((expected_type_id) as i64)) } else { ((expected_type_id) as i64) }) as usize)];
    return ((expected_min <= actual_order) && (actual_order <= expected_max));
}

fn py_tid_issubclass(actual_type_id: i64, expected_type_id: i64) -> bool {
    return ({ py_register_generated_type_info(); py_runtime_type_id_is_subtype(actual_type_id, expected_type_id) });
}

fn py_tid_isinstance(value: PyAny, expected_type_id: i64) -> bool {
    return ({ py_register_generated_type_info(); py_runtime_type_id_is_subtype(py_runtime_value_type_id(&value), expected_type_id) });
}

fn _py_reset_type_registry_for_test() {
    _TYPE_IDS.clear();
    _TYPE_BASE.clear();
    _TYPE_CHILDREN.clear();
    _TYPE_ORDER.clear();
    _TYPE_MIN.clear();
    _TYPE_MAX.clear();
    _TYPE_STATE.clear();
    let __idx_i64_30 = ((("next_user_type_id").to_string()) as i64);
    let __idx_29 = if __idx_i64_30 < 0 { (_TYPE_STATE.len() as i64 + __idx_i64_30) as usize } else { __idx_i64_30 as usize };
    _TYPE_STATE[__idx_29] = _tid_user_base();
    let __idx_i64_32 = ((("ranges_dirty").to_string()) as i64);
    let __idx_31 = if __idx_i64_32 < 0 { (_TYPE_STATE.len() as i64 + __idx_i64_32) as usize } else { __idx_i64_32 as usize };
    _TYPE_STATE[__idx_31] = 1;
    _ensure_builtins();
}

fn main() {
    py_register_generated_type_info();
    ("Pure-Python source-of-truth for single-inheritance type_id range semantics.").to_string();
    let _TYPE_IDS: Vec<i64> = vec![];
    let _TYPE_BASE: ::std::collections::BTreeMap<i64, i64> = ::std::collections::BTreeMap::from([]);
    let _TYPE_CHILDREN: ::std::collections::BTreeMap<i64, Vec<i64>> = ::std::collections::BTreeMap::from([]);
    let _TYPE_ORDER: ::std::collections::BTreeMap<i64, i64> = ::std::collections::BTreeMap::from([]);
    let _TYPE_MIN: ::std::collections::BTreeMap<i64, i64> = ::std::collections::BTreeMap::from([]);
    let _TYPE_MAX: ::std::collections::BTreeMap<i64, i64> = ::std::collections::BTreeMap::from([]);
    let _TYPE_STATE: ::std::collections::BTreeMap<String, i64> = ::std::collections::BTreeMap::from([]);
}
