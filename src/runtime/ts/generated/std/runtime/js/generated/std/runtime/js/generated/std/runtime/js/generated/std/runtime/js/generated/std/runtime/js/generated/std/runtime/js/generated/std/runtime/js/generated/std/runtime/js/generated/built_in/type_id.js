// AUTO-GENERATED FILE. DO NOT EDIT.
// source: src/pytra/built_in/type_id.py
// generated-by: tools/gen_runtime_from_manifest.py

const {PYTRA_TYPE_ID, PY_TYPE_BOOL, PY_TYPE_NUMBER, PY_TYPE_STRING, PY_TYPE_ARRAY, PY_TYPE_MAP, PY_TYPE_SET, pyIsInstance, pyIsSubtype, pyLen, pyTypeId} = require("../../native/built_in/py_runtime.js");

function _tid_none() {
    return 0;
}

function _tid_bool() {
    return 1;
}

function _tid_int() {
    return 2;
}

function _tid_float() {
    return 3;
}

function _tid_str() {
    return 4;
}

function _tid_list() {
    return 5;
}

function _tid_dict() {
    return 6;
}

function _tid_set() {
    return 7;
}

function _tid_object() {
    return 8;
}

function _tid_user_base() {
    return 1000;
}

function _make_int_list_0() {
    let out = [];
    return out;
}

function _make_int_list_1(a0) {
    let out = [];
    out.push(a0);
    return out;
}

function _contains_int(items, value) {
    let i = 0;
    while (i < (items).length) {
        if (items[(((i) < 0) ? ((items).length + (i)) : (i))] === value) {
            return true;
        }
        i += 1;
    }
    return false;
}

function _copy_int_list(items) {
    let out = [];
    let i = 0;
    while (i < (items).length) {
        out.push(items[(((i) < 0) ? ((items).length + (i)) : (i))]);
        i += 1;
    }
    return out;
}

function _sorted_ints(items) {
    let out = _copy_int_list(items);
    let i = 0;
    while (i < (out).length) {
        let j = i + 1;
        while (j < (out).length) {
            if (out[(((j) < 0) ? ((out).length + (j)) : (j))] < out[(((i) < 0) ? ((out).length + (i)) : (i))]) {
                let tmp = out[(((i) < 0) ? ((out).length + (i)) : (i))];
                out[(((i) < 0) ? ((out).length + (i)) : (i))] = out[(((j) < 0) ? ((out).length + (j)) : (j))];
                out[(((j) < 0) ? ((out).length + (j)) : (j))] = tmp;
            }
            j += 1;
        }
        i += 1;
    }
    return out;
}

function _register_type_node(type_id, base_type_id) {
    if (!_contains_int(_TYPE_IDS, type_id)) {
        _TYPE_IDS.append(type_id);
    }
    _TYPE_BASE[type_id] = base_type_id;
    if (!((type_id in _TYPE_CHILDREN))) {
        _TYPE_CHILDREN[type_id] = _make_int_list_0();
    }
    if (base_type_id < 0) {
        return;
    }
    if (!((base_type_id in _TYPE_CHILDREN))) {
        _TYPE_CHILDREN[base_type_id] = _make_int_list_0();
    }
    let children = _TYPE_CHILDREN[base_type_id];
    if (!_contains_int(children, type_id)) {
        children.append(type_id);
        _TYPE_CHILDREN[base_type_id] = children;
    }
}

function _sorted_child_type_ids(type_id) {
    let children = _make_int_list_0();
    if (type_id in _TYPE_CHILDREN) {
        children = _TYPE_CHILDREN[type_id];
    }
    return _sorted_ints(children);
}

function _collect_root_type_ids() {
    let roots = [];
    let i = 0;
    while (i < pyLen(_TYPE_IDS)) {
        let tid = _TYPE_IDS[i];
        let base_tid = -1;
        if (tid in _TYPE_BASE) {
            base_tid = _TYPE_BASE[tid];
        }
        if (base_tid < 0 || !((base_tid in _TYPE_BASE))) {
            roots.push(tid);
        }
        i += 1;
    }
    return _sorted_ints(roots);
}

function _assign_type_ranges_dfs(type_id, next_order) {
    _TYPE_ORDER[type_id] = next_order;
    _TYPE_MIN[type_id] = next_order;
    let cur = next_order + 1;
    let children = _sorted_child_type_ids(type_id);
    let i = 0;
    while (i < (children).length) {
        cur = _assign_type_ranges_dfs(children[(((i) < 0) ? ((children).length + (i)) : (i))], cur);
        i += 1;
    }
    _TYPE_MAX[type_id] = cur - 1;
    return cur;
}

function _recompute_type_ranges() {
    _TYPE_ORDER.clear();
    _TYPE_MIN.clear();
    _TYPE_MAX.clear();
    
    let next_order = 0;
    let roots = _collect_root_type_ids();
    let i = 0;
    while (i < (roots).length) {
        next_order = _assign_type_ranges_dfs(roots[(((i) < 0) ? ((roots).length + (i)) : (i))], next_order);
        i += 1;
    }
    let all_ids = _sorted_ints(_TYPE_IDS);
    i = 0;
    while (i < (all_ids).length) {
        let tid = all_ids[(((i) < 0) ? ((all_ids).length + (i)) : (i))];
        if (!((tid in _TYPE_ORDER))) {
            next_order = _assign_type_ranges_dfs(tid, next_order);
        }
        i += 1;
    }
}

function _mark_type_ranges_dirty() {
    _TYPE_STATE["ranges_dirty"] = 1;
}

function _mark_type_ranges_clean() {
    _TYPE_STATE["ranges_dirty"] = 0;
}

function _is_type_ranges_dirty() {
    return _TYPE_STATE.get("ranges_dirty", 1) !== 0;
}

function _ensure_type_ranges() {
    if (_is_type_ranges_dirty()) {
        _recompute_type_ranges();
        _mark_type_ranges_clean();
    }
}

function _ensure_builtins() {
    if (!(("next_user_type_id" in _TYPE_STATE))) {
        _TYPE_STATE["next_user_type_id"] = _tid_user_base();
    }
    if (!(("ranges_dirty" in _TYPE_STATE))) {
        _TYPE_STATE["ranges_dirty"] = 1;
    }
    if (pyLen(_TYPE_IDS) > 0) {
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

function _normalize_base_type_id(base_type_id) {
    _ensure_builtins();
    if (!(pyIsInstance(base_type_id, PY_TYPE_NUMBER))) {
        throw new Error("base type_id must be int");
    }
    if (!((base_type_id in _TYPE_BASE))) {
        throw new Error("unknown base type_id: " + String(base_type_id));
    }
    return base_type_id;
}

function py_tid_register_class_type(base_type_id) {
    _ensure_builtins();
    let base_tid = _normalize_base_type_id(base_type_id);
    
    let tid = _TYPE_STATE["next_user_type_id"];
    while (tid in _TYPE_BASE) {
        tid += 1;
    }
    _TYPE_STATE["next_user_type_id"] = tid + 1;
    
    _register_type_node(tid, base_tid);
    _mark_type_ranges_dirty();
    return tid;
}

function py_tid_register_known_class_type(type_id, base_type_id) {
    _ensure_builtins();
    if (!(pyIsInstance(type_id, PY_TYPE_NUMBER))) {
        throw new Error("type_id must be int");
    }
    if (type_id < _tid_user_base()) {
        throw new Error("user type_id must be >= " + String(_tid_user_base()));
    }
    let base_tid = _normalize_base_type_id(base_type_id);
    if (type_id in _TYPE_BASE) {
        if (_TYPE_BASE[type_id] !== base_tid) {
            throw new Error("type_id already registered with different base");
        }
        return type_id;
    }
    _register_type_node(type_id, base_tid);
    let next_user_type_id = _TYPE_STATE["next_user_type_id"];
    if (type_id >= next_user_type_id) {
        _TYPE_STATE["next_user_type_id"] = type_id + 1;
    }
    _mark_type_ranges_dirty();
    return type_id;
}

function _try_runtime_tagged_type_id(value) {
    let tagged = pyTypeId(value);
    if (pyIsInstance(tagged, PY_TYPE_NUMBER)) {
        let tagged_id = Math.trunc(Number(tagged));
        if (tagged_id in _TYPE_BASE) {
            return tagged_id;
        }
    }
    return -1;
}

function py_tid_runtime_type_id(value) {
    _ensure_builtins();
    if (value === null) {
        return _tid_none();
    }
    if (pyIsInstance(value, PY_TYPE_BOOL)) {
        return _tid_bool();
    }
    if (pyIsInstance(value, PY_TYPE_NUMBER)) {
        return _tid_int();
    }
    if (pyIsInstance(value, PY_TYPE_NUMBER)) {
        return _tid_float();
    }
    if (pyIsInstance(value, PY_TYPE_STRING)) {
        return _tid_str();
    }
    if (pyIsInstance(value, PY_TYPE_ARRAY)) {
        return _tid_list();
    }
    if (pyIsInstance(value, PY_TYPE_MAP)) {
        return _tid_dict();
    }
    if (pyIsInstance(value, PY_TYPE_SET)) {
        return _tid_set();
    }
    let tagged = _try_runtime_tagged_type_id(value);
    if (tagged >= 0) {
        return tagged;
    }
    return _tid_object();
}

function py_tid_is_subtype(actual_type_id, expected_type_id) {
    _ensure_builtins();
    _ensure_type_ranges();
    if (!((actual_type_id in _TYPE_ORDER))) {
        return false;
    }
    if (!((expected_type_id in _TYPE_ORDER))) {
        return false;
    }
    let actual_order = _TYPE_ORDER[actual_type_id];
    let expected_min = _TYPE_MIN[expected_type_id];
    let expected_max = _TYPE_MAX[expected_type_id];
    return expected_min <= actual_order && actual_order <= expected_max;
}

function py_tid_issubclass(actual_type_id, expected_type_id) {
    return pyIsSubtype(actual_type_id, expected_type_id);
}

function py_tid_isinstance(value, expected_type_id) {
    return pyIsSubtype(pyTypeId(value), expected_type_id);
}

function _py_reset_type_registry_for_test() {
    _TYPE_IDS.clear();
    _TYPE_BASE.clear();
    _TYPE_CHILDREN.clear();
    _TYPE_ORDER.clear();
    _TYPE_MIN.clear();
    _TYPE_MAX.clear();
    _TYPE_STATE.clear();
    _TYPE_STATE["next_user_type_id"] = _tid_user_base();
    _TYPE_STATE["ranges_dirty"] = 1;
    _ensure_builtins();
}

"Pure-Python source-of-truth for single-inheritance type_id range semantics.";
let _TYPE_IDS = [];
let _TYPE_BASE = ({[PYTRA_TYPE_ID]: PY_TYPE_MAP});
let _TYPE_CHILDREN = ({[PYTRA_TYPE_ID]: PY_TYPE_MAP});
let _TYPE_ORDER = ({[PYTRA_TYPE_ID]: PY_TYPE_MAP});
let _TYPE_MIN = ({[PYTRA_TYPE_ID]: PY_TYPE_MAP});
let _TYPE_MAX = ({[PYTRA_TYPE_ID]: PY_TYPE_MAP});
let _TYPE_STATE = ({[PYTRA_TYPE_ID]: PY_TYPE_MAP});

module.exports = {py_tid_register_class_type, py_tid_register_known_class_type, py_tid_runtime_type_id, py_tid_is_subtype, py_tid_issubclass, py_tid_isinstance};
