// AUTO-GENERATED FILE. DO NOT EDIT.
// source: src/pytra/built_in/type_id.py
// generated-by: src/py2cpp.py

#ifndef PYTRA_SRC_RUNTIME_CPP_PYTRA_GEN_BUILT_IN_TYPE_ID_H
#define PYTRA_SRC_RUNTIME_CPP_PYTRA_GEN_BUILT_IN_TYPE_ID_H

extern int64 PYTRA_TID_NONE;
extern int64 PYTRA_TID_BOOL;
extern int64 PYTRA_TID_INT;
extern int64 PYTRA_TID_FLOAT;
extern int64 PYTRA_TID_STR;
extern int64 PYTRA_TID_LIST;
extern int64 PYTRA_TID_DICT;
extern int64 PYTRA_TID_SET;
extern int64 PYTRA_TID_OBJECT;
extern int64 PYTRA_TID_USER_BASE;
extern dict<int64, list<int64>> _TYPE_BASES;
extern dict<str, int64> _TYPE_STATE;

bool _contains_int(const list<int64>& items, int64 value);
void _ensure_builtins();
list<int64> _normalize_base_type_ids(const list<int64>& base_type_ids);
int64 py_register_class_type(const list<int64>& base_type_ids);
int64 py_runtime_type_id(const object& value);
bool py_is_subtype(int64 actual_type_id, int64 expected_type_id);
bool py_issubclass(int64 actual_type_id, int64 expected_type_id);
bool py_isinstance(const object& value, int64 expected_type_id);
void _py_reset_type_registry_for_test();

#endif  // PYTRA_SRC_RUNTIME_CPP_PYTRA_GEN_BUILT_IN_TYPE_ID_H
