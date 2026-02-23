// AUTO-GENERATED FILE. DO NOT EDIT.
// source: src/pytra/built_in/type_id.py
// generated-by: src/py2cpp.py
#include "runtime/cpp/pytra/built_in/py_runtime.h"

#include "pytra/built_in/type_id.h"

#include "pytra/std/typing.h"

dict<int64, list<int64>> _TYPE_BASES;
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

list<int64> _make_int_list_2(int64 a0, int64 a1) {
    list<int64> out = list<int64>{};
    out.append(int64(a0));
    out.append(int64(a1));
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

void _ensure_builtins() {
    if (!py_contains(_TYPE_STATE, "next_user_type_id"))
        _TYPE_STATE["next_user_type_id"] = _tid_user_base();
    if (py_len(_TYPE_BASES) > 0)
        return;
    _TYPE_BASES[_tid_none()] = _make_int_list_0();
    _TYPE_BASES[_tid_object()] = _make_int_list_0();
    _TYPE_BASES[_tid_bool()] = _make_int_list_2(_tid_int(), _tid_object());
    _TYPE_BASES[_tid_int()] = _make_int_list_1(_tid_object());
    _TYPE_BASES[_tid_float()] = _make_int_list_1(_tid_object());
    _TYPE_BASES[_tid_str()] = _make_int_list_1(_tid_object());
    _TYPE_BASES[_tid_list()] = _make_int_list_1(_tid_object());
    _TYPE_BASES[_tid_dict()] = _make_int_list_1(_tid_object());
    _TYPE_BASES[_tid_set()] = _make_int_list_1(_tid_object());
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
    return out;
}

int64 py_tid_register_class_type(const list<int64>& base_type_ids) {
    /* Allocate and register a new user class type_id. */
    _ensure_builtins();
    auto tid = py_dict_get(_TYPE_STATE, "next_user_type_id");
    _TYPE_STATE["next_user_type_id"] = tid + 1;
    _TYPE_BASES[tid] = _normalize_base_type_ids(base_type_ids);
    return tid;
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
    return _tid_object();
}

bool py_tid_is_subtype(int64 actual_type_id, int64 expected_type_id) {
    /* Check nominal subtype relation by walking base type graph. */
    _ensure_builtins();
    if (actual_type_id == expected_type_id)
        return true;
    if ((expected_type_id == _tid_object()) && (actual_type_id != _tid_none()))
        return true;
    list<int64> stack = _make_int_list_1(actual_type_id);
    list<int64> visited = _make_int_list_0();
    while (py_len(stack) > 0) {
        auto cur = stack.pop();
        if (cur == expected_type_id)
            return true;
        if (_contains_int(visited, cur))
            continue;
        visited.append(int64(cur));
        list<int64> bases = _make_int_list_0();
        if (py_contains(_TYPE_BASES, cur))
            bases = _TYPE_BASES[cur];
        int64 i = 0;
        while (i < py_len(bases)) {
            int64 base_tid = bases[i];
            if (!(_contains_int(visited, base_tid)))
                stack.append(int64(base_tid));
            i++;
        }
    }
    return false;
}

bool py_tid_issubclass(int64 actual_type_id, int64 expected_type_id) {
    return py_tid_is_subtype(actual_type_id, expected_type_id);
}

bool py_tid_isinstance(const object& value, int64 expected_type_id) {
    return py_tid_is_subtype(py_tid_runtime_type_id(value), expected_type_id);
}

void _py_reset_type_registry_for_test() {
    /* Reset mutable registry state for deterministic unit tests. */
    _TYPE_BASES.clear();
    _TYPE_STATE["next_user_type_id"] = _tid_user_base();
    _ensure_builtins();
}

static void __pytra_module_init() {
    static bool __initialized = false;
    if (__initialized) return;
    __initialized = true;
    /* Pure-Python source-of-truth for type_id based subtype/isinstance semantics. */
    _TYPE_BASES = dict<int64, list<int64>>{};
    _TYPE_STATE = dict<str, int64>{};
}
