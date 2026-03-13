// AUTO-GENERATED FILE. DO NOT EDIT.
// source: src/pytra/built_in/type_id.py
// generated-by: tools/gen_runtime_from_manifest.py

using System;
using System.Collections.Generic;
using System.Linq;
using Any = System.Object;
using int64 = System.Int64;
using float64 = System.Double;
using str = System.String;

namespace Pytra.CsModule
{
    public static class type_id_helper
    {
        public static int64 _tid_none()
        {
            return 0;
        }

        public static int64 _tid_bool()
        {
            return 1;
        }

        public static int64 _tid_int()
        {
            return 2;
        }

        public static int64 _tid_float()
        {
            return 3;
        }

        public static int64 _tid_str()
        {
            return 4;
        }

        public static int64 _tid_list()
        {
            return 5;
        }

        public static int64 _tid_dict()
        {
            return 6;
        }

        public static int64 _tid_set()
        {
            return 7;
        }

        public static int64 _tid_object()
        {
            return 8;
        }

        public static int64 _tid_user_base()
        {
            return 1000;
        }

        public static System.Collections.Generic.List<int64> _make_int_list_0()
        {
            System.Collections.Generic.List<int64> py_out = new System.Collections.Generic.List<int64>();
            return py_out;
        }

        public static System.Collections.Generic.List<int64> _make_int_list_1(int64 a0)
        {
            System.Collections.Generic.List<int64> py_out = new System.Collections.Generic.List<int64>();
            py_out.Add(a0);
            return py_out;
        }

        public static bool _contains_int(System.Collections.Generic.List<int64> items, int64 value)
        {
            int64 i = 0;
            while ((i) < ((items).Count)) {
                if ((Pytra.CsModule.py_runtime.py_get(items, i)) == (value)) {
                    return true;
                }
                i += 1;
            }
            return false;
        }

        public static System.Collections.Generic.List<int64> _copy_int_list(System.Collections.Generic.List<int64> items)
        {
            System.Collections.Generic.List<int64> py_out = new System.Collections.Generic.List<int64>();
            int64 i = 0;
            while ((i) < ((items).Count)) {
                py_out.Add(Pytra.CsModule.py_runtime.py_get(items, i));
                i += 1;
            }
            return py_out;
        }

        public static System.Collections.Generic.List<int64> _sorted_ints(System.Collections.Generic.List<int64> items)
        {
            System.Collections.Generic.List<int64> py_out = _copy_int_list(items);
            int64 i = 0;
            while ((i) < ((py_out).Count)) {
                int64 j = i + 1;
                while ((j) < ((py_out).Count)) {
                    if ((Pytra.CsModule.py_runtime.py_get(py_out, j)) < (Pytra.CsModule.py_runtime.py_get(py_out, i))) {
                        int64 tmp = Pytra.CsModule.py_runtime.py_get(py_out, i);
                        Pytra.CsModule.py_runtime.py_set(py_out, i, Pytra.CsModule.py_runtime.py_get(py_out, j));
                        Pytra.CsModule.py_runtime.py_set(py_out, j, tmp);
                    }
                    j += 1;
                }
                i += 1;
            }
            return py_out;
        }

        public static void _register_type_node(int64 type_id, int64 base_type_id)
        {
            if (!_contains_int(_TYPE_IDS, type_id)) {
                _TYPE_IDS.append(type_id);
            }
            _TYPE_BASE[System.Convert.ToInt32(type_id)] = base_type_id;
            if (!((_TYPE_CHILDREN).Contains(type_id))) {
                _TYPE_CHILDREN[System.Convert.ToInt32(type_id)] = _make_int_list_0();
            }
            if ((base_type_id) < (0)) {
                return;
            }
            if (!((_TYPE_CHILDREN).Contains(base_type_id))) {
                _TYPE_CHILDREN[System.Convert.ToInt32(base_type_id)] = _make_int_list_0();
            }
            var children = _TYPE_CHILDREN[System.Convert.ToInt32(base_type_id)];
            if (!_contains_int(children, type_id)) {
                children.append(type_id);
                _TYPE_CHILDREN[System.Convert.ToInt32(base_type_id)] = children;
            }
        }

        public static System.Collections.Generic.List<int64> _sorted_child_type_ids(int64 type_id)
        {
            System.Collections.Generic.List<int64> children = _make_int_list_0();
            if ((_TYPE_CHILDREN).Contains(type_id)) {
                children = _TYPE_CHILDREN[System.Convert.ToInt32(type_id)];
            }
            return _sorted_ints(children);
        }

        public static System.Collections.Generic.List<int64> _collect_root_type_ids()
        {
            System.Collections.Generic.List<int64> roots = new System.Collections.Generic.List<int64>();
            int64 i = 0;
            while ((i) < ((_TYPE_IDS).Count())) {
                var tid = _TYPE_IDS[System.Convert.ToInt32(i)];
                int64 base_tid = -1;
                if ((_TYPE_BASE).Contains(tid)) {
                    base_tid = System.Convert.ToInt64(_TYPE_BASE[System.Convert.ToInt32(tid)]);
                }
                if (((base_tid) < (0)) || (!((_TYPE_BASE).Contains(base_tid)))) {
                    roots.Add(tid);
                }
                i += 1;
            }
            return _sorted_ints(roots);
        }

        public static int64 _assign_type_ranges_dfs(int64 type_id, int64 next_order)
        {
            _TYPE_ORDER[System.Convert.ToInt32(type_id)] = next_order;
            _TYPE_MIN[System.Convert.ToInt32(type_id)] = next_order;
            int64 cur = next_order + 1;
            System.Collections.Generic.List<int64> children = _sorted_child_type_ids(type_id);
            int64 i = 0;
            while ((i) < ((children).Count)) {
                cur = _assign_type_ranges_dfs(Pytra.CsModule.py_runtime.py_get(children, i), cur);
                i += 1;
            }
            _TYPE_MAX[System.Convert.ToInt32(type_id)] = cur - 1;
            return cur;
        }

        public static void _recompute_type_ranges()
        {
            _TYPE_ORDER.clear();
            _TYPE_MIN.clear();
            _TYPE_MAX.clear();

            int64 next_order = 0;
            System.Collections.Generic.List<int64> roots = _collect_root_type_ids();
            int64 i = 0;
            while ((i) < ((roots).Count)) {
                next_order = _assign_type_ranges_dfs(Pytra.CsModule.py_runtime.py_get(roots, i), next_order);
                i += 1;
            }
            System.Collections.Generic.List<int64> all_ids = _sorted_ints(_TYPE_IDS);
            i = 0;
            while ((i) < ((all_ids).Count)) {
                int64 tid = Pytra.CsModule.py_runtime.py_get(all_ids, i);
                if (!((_TYPE_ORDER).Contains(tid))) {
                    next_order = _assign_type_ranges_dfs(tid, next_order);
                }
                i += 1;
            }
        }

        public static void _mark_type_ranges_dirty()
        {
            _TYPE_STATE[System.Convert.ToInt32("ranges_dirty")] = 1;
        }

        public static void _mark_type_ranges_clean()
        {
            _TYPE_STATE[System.Convert.ToInt32("ranges_dirty")] = 0;
        }

        public static bool _is_type_ranges_dirty()
        {
            return ((((System.Collections.Generic.Dictionary<string, object>)_TYPE_STATE).ContainsKey(System.Convert.ToString("ranges_dirty")) ? ((System.Collections.Generic.Dictionary<string, object>)_TYPE_STATE)[System.Convert.ToString("ranges_dirty")] : 1)) != (0);
        }

        public static void _ensure_type_ranges()
        {
            if (_is_type_ranges_dirty()) {
                _recompute_type_ranges();
                _mark_type_ranges_clean();
            }
        }

        public static void _ensure_builtins()
        {
            if (!((_TYPE_STATE).Contains("next_user_type_id"))) {
                _TYPE_STATE[System.Convert.ToInt32("next_user_type_id")] = _tid_user_base();
            }
            if (!((_TYPE_STATE).Contains("ranges_dirty"))) {
                _TYPE_STATE[System.Convert.ToInt32("ranges_dirty")] = 1;
            }
            if (((_TYPE_IDS).Count()) > (0)) {
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

        public static int64 _normalize_base_type_id(int64 base_type_id)
        {
            _ensure_builtins();
            if (!(Pytra.CsModule.py_runtime.py_runtime_value_isinstance(base_type_id, Pytra.CsModule.py_runtime.PYTRA_TID_INT))) {
                throw new System.Exception("base type_id must be int");
            }
            if (!((_TYPE_BASE).Contains(base_type_id))) {
                throw new System.Exception("unknown base type_id: " + System.Convert.ToString(base_type_id));
            }
            return base_type_id;
        }

        public static int64 py_tid_register_class_type(int64 base_type_id)
        {
            _ensure_builtins();
            int64 base_tid = _normalize_base_type_id(base_type_id);

            var tid = _TYPE_STATE[System.Convert.ToInt32("next_user_type_id")];
            while ((_TYPE_BASE).Contains(tid)) {
                tid += 1;
            }
            _TYPE_STATE[System.Convert.ToInt32("next_user_type_id")] = tid + 1;

            _register_type_node(tid, base_tid);
            _mark_type_ranges_dirty();
            return tid;
        }

        public static int64 py_tid_register_known_class_type(int64 type_id, int64 base_type_id)
        {
            _ensure_builtins();
            if (!(Pytra.CsModule.py_runtime.py_runtime_value_isinstance(type_id, Pytra.CsModule.py_runtime.PYTRA_TID_INT))) {
                throw new System.Exception("type_id must be int");
            }
            if ((type_id) < (_tid_user_base())) {
                throw new System.Exception("user type_id must be >= " + System.Convert.ToString(_tid_user_base()));
            }
            int64 base_tid = _normalize_base_type_id(base_type_id);
            if ((_TYPE_BASE).Contains(type_id)) {
                if ((_TYPE_BASE[System.Convert.ToInt32(type_id)]) != (base_tid)) {
                    throw new System.Exception("type_id already registered with different base");
                }
                return type_id;
            }
            _register_type_node(type_id, base_tid);
            var next_user_type_id = _TYPE_STATE[System.Convert.ToInt32("next_user_type_id")];
            if ((type_id) >= (next_user_type_id)) {
                _TYPE_STATE[System.Convert.ToInt32("next_user_type_id")] = type_id + 1;
            }
            _mark_type_ranges_dirty();
            return type_id;
        }

        public static int64 _try_runtime_tagged_type_id(Any value)
        {
            int64 tagged = Pytra.CsModule.py_runtime.py_runtime_value_type_id(value);
            if (Pytra.CsModule.py_runtime.py_runtime_value_isinstance(tagged, Pytra.CsModule.py_runtime.PYTRA_TID_INT)) {
                int64 tagged_id = Pytra.CsModule.py_runtime.py_int(tagged);
                if ((_TYPE_BASE).Contains(tagged_id)) {
                    return tagged_id;
                }
            }
            return -1;
        }

        public static int64 py_tid_runtime_type_id(Any value)
        {
            _ensure_builtins();
            if ((value) == (null)) {
                return _tid_none();
            }
            if (Pytra.CsModule.py_runtime.py_runtime_value_isinstance(value, Pytra.CsModule.py_runtime.PYTRA_TID_BOOL)) {
                return _tid_bool();
            }
            if (Pytra.CsModule.py_runtime.py_runtime_value_isinstance(value, Pytra.CsModule.py_runtime.PYTRA_TID_INT)) {
                return _tid_int();
            }
            if (Pytra.CsModule.py_runtime.py_runtime_value_isinstance(value, Pytra.CsModule.py_runtime.PYTRA_TID_FLOAT)) {
                return _tid_float();
            }
            if (Pytra.CsModule.py_runtime.py_runtime_value_isinstance(value, Pytra.CsModule.py_runtime.PYTRA_TID_STR)) {
                return _tid_str();
            }
            if (Pytra.CsModule.py_runtime.py_runtime_value_isinstance(value, Pytra.CsModule.py_runtime.PYTRA_TID_LIST)) {
                return _tid_list();
            }
            if (Pytra.CsModule.py_runtime.py_runtime_value_isinstance(value, Pytra.CsModule.py_runtime.PYTRA_TID_DICT)) {
                return _tid_dict();
            }
            if (Pytra.CsModule.py_runtime.py_runtime_value_isinstance(value, Pytra.CsModule.py_runtime.PYTRA_TID_SET)) {
                return _tid_set();
            }
            int64 tagged = _try_runtime_tagged_type_id(value);
            if ((tagged) >= (0)) {
                return tagged;
            }
            return _tid_object();
        }

        public static bool py_tid_is_subtype(int64 actual_type_id, int64 expected_type_id)
        {
            _ensure_builtins();
            _ensure_type_ranges();
            if (!((_TYPE_ORDER).Contains(actual_type_id))) {
                return false;
            }
            if (!((_TYPE_ORDER).Contains(expected_type_id))) {
                return false;
            }
            var actual_order = _TYPE_ORDER[System.Convert.ToInt32(actual_type_id)];
            var expected_min = _TYPE_MIN[System.Convert.ToInt32(expected_type_id)];
            var expected_max = _TYPE_MAX[System.Convert.ToInt32(expected_type_id)];
            return (((expected_min) <= (actual_order)) && ((actual_order) <= (expected_max)));
        }

        public static bool py_tid_issubclass(int64 actual_type_id, int64 expected_type_id)
        {
            return Pytra.CsModule.py_runtime.py_runtime_type_id_is_subtype(actual_type_id, expected_type_id);
        }

        public static bool py_tid_isinstance(Any value, int64 expected_type_id)
        {
            return Pytra.CsModule.py_runtime.py_runtime_type_id_is_subtype(Pytra.CsModule.py_runtime.py_runtime_value_type_id(value), expected_type_id);
        }

        public static void _py_reset_type_registry_for_test()
        {
            _TYPE_IDS.clear();
            _TYPE_BASE.clear();
            _TYPE_CHILDREN.clear();
            _TYPE_ORDER.clear();
            _TYPE_MIN.clear();
            _TYPE_MAX.clear();
            _TYPE_STATE.clear();
            _TYPE_STATE[System.Convert.ToInt32("next_user_type_id")] = _tid_user_base();
            _TYPE_STATE[System.Convert.ToInt32("ranges_dirty")] = 1;
            _ensure_builtins();
        }

    }
}
