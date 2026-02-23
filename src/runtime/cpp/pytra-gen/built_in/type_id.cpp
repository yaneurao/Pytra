// AUTO-GENERATED FILE. DO NOT EDIT.
// source: src/pytra/built_in/type_id.py
// generated-by: src/py2cpp.py
#include "runtime/cpp/pytra/built_in/py_runtime.h"

#include "pytra/built_in/type_id.h"

#include "pytra/std/typing.h"

int64 PYB_TID_NONE;
int64 PYB_TID_BOOL;
int64 PYB_TID_INT;
int64 PYB_TID_FLOAT;
int64 PYB_TID_STR;
int64 PYB_TID_LIST;
int64 PYB_TID_DICT;
int64 PYB_TID_SET;
int64 PYB_TID_OBJECT;
int64 PYB_TID_USER_BASE;
dict<int64, list<int64>> _TYPE_BASES;
dict<str, int64> _TYPE_STATE;


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
    if (py_len(_TYPE_BASES) > 0)
        return;
    _TYPE_BASES[PYB_TID_NONE] = _make_int_list_0();
    _TYPE_BASES[PYB_TID_OBJECT] = _make_int_list_0();
    _TYPE_BASES[PYB_TID_BOOL] = _make_int_list_2(PYB_TID_INT, PYB_TID_OBJECT);
    _TYPE_BASES[PYB_TID_INT] = _make_int_list_1(PYB_TID_OBJECT);
    _TYPE_BASES[PYB_TID_FLOAT] = _make_int_list_1(PYB_TID_OBJECT);
    _TYPE_BASES[PYB_TID_STR] = _make_int_list_1(PYB_TID_OBJECT);
    _TYPE_BASES[PYB_TID_LIST] = _make_int_list_1(PYB_TID_OBJECT);
    _TYPE_BASES[PYB_TID_DICT] = _make_int_list_1(PYB_TID_OBJECT);
    _TYPE_BASES[PYB_TID_SET] = _make_int_list_1(PYB_TID_OBJECT);
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
        out.append(int64(PYB_TID_OBJECT));
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
        return PYB_TID_NONE;
    if (py_isinstance(value, PYTRA_TID_BOOL))
        return PYB_TID_BOOL;
    if (py_isinstance(value, PYTRA_TID_INT))
        return PYB_TID_INT;
    if (py_isinstance(value, PYTRA_TID_FLOAT))
        return PYB_TID_FLOAT;
    if (py_isinstance(value, PYTRA_TID_STR))
        return PYB_TID_STR;
    if (py_isinstance(value, PYTRA_TID_LIST))
        return PYB_TID_LIST;
    if (py_isinstance(value, PYTRA_TID_DICT))
        return PYB_TID_DICT;
    if (py_isinstance(value, PYTRA_TID_SET))
        return PYB_TID_SET;
    return PYB_TID_OBJECT;
}

bool py_tid_is_subtype(int64 actual_type_id, int64 expected_type_id) {
    /* Check nominal subtype relation by walking base type graph. */
    _ensure_builtins();
    if (actual_type_id == expected_type_id)
        return true;
    if ((expected_type_id == PYB_TID_OBJECT) && (actual_type_id != PYB_TID_NONE))
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
    _TYPE_STATE["next_user_type_id"] = PYB_TID_USER_BASE;
    _ensure_builtins();
}

static void __pytra_module_init() {
    static bool __initialized = false;
    if (__initialized) return;
    __initialized = true;
    /* Pure-Python source-of-truth for type_id based subtype/isinstance semantics. */
    PYB_TID_NONE = 0;
    PYB_TID_BOOL = 1;
    PYB_TID_INT = 2;
    PYB_TID_FLOAT = 3;
    PYB_TID_STR = 4;
    PYB_TID_LIST = 5;
    PYB_TID_DICT = 6;
    PYB_TID_SET = 7;
    PYB_TID_OBJECT = 8;
    PYB_TID_USER_BASE = 1000;
    _TYPE_BASES = dict<int64, list<int64>>{};
    _TYPE_STATE = dict<str, int64>{{"next_user_type_id", PYB_TID_USER_BASE}};
}
