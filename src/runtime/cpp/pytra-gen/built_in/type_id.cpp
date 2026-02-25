// AUTO-GENERATED FILE. DO NOT EDIT.
// source: src/pytra/built_in/type_id.py
// generated-by: src/py2cpp.py
#include "runtime/cpp/pytra/built_in/py_runtime.h"

#include "pytra/built_in/type_id.h"

#include "pytra/std/typing.h"

list<int64> _TYPE_IDS;
dict<int64, int64> _TYPE_BASE;
dict<int64, list<int64>> _TYPE_CHILDREN;
dict<int64, int64> _TYPE_ORDER;
dict<int64, int64> _TYPE_MIN;
dict<int64, int64> _TYPE_MAX;
dict<str, int64> _TYPE_STATE;


int64 _tid_none() {
    return 0;
}

int64 _tid_bool() {
    return 1;
}

int64 _tid_int() {
    return 2;
}

int64 _tid_float() {
    return 3;
}

int64 _tid_str() {
    return 4;
}

int64 _tid_list() {
    return 5;
}

int64 _tid_dict() {
    return 6;
}

int64 _tid_set() {
    return 7;
}

int64 _tid_object() {
    return 8;
}

int64 _tid_user_base() {
    return 1000;
}

list<int64> _make_int_list_0() {
    list<int64> out = list<int64>{};
    return out;
}

list<int64> _make_int_list_1(int64 a0) {
    list<int64> out = list<int64>{};
    out.append(int64(a0));
    return out;
}

bool _contains_int(const list<int64>& items, int64 value) {
    int64 i = 0;
    while (i < py_len(items)) {
        if (items[i] == value)
            return true;
        i++;
    }
    return false;
}

list<int64> _copy_int_list(const list<int64>& items) {
    list<int64> out = list<int64>{};
    int64 i = 0;
    while (i < py_len(items)) {
        out.append(int64(items[i]));
        i++;
    }
    return out;
}

list<int64> _sorted_ints(const list<int64>& items) {
    list<int64> out = _copy_int_list(items);
    int64 i = 0;
    while (i < py_len(out)) {
        int64 j = i + 1;
        while (j < py_len(out)) {
            if (out[j] < out[i]) {
                int64 tmp = out[i];
                out[i] = out[j];
                out[j] = tmp;
            }
            j++;
        }
        i++;
    }
    return out;
}

void _register_type_node(int64 type_id, int64 base_type_id) {
    if (!(_contains_int(_TYPE_IDS, type_id)))
        py_append(_TYPE_IDS, make_object(type_id));
    _TYPE_BASE[type_id] = base_type_id;
    if (!py_contains(_TYPE_CHILDREN, type_id))
        _TYPE_CHILDREN[type_id] = _make_int_list_0();
    if (base_type_id < 0)
        return;
    if (!py_contains(_TYPE_CHILDREN, base_type_id))
        _TYPE_CHILDREN[base_type_id] = _make_int_list_0();
    auto children = py_at(_TYPE_CHILDREN, py_to_int64(base_type_id));
    if (!(_contains_int(children, type_id)))
        py_append(children, make_object(type_id));
}

list<int64> _sorted_child_type_ids(int64 type_id) {
    list<int64> children = _make_int_list_0();
    if (py_contains(_TYPE_CHILDREN, type_id))
        children = list<int64>(py_at(_TYPE_CHILDREN, py_to_int64(type_id)));
    return _sorted_ints(children);
}

list<int64> _collect_root_type_ids() {
    list<int64> roots = list<int64>{};
    int64 i = 0;
    while (i < py_len(_TYPE_IDS)) {
        auto tid = py_at(_TYPE_IDS, py_to_int64(i));
        int64 base_tid = -1;
        if (py_contains(_TYPE_BASE, tid))
            base_tid = int64(py_to_int64(py_at(_TYPE_BASE, py_to_int64(tid))));
        if ((base_tid < 0) || (!py_contains(_TYPE_BASE, base_tid)))
            roots.append(int64(tid));
        i++;
    }
    return _sorted_ints(roots);
}

int64 _assign_type_ranges_dfs(int64 type_id, int64 next_order) {
    _TYPE_ORDER[type_id] = next_order;
    _TYPE_MIN[type_id] = next_order;
    int64 cur = next_order + 1;
    list<int64> children = _sorted_child_type_ids(type_id);
    int64 i = 0;
    while (i < py_len(children)) {
        cur = _assign_type_ranges_dfs(children[i], cur);
        i++;
    }
    _TYPE_MAX[type_id] = cur - 1;
    return cur;
}

void _recompute_type_ranges() {
    _TYPE_ORDER.clear();
    _TYPE_MIN.clear();
    _TYPE_MAX.clear();
    
    int64 next_order = 0;
    list<int64> roots = _collect_root_type_ids();
    int64 i = 0;
    while (i < py_len(roots)) {
        next_order = _assign_type_ranges_dfs(roots[i], next_order);
        i++;
    }
    list<int64> all_ids = _sorted_ints(_TYPE_IDS);
    i = 0;
    while (i < py_len(all_ids)) {
        int64 tid = all_ids[i];
        if (!py_contains(_TYPE_ORDER, tid))
            next_order = _assign_type_ranges_dfs(tid, next_order);
        i++;
    }
}

void _ensure_builtins() {
    if (!py_contains(_TYPE_STATE, "next_user_type_id"))
        _TYPE_STATE["next_user_type_id"] = _tid_user_base();
    if (py_len(_TYPE_IDS) > 0)
        return;
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
}

list<int64> _normalize_base_type_ids(const list<int64>& base_type_ids) {
    _ensure_builtins();
    list<int64> out = list<int64>{};
    int64 i = 0;
    while (i < py_len(base_type_ids)) {
        int64 tid = base_type_ids[i];
        if (py_isinstance(tid, PYTRA_TID_INT)) {
            if (!(_contains_int(out, tid)))
                out.append(int64(tid));
        }
        i++;
    }
    if (py_len(out) == 0)
        out.append(int64(_tid_object()));
    if (py_len(out) > 1)
        throw ValueError("multiple inheritance is not supported");
    if (!py_contains(_TYPE_BASE, out[0]))
        throw ValueError("unknown base type_id: " + ::std::to_string(out[0]));
    return out;
}

int64 py_tid_register_class_type(const list<int64>& base_type_ids) {
    /* Allocate and register a new user class type_id. */
    _ensure_builtins();
    list<int64> bases = _normalize_base_type_ids(base_type_ids);
    int64 base_tid = bases[0];
    
    auto tid = py_dict_get(_TYPE_STATE, "next_user_type_id");
    while (py_contains(_TYPE_BASE, tid)) {
        tid++;
    }
    _TYPE_STATE["next_user_type_id"] = tid + 1;
    
    _register_type_node(tid, base_tid);
    _recompute_type_ranges();
    return tid;
}

int64 _try_runtime_tagged_type_id(const object& value) {
    auto tagged = getattr(value, "PYTRA_TYPE_ID", ::std::nullopt);
    if (py_isinstance(tagged, PYTRA_TID_INT)) {
        if (py_contains(_TYPE_BASE, tagged))
            return tagged;
    }
    return -1;
}

int64 py_tid_runtime_type_id(const object& value) {
    /* Resolve runtime type_id for a Python value. */
    _ensure_builtins();
    if (py_is_none(value))
        return _tid_none();
    if (py_isinstance(value, PYTRA_TID_BOOL))
        return _tid_bool();
    if (py_isinstance(value, PYTRA_TID_INT))
        return _tid_int();
    if (py_isinstance(value, PYTRA_TID_FLOAT))
        return _tid_float();
    if (py_isinstance(value, PYTRA_TID_STR))
        return _tid_str();
    if (py_isinstance(value, PYTRA_TID_LIST))
        return _tid_list();
    if (py_isinstance(value, PYTRA_TID_DICT))
        return _tid_dict();
    if (py_isinstance(value, PYTRA_TID_SET))
        return _tid_set();
    int64 tagged = _try_runtime_tagged_type_id(value);
    if (tagged >= 0)
        return tagged;
    return _tid_object();
}

bool py_tid_is_subtype(int64 actual_type_id, int64 expected_type_id) {
    /* Check nominal subtype relation by type_id order range. */
    _ensure_builtins();
    if (!py_contains(_TYPE_ORDER, actual_type_id))
        return false;
    if (!py_contains(_TYPE_ORDER, expected_type_id))
        return false;
    auto actual_order = py_at(_TYPE_ORDER, py_to_int64(actual_type_id));
    auto expected_min = py_at(_TYPE_MIN, py_to_int64(expected_type_id));
    auto expected_max = py_at(_TYPE_MAX, py_to_int64(expected_type_id));
    return (expected_min <= actual_order) && (actual_order <= expected_max);
}

bool py_tid_issubclass(int64 actual_type_id, int64 expected_type_id) {
    return py_is_subtype(actual_type_id, expected_type_id);
}

bool py_tid_isinstance(const object& value, int64 expected_type_id) {
    return py_is_subtype(py_runtime_type_id(value), expected_type_id);
}

void _py_reset_type_registry_for_test() {
    /* Reset mutable registry state for deterministic unit tests. */
    _TYPE_IDS.clear();
    _TYPE_BASE.clear();
    _TYPE_CHILDREN.clear();
    _TYPE_ORDER.clear();
    _TYPE_MIN.clear();
    _TYPE_MAX.clear();
    _TYPE_STATE.clear();
    _TYPE_STATE["next_user_type_id"] = _tid_user_base();
    _ensure_builtins();
}

static void __pytra_module_init() {
    static bool __initialized = false;
    if (__initialized) return;
    __initialized = true;
    /* Pure-Python source-of-truth for single-inheritance type_id range semantics. */
    list<int64> _TYPE_IDS = list<int64>{};
    dict<int64, int64> _TYPE_BASE = dict<int64, int64>{};
    dict<int64, list<int64>> _TYPE_CHILDREN = dict<int64, list<int64>>{};
    dict<int64, int64> _TYPE_ORDER = dict<int64, int64>{};
    dict<int64, int64> _TYPE_MIN = dict<int64, int64>{};
    dict<int64, int64> _TYPE_MAX = dict<int64, int64>{};
    dict<str, int64> _TYPE_STATE = dict<str, int64>{};
}
