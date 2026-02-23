// AUTO-GENERATED FILE. DO NOT EDIT.
// source: src/pytra/built_in/type_id.py
// generated-by: src/py2cpp.py
#include "runtime/cpp/pytra/built_in/py_runtime.h"

#include "pytra/built_in/type_id.h"

#include "pytra/std/typing.h"

int64 PYTRA_TID_NONE;
int64 PYTRA_TID_BOOL;
int64 PYTRA_TID_INT;
int64 PYTRA_TID_FLOAT;
int64 PYTRA_TID_STR;
int64 PYTRA_TID_LIST;
int64 PYTRA_TID_DICT;
int64 PYTRA_TID_SET;
int64 PYTRA_TID_OBJECT;
int64 PYTRA_TID_USER_BASE;
dict<int64, list<int64>> _TYPE_BASES;
dict<str, int64> _TYPE_STATE;


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
    _TYPE_BASES[PYTRA_TID_NONE] = list<object>{};
    _TYPE_BASES[PYTRA_TID_OBJECT] = list<object>{};
    _TYPE_BASES[PYTRA_TID_BOOL] = list<object>{make_object(PYTRA_TID_INT), make_object(PYTRA_TID_OBJECT)};
    _TYPE_BASES[PYTRA_TID_INT] = list<object>{make_object(PYTRA_TID_OBJECT)};
    _TYPE_BASES[PYTRA_TID_FLOAT] = list<object>{make_object(PYTRA_TID_OBJECT)};
    _TYPE_BASES[PYTRA_TID_STR] = list<object>{make_object(PYTRA_TID_OBJECT)};
    _TYPE_BASES[PYTRA_TID_LIST] = list<object>{make_object(PYTRA_TID_OBJECT)};
    _TYPE_BASES[PYTRA_TID_DICT] = list<object>{make_object(PYTRA_TID_OBJECT)};
    _TYPE_BASES[PYTRA_TID_SET] = list<object>{make_object(PYTRA_TID_OBJECT)};
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
        out.append(int64(PYTRA_TID_OBJECT));
    return out;
}

int64 py_register_class_type(const list<int64>& base_type_ids) {
    /* Allocate and register a new user class type_id. */
    _ensure_builtins();
    auto tid = py_dict_get(_TYPE_STATE, "next_user_type_id");
    _TYPE_STATE["next_user_type_id"] = tid + 1;
    _TYPE_BASES[tid] = _normalize_base_type_ids(base_type_ids);
    return tid;
}

int64 py_runtime_type_id(const object& value) {
    /* Resolve runtime type_id for a Python value. */
    _ensure_builtins();
    if (py_is_none(value))
        return PYTRA_TID_NONE;
    if (py_isinstance(value, PYTRA_TID_BOOL))
        return PYTRA_TID_BOOL;
    if (py_isinstance(value, PYTRA_TID_INT))
        return PYTRA_TID_INT;
    if (py_isinstance(value, PYTRA_TID_FLOAT))
        return PYTRA_TID_FLOAT;
    if (py_isinstance(value, PYTRA_TID_STR))
        return PYTRA_TID_STR;
    if (py_isinstance(value, PYTRA_TID_LIST))
        return PYTRA_TID_LIST;
    if (py_isinstance(value, PYTRA_TID_DICT))
        return PYTRA_TID_DICT;
    if (py_isinstance(value, PYTRA_TID_SET))
        return PYTRA_TID_SET;
    auto py_type_id = getattr(value, "py_type_id", ::std::nullopt);
    if (py_isinstance(py_type_id, PYTRA_TID_INT))
        return py_type_id;
    auto cls_type_id = getattr(type(value), "PYTRA_TYPE_ID", ::std::nullopt);
    if (py_isinstance(cls_type_id, PYTRA_TID_INT))
        return cls_type_id;
    return PYTRA_TID_OBJECT;
}

bool py_is_subtype(int64 actual_type_id, int64 expected_type_id) {
    /* Check nominal subtype relation by walking base type graph. */
    _ensure_builtins();
    if (actual_type_id == expected_type_id)
        return true;
    if ((expected_type_id == PYTRA_TID_OBJECT) && (actual_type_id != PYTRA_TID_NONE))
        return true;
    list<int64> stack = list<int64>{actual_type_id};
    list<int64> visited = list<int64>{};
    while (py_len(stack) > 0) {
        auto cur = stack.pop();
        if (cur == expected_type_id)
            return true;
        if (_contains_int(visited, cur))
            continue;
        visited.append(int64(cur));
        auto bases = (py_contains(_TYPE_BASES, cur) ? _TYPE_BASES[cur] : list<object>{});
        int64 i = 0;
        while (i < py_len(bases)) {
            auto base_tid = py_at(bases, py_to_int64(i));
            if (!(_contains_int(visited, base_tid)))
                stack.append(int64(base_tid));
            i++;
        }
    }
    return false;
}

bool py_issubclass(int64 actual_type_id, int64 expected_type_id) {
    return py_is_subtype(actual_type_id, expected_type_id);
}

bool py_isinstance(const object& value, int64 expected_type_id) {
    return py_is_subtype(py_runtime_type_id(value), expected_type_id);
}

void _py_reset_type_registry_for_test() {
    /* Reset mutable registry state for deterministic unit tests. */
    _TYPE_BASES.clear();
    _TYPE_STATE["next_user_type_id"] = PYTRA_TID_USER_BASE;
    _ensure_builtins();
}

static void __pytra_module_init() {
    static bool __initialized = false;
    if (__initialized) return;
    __initialized = true;
    /* Pure-Python source-of-truth for type_id based subtype/isinstance semantics. */
    PYTRA_TID_NONE = 0;
    PYTRA_TID_BOOL = 1;
    PYTRA_TID_INT = 2;
    PYTRA_TID_FLOAT = 3;
    PYTRA_TID_STR = 4;
    PYTRA_TID_LIST = 5;
    PYTRA_TID_DICT = 6;
    PYTRA_TID_SET = 7;
    PYTRA_TID_OBJECT = 8;
    PYTRA_TID_USER_BASE = 1000;
    _TYPE_BASES = dict<int64, list<int64>>{};
    _TYPE_STATE = dict<str, int64>{{"next_user_type_id", PYTRA_TID_USER_BASE}};
}
