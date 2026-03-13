// AUTO-GENERATED FILE. DO NOT EDIT.
// source: src/pytra/built_in/type_id.py
// generated-by: tools/gen_runtime_from_manifest.py

package main


func _tid_none() int64 {
    return int64(0)
}

func _tid_bool() int64 {
    return int64(1)
}

func _tid_int() int64 {
    return int64(2)
}

func _tid_float() int64 {
    return int64(3)
}

func _tid_str() int64 {
    return int64(4)
}

func _tid_list() int64 {
    return int64(5)
}

func _tid_dict() int64 {
    return int64(6)
}

func _tid_set() int64 {
    return int64(7)
}

func _tid_object() int64 {
    return int64(8)
}

func _tid_user_base() int64 {
    return int64(1000)
}

func _make_int_list_0() []any {
    var out []any = __pytra_as_list([]any{})
    return __pytra_as_list(out)
}

func _make_int_list_1(a0 int64) []any {
    var out []any = __pytra_as_list([]any{})
    out = append(out, a0)
    return __pytra_as_list(out)
}

func _contains_int(items []any, value int64) bool {
    var i int64 = int64(0)
    for (i < __pytra_len(items)) {
        if (__pytra_int(__pytra_get_index(items, i)) == value) {
            return __pytra_truthy(true)
        }
        i += int64(1)
    }
    return __pytra_truthy(false)
}

func _copy_int_list(items []any) []any {
    var out []any = __pytra_as_list([]any{})
    var i int64 = int64(0)
    for (i < __pytra_len(items)) {
        out = append(out, __pytra_int(__pytra_get_index(items, i)))
        i += int64(1)
    }
    return __pytra_as_list(out)
}

func _sorted_ints(items []any) []any {
    var out []any = __pytra_as_list(_copy_int_list(items))
    var i int64 = int64(0)
    for (i < __pytra_len(out)) {
        var j int64 = (i + int64(1))
        for (j < __pytra_len(out)) {
            if (__pytra_int(__pytra_get_index(out, j)) < __pytra_int(__pytra_get_index(out, i))) {
                var tmp int64 = __pytra_int(__pytra_get_index(out, i))
                __pytra_set_index(out, i, __pytra_int(__pytra_get_index(out, j)))
                __pytra_set_index(out, j, tmp)
            }
            j += int64(1)
        }
        i += int64(1)
    }
    return __pytra_as_list(out)
}

func _register_type_node(type_id int64, base_type_id int64) {
    if (!_contains_int(_TYPE_IDS, type_id)) {
        _TYPE_IDS = append(__pytra_as_list(_TYPE_IDS), type_id)
    }
    __pytra_set_index(_TYPE_BASE, type_id, base_type_id)
    if ((!__pytra_contains(_TYPE_CHILDREN, type_id))) {
        __pytra_set_index(_TYPE_CHILDREN, type_id, _make_int_list_0())
    }
    if (base_type_id < int64(0)) {
        return
    }
    if ((!__pytra_contains(_TYPE_CHILDREN, base_type_id))) {
        __pytra_set_index(_TYPE_CHILDREN, base_type_id, _make_int_list_0())
    }
    var children any = __pytra_get_index(_TYPE_CHILDREN, base_type_id)
    if (!_contains_int(children, type_id)) {
        children = append(__pytra_as_list(children), type_id)
        __pytra_set_index(_TYPE_CHILDREN, base_type_id, children)
    }
}

func _sorted_child_type_ids(type_id int64) []any {
    var children []any = __pytra_as_list(_make_int_list_0())
    if (__pytra_contains(_TYPE_CHILDREN, type_id)) {
        children = __pytra_as_list(__pytra_get_index(_TYPE_CHILDREN, type_id))
    }
    return __pytra_as_list(_sorted_ints(children))
}

func _collect_root_type_ids() []any {
    var roots []any = __pytra_as_list([]any{})
    var i int64 = int64(0)
    for (i < __pytra_len(_TYPE_IDS)) {
        var tid any = __pytra_get_index(_TYPE_IDS, i)
        var base_tid int64 = (-int64(1))
        if (__pytra_contains(_TYPE_BASE, tid)) {
            base_tid = __pytra_get_index(_TYPE_BASE, tid)
        }
        if ((base_tid < int64(0)) || ((!__pytra_contains(_TYPE_BASE, base_tid)))) {
            roots = append(roots, tid)
        }
        i += int64(1)
    }
    return __pytra_as_list(_sorted_ints(roots))
}

func _assign_type_ranges_dfs(type_id int64, next_order int64) int64 {
    __pytra_set_index(_TYPE_ORDER, type_id, next_order)
    __pytra_set_index(_TYPE_MIN, type_id, next_order)
    var cur int64 = (next_order + int64(1))
    var children []any = __pytra_as_list(_sorted_child_type_ids(type_id))
    var i int64 = int64(0)
    for (i < __pytra_len(children)) {
        cur = _assign_type_ranges_dfs(__pytra_int(__pytra_get_index(children, i)), cur)
        i += int64(1)
    }
    __pytra_set_index(_TYPE_MAX, type_id, (cur - int64(1)))
    return cur
}

func _recompute_type_ranges() {
    _TYPE_ORDER.clear()
    _TYPE_MIN.clear()
    _TYPE_MAX.clear()
    var next_order int64 = int64(0)
    var roots []any = __pytra_as_list(_collect_root_type_ids())
    var i int64 = int64(0)
    for (i < __pytra_len(roots)) {
        next_order = _assign_type_ranges_dfs(__pytra_int(__pytra_get_index(roots, i)), next_order)
        i += int64(1)
    }
    var all_ids []any = __pytra_as_list(_sorted_ints(_TYPE_IDS))
    i = int64(0)
    for (i < __pytra_len(all_ids)) {
        var tid int64 = __pytra_int(__pytra_get_index(all_ids, i))
        if ((!__pytra_contains(_TYPE_ORDER, tid))) {
            next_order = _assign_type_ranges_dfs(tid, next_order)
        }
        i += int64(1)
    }
}

func _mark_type_ranges_dirty() {
    __pytra_set_index(_TYPE_STATE, "ranges_dirty", int64(1))
}

func _mark_type_ranges_clean() {
    __pytra_set_index(_TYPE_STATE, "ranges_dirty", int64(0))
}

func _is_type_ranges_dirty() bool {
    return __pytra_truthy((__pytra_int(__pytra_dict_get_default(_TYPE_STATE, "ranges_dirty", int64(1))) != int64(0)))
}

func _ensure_type_ranges() {
    if _is_type_ranges_dirty() {
        _recompute_type_ranges()
        _mark_type_ranges_clean()
    }
}

func _ensure_builtins() {
    if ((!__pytra_contains(_TYPE_STATE, "next_user_type_id"))) {
        __pytra_set_index(_TYPE_STATE, "next_user_type_id", _tid_user_base())
    }
    if ((!__pytra_contains(_TYPE_STATE, "ranges_dirty"))) {
        __pytra_set_index(_TYPE_STATE, "ranges_dirty", int64(1))
    }
    if (__pytra_len(_TYPE_IDS) > int64(0)) {
        return
    }
    _register_type_node(_tid_none(), (-int64(1)))
    _register_type_node(_tid_object(), (-int64(1)))
    _register_type_node(_tid_int(), _tid_object())
    _register_type_node(_tid_bool(), _tid_int())
    _register_type_node(_tid_float(), _tid_object())
    _register_type_node(_tid_str(), _tid_object())
    _register_type_node(_tid_list(), _tid_object())
    _register_type_node(_tid_dict(), _tid_object())
    _register_type_node(_tid_set(), _tid_object())
    _recompute_type_ranges()
    _mark_type_ranges_clean()
}

func _normalize_base_type_id(base_type_id int64) int64 {
    _ensure_builtins()
    if (!false) {
        panic(__pytra_str("base type_id must be int"))
    }
    if ((!__pytra_contains(_TYPE_BASE, base_type_id))) {
        panic(__pytra_str((__pytra_str("unknown base type_id: ") + __pytra_str(__pytra_str(base_type_id)))))
    }
    return base_type_id
}

func py_tid_register_class_type(base_type_id int64) int64 {
    _ensure_builtins()
    var base_tid int64 = _normalize_base_type_id(base_type_id)
    var tid any = __pytra_get_index(_TYPE_STATE, "next_user_type_id")
    for (__pytra_contains(_TYPE_BASE, tid)) {
        tid += int64(1)
    }
    __pytra_set_index(_TYPE_STATE, "next_user_type_id", (tid + int64(1)))
    _register_type_node(tid, base_tid)
    _mark_type_ranges_dirty()
    return __pytra_int(tid)
}

func py_tid_register_known_class_type(type_id int64, base_type_id int64) int64 {
    _ensure_builtins()
    if (!false) {
        panic(__pytra_str("type_id must be int"))
    }
    if (type_id < _tid_user_base()) {
        panic(__pytra_str((__pytra_str("user type_id must be >= ") + __pytra_str(__pytra_str(_tid_user_base())))))
    }
    var base_tid int64 = _normalize_base_type_id(base_type_id)
    if (__pytra_contains(_TYPE_BASE, type_id)) {
        if (__pytra_int(__pytra_get_index(_TYPE_BASE, type_id)) != base_tid) {
            panic(__pytra_str("type_id already registered with different base"))
        }
        return type_id
    }
    _register_type_node(type_id, base_tid)
    var next_user_type_id any = __pytra_get_index(_TYPE_STATE, "next_user_type_id")
    if (type_id >= __pytra_int(next_user_type_id)) {
        __pytra_set_index(_TYPE_STATE, "next_user_type_id", (type_id + int64(1)))
    }
    _mark_type_ranges_dirty()
    return type_id
}

func _try_runtime_tagged_type_id(value *Any) int64 {
    var tagged int64 = nil
    if false {
        var tagged_id int64 = __pytra_int(tagged)
        if (__pytra_contains(_TYPE_BASE, tagged_id)) {
            return tagged_id
        }
    }
    return (-int64(1))
}

func py_tid_runtime_type_id(value *Any) int64 {
    _ensure_builtins()
    if (value == nil) {
        return _tid_none()
    }
    if false {
        return _tid_bool()
    }
    if false {
        return _tid_int()
    }
    if false {
        return _tid_float()
    }
    if false {
        return _tid_str()
    }
    if false {
        return _tid_list()
    }
    if false {
        return _tid_dict()
    }
    if false {
        return _tid_set()
    }
    var tagged int64 = _try_runtime_tagged_type_id(value)
    if (tagged >= int64(0)) {
        return tagged
    }
    return _tid_object()
}

func py_tid_is_subtype(actual_type_id int64, expected_type_id int64) bool {
    _ensure_builtins()
    _ensure_type_ranges()
    if ((!__pytra_contains(_TYPE_ORDER, actual_type_id))) {
        return __pytra_truthy(false)
    }
    if ((!__pytra_contains(_TYPE_ORDER, expected_type_id))) {
        return __pytra_truthy(false)
    }
    var actual_order any = __pytra_get_index(_TYPE_ORDER, actual_type_id)
    var expected_min any = __pytra_get_index(_TYPE_MIN, expected_type_id)
    var expected_max any = __pytra_get_index(_TYPE_MAX, expected_type_id)
    return __pytra_truthy(((expected_min <= actual_order) && (actual_order <= expected_max)))
}

func py_tid_issubclass(actual_type_id int64, expected_type_id int64) bool {
    return __pytra_truthy(nil)
}

func py_tid_isinstance(value *Any, expected_type_id int64) bool {
    return __pytra_truthy(nil)
}

func _py_reset_type_registry_for_test() {
    _TYPE_IDS.clear()
    _TYPE_BASE.clear()
    _TYPE_CHILDREN.clear()
    _TYPE_ORDER.clear()
    _TYPE_MIN.clear()
    _TYPE_MAX.clear()
    _TYPE_STATE.clear()
    __pytra_set_index(_TYPE_STATE, "next_user_type_id", _tid_user_base())
    __pytra_set_index(_TYPE_STATE, "ranges_dirty", int64(1))
    _ensure_builtins()
}
