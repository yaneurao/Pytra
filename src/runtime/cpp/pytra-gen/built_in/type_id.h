// AUTO-GENERATED FILE. DO NOT EDIT.
// source: src/pytra/built_in/type_id.py
// generated-by: src/py2cpp.py

#ifndef PYTRA_SRC_RUNTIME_CPP_PYTRA_GEN_BUILT_IN_TYPE_ID_H
#define PYTRA_SRC_RUNTIME_CPP_PYTRA_GEN_BUILT_IN_TYPE_ID_H

extern list<int64> _TYPE_IDS;
extern dict<int64, int64> _TYPE_BASE;
extern dict<int64, list<int64>> _TYPE_CHILDREN;
extern dict<int64, int64> _TYPE_ORDER;
extern dict<int64, int64> _TYPE_MIN;
extern dict<int64, int64> _TYPE_MAX;
extern dict<str, int64> _TYPE_STATE;

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
void _ensure_builtins();
int64 _normalize_base_type_id(int64 base_type_id);
int64 py_tid_register_class_type(int64 base_type_id);
int64 _try_runtime_tagged_type_id(const object& value);
int64 py_tid_runtime_type_id(const object& value);
bool py_tid_is_subtype(int64 actual_type_id, int64 expected_type_id);
bool py_tid_issubclass(int64 actual_type_id, int64 expected_type_id);
bool py_tid_isinstance(const object& value, int64 expected_type_id);
void _py_reset_type_registry_for_test();

#endif  // PYTRA_SRC_RUNTIME_CPP_PYTRA_GEN_BUILT_IN_TYPE_ID_H
