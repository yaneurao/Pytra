// AUTO-GENERATED FILE. DO NOT EDIT.
// source: src/pytra/built_in/type_id.py
// generated-by: tools/gen_runtime_from_manifest.py

#ifndef PYTRA_GEN_BUILT_IN_TYPE_ID_H
#define PYTRA_GEN_BUILT_IN_TYPE_ID_H

// forward declarations
int64 _tid_none();
int64 _tid_bool();
int64 _tid_int();
int64 _tid_float();
int64 _tid_str();
int64 _tid_list();
int64 _tid_dict();
int64 _tid_set();
int64 _tid_object();
int64 _tid_user_base();
list<int64> _make_int_list_0();
list<int64> _make_int_list_1(int64 a0);
bool _contains_int(const list<int64>& items, int64 value);
list<int64> _copy_int_list(const list<int64>& items);
list<int64> _sorted_ints(const list<int64>& items);
void _register_type_node(int64 type_id, int64 base_type_id);
list<int64> _sorted_child_type_ids(int64 type_id);
list<int64> _collect_root_type_ids();
int64 _assign_type_ranges_dfs(int64 type_id, int64 next_order);
void _recompute_type_ranges();
void _mark_type_ranges_dirty();
void _mark_type_ranges_clean();
bool _is_type_ranges_dirty();
void _ensure_type_ranges();
void _ensure_builtins();
int64 _normalize_base_type_id(int64 base_type_id);
int64 py_tid_register_class_type(int64 base_type_id);
int64 py_tid_register_known_class_type(int64 type_id, int64 base_type_id);
int64 _try_runtime_tagged_type_id(const object& value);
int64 py_tid_runtime_type_id(const object& value);
bool py_tid_is_subtype(int64 actual_type_id, int64 expected_type_id);
bool py_tid_issubclass(int64 actual_type_id, int64 expected_type_id);
bool py_tid_isinstance(const object& value, int64 expected_type_id);
void _py_reset_type_registry_for_test();

list<int64> _TYPE_IDS;
dict<int64, int64> _TYPE_BASE;
dict<int64, list<int64>> _TYPE_CHILDREN;
dict<int64, int64> _TYPE_ORDER;
dict<int64, int64> _TYPE_MIN;
dict<int64, int64> _TYPE_MAX;
dict<str, int64> _TYPE_STATE;

/* Pure-Python source-of-truth for single-inheritance type_id range semantics. */

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
    list<int64> out = {};
    return out;
}

list<int64> _make_int_list_1(int64 a0) {
    list<int64> out = {};
    out.append(a0);
    return out;
}

bool _contains_int(const list<int64>& items, int64 value) {
    int64 i = 0;
    while (i < items.size()) {
        if (items[i] == value)
            return true;
        i++;
    }
    return false;
}

list<int64> _copy_int_list(const list<int64>& items) {
    list<int64> out = {};
    int64 i = 0;
    while (i < items.size()) {
        out.append(items[i]);
        i++;
    }
    return out;
}

list<int64> _sorted_ints(const list<int64>& items) {
    list<int64> out = _copy_int_list(items);
    int64 i = 0;
    while (i < out.size()) {
        int64 j = i + 1;
        while (j < out.size()) {
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
        _TYPE_IDS.append(type_id);
    _TYPE_BASE[type_id] = base_type_id;
    if (!py_contains(_TYPE_CHILDREN, type_id))
        _TYPE_CHILDREN[type_id] = _make_int_list_0();
    if (base_type_id < 0)
        return;
    if (!py_contains(_TYPE_CHILDREN, base_type_id))
        _TYPE_CHILDREN[base_type_id] = _make_int_list_0();
    list<int64> children = ([&]() { auto&& __dict_1 = _TYPE_CHILDREN; auto __dict_key_2 = base_type_id; return __dict_1.at(__dict_key_2); }());
    if (!(_contains_int(children, type_id))) {
        children.append(type_id);
        _TYPE_CHILDREN[base_type_id] = children;
    }
}

list<int64> _sorted_child_type_ids(int64 type_id) {
    list<int64> children = _make_int_list_0();
    if (py_contains(_TYPE_CHILDREN, type_id))
        children = ([&]() { auto&& __dict_3 = _TYPE_CHILDREN; auto __dict_key_4 = type_id; return __dict_3.at(__dict_key_4); }());
    return _sorted_ints(children);
}

list<int64> _collect_root_type_ids() {
    list<int64> roots = {};
    int64 i = 0;
    while (i < _TYPE_IDS.size()) {
        int64 tid = _TYPE_IDS[i];
        int64 base_tid = -(1);
        if (py_contains(_TYPE_BASE, tid))
            base_tid = ([&]() { auto&& __dict_5 = _TYPE_BASE; auto __dict_key_6 = tid; return __dict_5.at(__dict_key_6); }());
        if ((base_tid < 0) || (!py_contains(_TYPE_BASE, base_tid)))
            roots.append(tid);
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
    while (i < children.size()) {
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
    while (i < roots.size()) {
        next_order = _assign_type_ranges_dfs(roots[i], next_order);
        i++;
    }
    list<int64> all_ids = _sorted_ints(_TYPE_IDS);
    i = 0;
    while (i < all_ids.size()) {
        int64 tid = all_ids[i];
        if (!py_contains(_TYPE_ORDER, tid))
            next_order = _assign_type_ranges_dfs(tid, next_order);
        i++;
    }
}

void _mark_type_ranges_dirty() {
    _TYPE_STATE[str("ranges_dirty")] = 1;
}

void _mark_type_ranges_clean() {
    _TYPE_STATE[str("ranges_dirty")] = 0;
}

bool _is_type_ranges_dirty() {
    return _TYPE_STATE.get(str("ranges_dirty"), 1) != 0;
}

void _ensure_type_ranges() {
    if (_is_type_ranges_dirty()) {
        _recompute_type_ranges();
        _mark_type_ranges_clean();
    }
}

void _ensure_builtins() {
    if (!py_contains(_TYPE_STATE, "next_user_type_id"))
        _TYPE_STATE[str("next_user_type_id")] = _tid_user_base();
    if (!py_contains(_TYPE_STATE, "ranges_dirty"))
        _TYPE_STATE[str("ranges_dirty")] = 1;
    if (_TYPE_IDS.size() > 0)
        return;
    _register_type_node(_tid_none(), -(1));
    _register_type_node(_tid_object(), -(1));
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

int64 _normalize_base_type_id(int64 base_type_id) {
    _ensure_builtins();
    if (!(py_runtime_value_isinstance(base_type_id, PYTRA_TID_INT)))
        throw ValueError("base type_id must be int");
    if (!py_contains(_TYPE_BASE, base_type_id))
        throw ValueError("unknown base type_id: " + ::std::to_string(base_type_id));
    return base_type_id;
}

int64 py_tid_register_class_type(int64 base_type_id) {
    /* Allocate and register a new user class type_id (single inheritance only). */
    _ensure_builtins();
    int64 base_tid = _normalize_base_type_id(base_type_id);
    
    int64 tid = ([&]() { auto&& __dict_7 = _TYPE_STATE; auto __dict_key_8 = str("next_user_type_id"); return __dict_7.at(__dict_key_8); }());
    while (py_contains(_TYPE_BASE, tid)) {
        tid++;
    }
    _TYPE_STATE[str("next_user_type_id")] = tid + 1;
    
    _register_type_node(tid, base_tid);
    _mark_type_ranges_dirty();
    return tid;
}

int64 py_tid_register_known_class_type(int64 type_id, int64 base_type_id) {
    /* Register a pre-allocated user class type_id into the canonical registry. */
    _ensure_builtins();
    if (!(py_runtime_value_isinstance(type_id, PYTRA_TID_INT)))
        throw ValueError("type_id must be int");
    if (type_id < _tid_user_base())
        throw ValueError("user type_id must be >= " + ::std::to_string(_tid_user_base()));
    int64 base_tid = _normalize_base_type_id(base_type_id);
    if (py_contains(_TYPE_BASE, type_id)) {
        if (([&]() { auto&& __dict_9 = _TYPE_BASE; auto __dict_key_10 = type_id; return __dict_9.at(__dict_key_10); }()) != base_tid)
            throw ValueError("type_id already registered with different base");
        return type_id;
    }
    _register_type_node(type_id, base_tid);
    int64 next_user_type_id = ([&]() { auto&& __dict_11 = _TYPE_STATE; auto __dict_key_12 = str("next_user_type_id"); return __dict_11.at(__dict_key_12); }());
    if (type_id >= next_user_type_id)
        _TYPE_STATE[str("next_user_type_id")] = type_id + 1;
    _mark_type_ranges_dirty();
    return type_id;
}

int64 _try_runtime_tagged_type_id(const object& value) {
    int64 tagged = py_runtime_value_type_id(value);
    if (py_runtime_value_isinstance(tagged, PYTRA_TID_INT)) {
        int64 tagged_id = tagged;
        if (py_contains(_TYPE_BASE, tagged_id))
            return tagged_id;
    }
    return -(1);
}

int64 py_tid_runtime_type_id(const object& value) {
    /* Resolve runtime type_id for a Python value. */
    _ensure_builtins();
    if (false)
        return _tid_none();
    if (py_runtime_value_isinstance(value, PYTRA_TID_BOOL))
        return _tid_bool();
    if (py_runtime_value_isinstance(value, PYTRA_TID_INT))
        return _tid_int();
    if (py_runtime_value_isinstance(value, PYTRA_TID_FLOAT))
        return _tid_float();
    if (py_runtime_value_isinstance(value, PYTRA_TID_STR))
        return _tid_str();
    if (py_runtime_value_isinstance(value, PYTRA_TID_LIST))
        return _tid_list();
    if (py_runtime_value_isinstance(value, PYTRA_TID_DICT))
        return _tid_dict();
    if (py_runtime_value_isinstance(value, PYTRA_TID_SET))
        return _tid_set();
    int64 tagged = _try_runtime_tagged_type_id(value);
    if (tagged >= 0)
        return tagged;
    return _tid_object();
}

bool py_tid_is_subtype(int64 actual_type_id, int64 expected_type_id) {
    /* Check nominal subtype relation by type_id order range. */
    _ensure_builtins();
    _ensure_type_ranges();
    if (!py_contains(_TYPE_ORDER, actual_type_id))
        return false;
    if (!py_contains(_TYPE_ORDER, expected_type_id))
        return false;
    int64 actual_order = ([&]() { auto&& __dict_13 = _TYPE_ORDER; auto __dict_key_14 = actual_type_id; return __dict_13.at(__dict_key_14); }());
    int64 expected_min = ([&]() { auto&& __dict_15 = _TYPE_MIN; auto __dict_key_16 = expected_type_id; return __dict_15.at(__dict_key_16); }());
    int64 expected_max = ([&]() { auto&& __dict_17 = _TYPE_MAX; auto __dict_key_18 = expected_type_id; return __dict_17.at(__dict_key_18); }());
    return (expected_min <= actual_order) && (actual_order <= expected_max);
}

bool py_tid_issubclass(int64 actual_type_id, int64 expected_type_id) {
    return py_tid_is_subtype(actual_type_id, expected_type_id);
}

bool py_tid_isinstance(const object& value, int64 expected_type_id) {
    return py_tid_is_subtype(py_runtime_value_type_id(value), expected_type_id);
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
    _TYPE_STATE[str("next_user_type_id")] = _tid_user_base();
    _TYPE_STATE[str("ranges_dirty")] = 1;
    _ensure_builtins();
}

#endif  // PYTRA_GEN_BUILT_IN_TYPE_ID_H
