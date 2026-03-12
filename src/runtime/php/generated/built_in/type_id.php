<?php
// AUTO-GENERATED FILE. DO NOT EDIT.
// source: src/pytra/built_in/type_id.py
// generated-by: tools/gen_runtime_from_manifest.py

declare(strict_types=1);

$__pytra_runtime_candidates = [
    dirname(__DIR__) . '/py_runtime.php',
    dirname(__DIR__, 2) . '/native/built_in/py_runtime.php',
];
foreach ($__pytra_runtime_candidates as $__pytra_runtime_path) {
    if (is_file($__pytra_runtime_path)) {
        require_once $__pytra_runtime_path;
        break;
    }
}
if (!function_exists('__pytra_len')) {
    throw new RuntimeException('py_runtime.php not found for generated PHP runtime lane');
}

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
    $out = [];
    return $out;
}

function _make_int_list_1($a0) {
    $out = [];
    $out[] = $a0;
    return $out;
}

function _contains_int($items, $value) {
    $i = 0;
    while (($i < __pytra_len($items))) {
        if (($items[__pytra_index($items, $i)] == $value)) {
            return true;
        }
        $i += 1;
    }
    return false;
}

function _copy_int_list($items) {
    $out = [];
    $i = 0;
    while (($i < __pytra_len($items))) {
        $out[] = $items[__pytra_index($items, $i)];
        $i += 1;
    }
    return $out;
}

function _sorted_ints($items) {
    $out = _copy_int_list($items);
    $i = 0;
    while (($i < __pytra_len($out))) {
        $j = ($i + 1);
        while (($j < __pytra_len($out))) {
            if (($out[__pytra_index($out, $j)] < $out[__pytra_index($out, $i)])) {
                $tmp = $out[__pytra_index($out, $i)];
                $out[__pytra_index($out, $i)] = $out[__pytra_index($out, $j)];
                $out[__pytra_index($out, $j)] = $tmp;
            }
            $j += 1;
        }
        $i += 1;
    }
    return $out;
}

function _register_type_node($type_id, $base_type_id) {
    if ((!_contains_int($_TYPE_IDS, $type_id))) {
        $_TYPE_IDS[] = $type_id;
    }
    $_TYPE_BASE[$type_id] = $base_type_id;
    if ((!__pytra_contains($_TYPE_CHILDREN, $type_id))) {
        $_TYPE_CHILDREN[$type_id] = _make_int_list_0();
    }
    if (($base_type_id < 0)) {
        return;
    }
    if ((!__pytra_contains($_TYPE_CHILDREN, $base_type_id))) {
        $_TYPE_CHILDREN[$base_type_id] = _make_int_list_0();
    }
    $children = $_TYPE_CHILDREN[$base_type_id];
    if ((!_contains_int($children, $type_id))) {
        $children[] = $type_id;
        $_TYPE_CHILDREN[$base_type_id] = $children;
    }
}

function _sorted_child_type_ids($type_id) {
    $children = _make_int_list_0();
    if ((__pytra_contains($_TYPE_CHILDREN, $type_id))) {
        $children = $_TYPE_CHILDREN[$type_id];
    }
    return _sorted_ints($children);
}

function _collect_root_type_ids() {
    $roots = [];
    $i = 0;
    while (($i < __pytra_len($_TYPE_IDS))) {
        $tid = $_TYPE_IDS[$i];
        $base_tid = (-1);
        if ((__pytra_contains($_TYPE_BASE, $tid))) {
            $base_tid = $_TYPE_BASE[$tid];
        }
        if ((($base_tid < 0) || (!__pytra_contains($_TYPE_BASE, $base_tid)))) {
            $roots[] = $tid;
        }
        $i += 1;
    }
    return _sorted_ints($roots);
}

function _assign_type_ranges_dfs($type_id, $next_order) {
    $_TYPE_ORDER[$type_id] = $next_order;
    $_TYPE_MIN[$type_id] = $next_order;
    $cur = ($next_order + 1);
    $children = _sorted_child_type_ids($type_id);
    $i = 0;
    while (($i < __pytra_len($children))) {
        $cur = _assign_type_ranges_dfs($children[__pytra_index($children, $i)], $cur);
        $i += 1;
    }
    $_TYPE_MAX[$type_id] = ($cur - 1);
    return $cur;
}

function _recompute_type_ranges() {
    $_TYPE_ORDER->clear();
    $_TYPE_MIN->clear();
    $_TYPE_MAX->clear();
    $next_order = 0;
    $roots = _collect_root_type_ids();
    $i = 0;
    while (($i < __pytra_len($roots))) {
        $next_order = _assign_type_ranges_dfs($roots[__pytra_index($roots, $i)], $next_order);
        $i += 1;
    }
    $all_ids = _sorted_ints($_TYPE_IDS);
    $i = 0;
    while (($i < __pytra_len($all_ids))) {
        $tid = $all_ids[__pytra_index($all_ids, $i)];
        if ((!__pytra_contains($_TYPE_ORDER, $tid))) {
            $next_order = _assign_type_ranges_dfs($tid, $next_order);
        }
        $i += 1;
    }
}

function _mark_type_ranges_dirty() {
    $_TYPE_STATE["ranges_dirty"] = 1;
}

function _mark_type_ranges_clean() {
    $_TYPE_STATE["ranges_dirty"] = 0;
}

function _is_type_ranges_dirty() {
    return (($_TYPE_STATE["ranges_dirty"] ?? 1) != 0);
}

function _ensure_type_ranges() {
    if (_is_type_ranges_dirty()) {
        _recompute_type_ranges();
        _mark_type_ranges_clean();
    }
}

function _ensure_builtins() {
    if ((!__pytra_contains($_TYPE_STATE, "next_user_type_id"))) {
        $_TYPE_STATE["next_user_type_id"] = _tid_user_base();
    }
    if ((!__pytra_contains($_TYPE_STATE, "ranges_dirty"))) {
        $_TYPE_STATE["ranges_dirty"] = 1;
    }
    if ((__pytra_len($_TYPE_IDS) > 0)) {
        return;
    }
    _register_type_node(_tid_none(), (-1));
    _register_type_node(_tid_object(), (-1));
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

function _normalize_base_type_id($base_type_id) {
    _ensure_builtins();
    if ((!($base_type_id instanceof PYTRA_TID_INT))) {
        throw new Exception(strval(ValueError("base type_id must be int")));
    }
    if ((!__pytra_contains($_TYPE_BASE, $base_type_id))) {
        throw new Exception(strval(ValueError(("unknown base type_id: " . strval($base_type_id)))));
    }
    return $base_type_id;
}

function py_tid_register_class_type($base_type_id) {
    _ensure_builtins();
    $base_tid = _normalize_base_type_id($base_type_id);
    $tid = $_TYPE_STATE["next_user_type_id"];
    while ((__pytra_contains($_TYPE_BASE, $tid))) {
        $tid += 1;
    }
    $_TYPE_STATE["next_user_type_id"] = ($tid + 1);
    _register_type_node($tid, $base_tid);
    _mark_type_ranges_dirty();
    return $tid;
}

function py_tid_register_known_class_type($type_id, $base_type_id) {
    _ensure_builtins();
    if ((!($type_id instanceof PYTRA_TID_INT))) {
        throw new Exception(strval(ValueError("type_id must be int")));
    }
    if (($type_id < _tid_user_base())) {
        throw new Exception(strval(ValueError(("user type_id must be >= " . strval(_tid_user_base())))));
    }
    $base_tid = _normalize_base_type_id($base_type_id);
    if ((__pytra_contains($_TYPE_BASE, $type_id))) {
        if (($_TYPE_BASE[$type_id] != $base_tid)) {
            throw new Exception(strval(ValueError("type_id already registered with different base")));
        }
        return $type_id;
    }
    _register_type_node($type_id, $base_tid);
    $next_user_type_id = $_TYPE_STATE["next_user_type_id"];
    if (($type_id >= $next_user_type_id)) {
        $_TYPE_STATE["next_user_type_id"] = ($type_id + 1);
    }
    _mark_type_ranges_dirty();
    return $type_id;
}

function _try_runtime_tagged_type_id($value) {
    $tagged = null;
    if (($tagged instanceof PYTRA_TID_INT)) {
        $tagged_id = ((int)($tagged));
        if ((__pytra_contains($_TYPE_BASE, $tagged_id))) {
            return $tagged_id;
        }
    }
    return (-1);
}

function py_tid_runtime_type_id($value) {
    _ensure_builtins();
    if (($value == null)) {
        return _tid_none();
    }
    if (($value instanceof PYTRA_TID_BOOL)) {
        return _tid_bool();
    }
    if (($value instanceof PYTRA_TID_INT)) {
        return _tid_int();
    }
    if (($value instanceof PYTRA_TID_FLOAT)) {
        return _tid_float();
    }
    if (($value instanceof PYTRA_TID_STR)) {
        return _tid_str();
    }
    if (($value instanceof PYTRA_TID_LIST)) {
        return _tid_list();
    }
    if (($value instanceof PYTRA_TID_DICT)) {
        return _tid_dict();
    }
    if (($value instanceof PYTRA_TID_SET)) {
        return _tid_set();
    }
    $tagged = _try_runtime_tagged_type_id($value);
    if (($tagged >= 0)) {
        return $tagged;
    }
    return _tid_object();
}

function py_tid_is_subtype($actual_type_id, $expected_type_id) {
    _ensure_builtins();
    _ensure_type_ranges();
    if ((!__pytra_contains($_TYPE_ORDER, $actual_type_id))) {
        return false;
    }
    if ((!__pytra_contains($_TYPE_ORDER, $expected_type_id))) {
        return false;
    }
    $actual_order = $_TYPE_ORDER[$actual_type_id];
    $expected_min = $_TYPE_MIN[$expected_type_id];
    $expected_max = $_TYPE_MAX[$expected_type_id];
    return (($expected_min <= $actual_order) && ($actual_order <= $expected_max));
}

function py_tid_issubclass($actual_type_id, $expected_type_id) {
    return null;
}

function py_tid_isinstance($value, $expected_type_id) {
    return null;
}

function _py_reset_type_registry_for_test() {
    $_TYPE_IDS->clear();
    $_TYPE_BASE->clear();
    $_TYPE_CHILDREN->clear();
    $_TYPE_ORDER->clear();
    $_TYPE_MIN->clear();
    $_TYPE_MAX->clear();
    $_TYPE_STATE->clear();
    $_TYPE_STATE["next_user_type_id"] = _tid_user_base();
    $_TYPE_STATE["ranges_dirty"] = 1;
    _ensure_builtins();
}
