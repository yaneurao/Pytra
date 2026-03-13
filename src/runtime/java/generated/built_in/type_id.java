// AUTO-GENERATED FILE. DO NOT EDIT.
// source: src/pytra/built_in/type_id.py
// generated-by: tools/gen_runtime_from_manifest.py

public final class type_id {
    private type_id() {
    }

    public static java.util.ArrayList<Long> _TYPE_IDS = new java.util.ArrayList<Long>();
    public static java.util.HashMap<Long, Long> _TYPE_BASE = new java.util.HashMap<Long, Long>();
    public static java.util.HashMap<Long, java.util.ArrayList<Long>> _TYPE_CHILDREN = new java.util.HashMap<Long, java.util.ArrayList<Long>>();
    public static java.util.HashMap<Long, Long> _TYPE_ORDER = new java.util.HashMap<Long, Long>();
    public static java.util.HashMap<Long, Long> _TYPE_MIN = new java.util.HashMap<Long, Long>();
    public static java.util.HashMap<Long, Long> _TYPE_MAX = new java.util.HashMap<Long, Long>();
    public static java.util.HashMap<String, Long> _TYPE_STATE = new java.util.HashMap<String, Long>();


    public static long _tid_none() {
        return 0L;
    }

    public static long _tid_bool() {
        return 1L;
    }

    public static long _tid_int() {
        return 2L;
    }

    public static long _tid_float() {
        return 3L;
    }

    public static long _tid_str() {
        return 4L;
    }

    public static long _tid_list() {
        return 5L;
    }

    public static long _tid_dict() {
        return 6L;
    }

    public static long _tid_set() {
        return 7L;
    }

    public static long _tid_object() {
        return 8L;
    }

    public static long _tid_user_base() {
        return 1000L;
    }

    public static java.util.ArrayList<Long> _make_int_list_0() {
        java.util.ArrayList<Long> out = new java.util.ArrayList<Long>();
        return out;
    }

    public static java.util.ArrayList<Long> _make_int_list_1(long a0) {
        java.util.ArrayList<Long> out = new java.util.ArrayList<Long>();
        out.add(a0);
        return out;
    }

    public static boolean _contains_int(java.util.ArrayList<Long> items, long value) {
        long i = 0L;
        while (((i) < (((long)(items.size()))))) {
            if (((((Long)(items.get((int)((((i) < 0L) ? (((long)(items.size())) + (i)) : (i))))))) == (value))) {
                return true;
            }
            i += 1L;
        }
        return false;
    }

    public static java.util.ArrayList<Long> _copy_int_list(java.util.ArrayList<Long> items) {
        java.util.ArrayList<Long> out = new java.util.ArrayList<Long>();
        long i = 0L;
        while (((i) < (((long)(items.size()))))) {
            out.add(((Long)(items.get((int)((((i) < 0L) ? (((long)(items.size())) + (i)) : (i)))))));
            i += 1L;
        }
        return out;
    }

    public static java.util.ArrayList<Long> _sorted_ints(java.util.ArrayList<Long> items) {
        java.util.ArrayList<Long> out = _copy_int_list(items);
        long i = 0L;
        while (((i) < (((long)(out.size()))))) {
            long j = i + 1L;
            while (((j) < (((long)(out.size()))))) {
                if (((((Long)(out.get((int)((((j) < 0L) ? (((long)(out.size())) + (j)) : (j))))))) < (((Long)(out.get((int)((((i) < 0L) ? (((long)(out.size())) + (i)) : (i))))))))) {
                    long tmp = ((Long)(out.get((int)((((i) < 0L) ? (((long)(out.size())) + (i)) : (i))))));
                    out.set((int)((((i) < 0L) ? (((long)(out.size())) + (i)) : (i))), ((Long)(out.get((int)((((j) < 0L) ? (((long)(out.size())) + (j)) : (j)))))));
                    out.set((int)((((j) < 0L) ? (((long)(out.size())) + (j)) : (j))), tmp);
                }
                j += 1L;
            }
            i += 1L;
        }
        return out;
    }

    public static void _register_type_node(long type_id, long base_type_id) {
        if ((!_contains_int(_TYPE_IDS, type_id))) {
            _TYPE_IDS.add(type_id);
        }
        _TYPE_BASE.set((int)((((type_id) < 0L) ? (((long)(_TYPE_BASE.size())) + (type_id)) : (type_id))), base_type_id);
        if ((!(_TYPE_CHILDREN.contains(type_id)))) {
            _TYPE_CHILDREN.set((int)((((type_id) < 0L) ? (((long)(_TYPE_CHILDREN.size())) + (type_id)) : (type_id))), _make_int_list_0());
        }
        if (((base_type_id) < (0L))) {
            return;
        }
        if ((!(_TYPE_CHILDREN.contains(base_type_id)))) {
            _TYPE_CHILDREN.set((int)((((base_type_id) < 0L) ? (((long)(_TYPE_CHILDREN.size())) + (base_type_id)) : (base_type_id))), _make_int_list_0());
        }
        Object children = _TYPE_CHILDREN.get((int)((((base_type_id) < 0L) ? (((long)(_TYPE_CHILDREN.size())) + (base_type_id)) : (base_type_id))));
        if ((!_contains_int(children, type_id))) {
            children.add(type_id);
            _TYPE_CHILDREN.set((int)((((base_type_id) < 0L) ? (((long)(_TYPE_CHILDREN.size())) + (base_type_id)) : (base_type_id))), children);
        }
    }

    public static java.util.ArrayList<Long> _sorted_child_type_ids(long type_id) {
        java.util.ArrayList<Long> children = _make_int_list_0();
        if ((_TYPE_CHILDREN.contains(type_id))) {
            children = _TYPE_CHILDREN.get((int)((((type_id) < 0L) ? (((long)(_TYPE_CHILDREN.size())) + (type_id)) : (type_id))));
        }
        return _sorted_ints(children);
    }

    public static java.util.ArrayList<Long> _collect_root_type_ids() {
        java.util.ArrayList<Long> roots = new java.util.ArrayList<Long>();
        long i = 0L;
        while (((i) < (PyRuntime.__pytra_len(_TYPE_IDS)))) {
            Object tid = _TYPE_IDS.get((int)((((i) < 0L) ? (((long)(_TYPE_IDS.size())) + (i)) : (i))));
            long base_tid = (-(1L));
            if ((_TYPE_BASE.contains(tid))) {
                base_tid = _TYPE_BASE.get((int)((((tid) < 0L) ? (((long)(_TYPE_BASE.size())) + (tid)) : (tid))));
            }
            if ((((base_tid) < (0L)) || (!(_TYPE_BASE.contains(base_tid))))) {
                roots.add(tid);
            }
            i += 1L;
        }
        return _sorted_ints(roots);
    }

    public static long _assign_type_ranges_dfs(long type_id, long next_order) {
        _TYPE_ORDER.set((int)((((type_id) < 0L) ? (((long)(_TYPE_ORDER.size())) + (type_id)) : (type_id))), next_order);
        _TYPE_MIN.set((int)((((type_id) < 0L) ? (((long)(_TYPE_MIN.size())) + (type_id)) : (type_id))), next_order);
        long cur = next_order + 1L;
        java.util.ArrayList<Long> children = _sorted_child_type_ids(type_id);
        long i = 0L;
        while (((i) < (((long)(children.size()))))) {
            cur = _assign_type_ranges_dfs(((Long)(children.get((int)((((i) < 0L) ? (((long)(children.size())) + (i)) : (i)))))), cur);
            i += 1L;
        }
        _TYPE_MAX.set((int)((((type_id) < 0L) ? (((long)(_TYPE_MAX.size())) + (type_id)) : (type_id))), cur - 1L);
        return cur;
    }

    public static void _recompute_type_ranges() {
        _TYPE_ORDER.clear();
        _TYPE_MIN.clear();
        _TYPE_MAX.clear();
        long next_order = 0L;
        java.util.ArrayList<Long> roots = _collect_root_type_ids();
        long i = 0L;
        while (((i) < (((long)(roots.size()))))) {
            next_order = _assign_type_ranges_dfs(((Long)(roots.get((int)((((i) < 0L) ? (((long)(roots.size())) + (i)) : (i)))))), next_order);
            i += 1L;
        }
        java.util.ArrayList<Long> all_ids = _sorted_ints(_TYPE_IDS);
        i = 0L;
        while (((i) < (((long)(all_ids.size()))))) {
            long tid = ((Long)(all_ids.get((int)((((i) < 0L) ? (((long)(all_ids.size())) + (i)) : (i))))));
            if ((!(_TYPE_ORDER.contains(tid)))) {
                next_order = _assign_type_ranges_dfs(tid, next_order);
            }
            i += 1L;
        }
    }

    public static void _mark_type_ranges_dirty() {
        _TYPE_STATE.set((int)(((("ranges_dirty") < 0L) ? (((long)(_TYPE_STATE.size())) + ("ranges_dirty")) : ("ranges_dirty"))), 1L);
    }

    public static void _mark_type_ranges_clean() {
        _TYPE_STATE.set((int)(((("ranges_dirty") < 0L) ? (((long)(_TYPE_STATE.size())) + ("ranges_dirty")) : ("ranges_dirty"))), 0L);
    }

    public static boolean _is_type_ranges_dirty() {
        return ((((Long)(PyRuntime.__pytra_dict_get_default(_TYPE_STATE, "ranges_dirty", 1L)))) != (0L));
    }

    public static void _ensure_type_ranges() {
        if (_is_type_ranges_dirty()) {
            _recompute_type_ranges();
            _mark_type_ranges_clean();
        }
    }

    public static void _ensure_builtins() {
        if ((!(_TYPE_STATE.contains("next_user_type_id")))) {
            _TYPE_STATE.set((int)(((("next_user_type_id") < 0L) ? (((long)(_TYPE_STATE.size())) + ("next_user_type_id")) : ("next_user_type_id"))), _tid_user_base());
        }
        if ((!(_TYPE_STATE.contains("ranges_dirty")))) {
            _TYPE_STATE.set((int)(((("ranges_dirty") < 0L) ? (((long)(_TYPE_STATE.size())) + ("ranges_dirty")) : ("ranges_dirty"))), 1L);
        }
        if (((PyRuntime.__pytra_len(_TYPE_IDS)) > (0L))) {
            return;
        }
        _register_type_node(_tid_none(), (-(1L)));
        _register_type_node(_tid_object(), (-(1L)));
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

    public static long _normalize_base_type_id(long base_type_id) {
        _ensure_builtins();
        if ((!(((Object)(base_type_id)) instanceof PYTRA_TID_INT))) {
            throw new RuntimeException(PyRuntime.pyToString("base type_id must be int"));
        }
        if ((!(_TYPE_BASE.contains(base_type_id)))) {
            throw new RuntimeException(PyRuntime.pyToString("unknown base type_id: " + String.valueOf(base_type_id)));
        }
        return base_type_id;
    }

    public static long py_tid_register_class_type(long base_type_id) {
        _ensure_builtins();
        long base_tid = _normalize_base_type_id(base_type_id);
        Object tid = _TYPE_STATE.get((int)(((("next_user_type_id") < 0L) ? (((long)(_TYPE_STATE.size())) + ("next_user_type_id")) : ("next_user_type_id"))));
        while ((_TYPE_BASE.contains(tid))) {
            tid += 1L;
        }
        _TYPE_STATE.set((int)(((("next_user_type_id") < 0L) ? (((long)(_TYPE_STATE.size())) + ("next_user_type_id")) : ("next_user_type_id"))), tid + 1L);
        _register_type_node(tid, base_tid);
        _mark_type_ranges_dirty();
        return tid;
    }

    public static long py_tid_register_known_class_type(long type_id, long base_type_id) {
        _ensure_builtins();
        if ((!(((Object)(type_id)) instanceof PYTRA_TID_INT))) {
            throw new RuntimeException(PyRuntime.pyToString("type_id must be int"));
        }
        if (((type_id) < (_tid_user_base()))) {
            throw new RuntimeException(PyRuntime.pyToString("user type_id must be >= " + String.valueOf(_tid_user_base())));
        }
        long base_tid = _normalize_base_type_id(base_type_id);
        if ((_TYPE_BASE.contains(type_id))) {
            if (((_TYPE_BASE.get((int)((((type_id) < 0L) ? (((long)(_TYPE_BASE.size())) + (type_id)) : (type_id))))) != (base_tid))) {
                throw new RuntimeException(PyRuntime.pyToString("type_id already registered with different base"));
            }
            return type_id;
        }
        _register_type_node(type_id, base_tid);
        Object next_user_type_id = _TYPE_STATE.get((int)(((("next_user_type_id") < 0L) ? (((long)(_TYPE_STATE.size())) + ("next_user_type_id")) : ("next_user_type_id"))));
        if (((type_id) >= (next_user_type_id))) {
            _TYPE_STATE.set((int)(((("next_user_type_id") < 0L) ? (((long)(_TYPE_STATE.size())) + ("next_user_type_id")) : ("next_user_type_id"))), type_id + 1L);
        }
        _mark_type_ranges_dirty();
        return type_id;
    }

    public static long _try_runtime_tagged_type_id(Any value) {
        long tagged = 0L;
        if ((((Object)(tagged)) instanceof PYTRA_TID_INT)) {
            long tagged_id = PyRuntime.__pytra_int(tagged);
            if ((_TYPE_BASE.contains(tagged_id))) {
                return tagged_id;
            }
        }
        return (-(1L));
    }

    public static long py_tid_runtime_type_id(Any value) {
        _ensure_builtins();
        if (((value) == (null))) {
            return _tid_none();
        }
        if ((((Object)(value)) instanceof PYTRA_TID_BOOL)) {
            return _tid_bool();
        }
        if ((((Object)(value)) instanceof PYTRA_TID_INT)) {
            return _tid_int();
        }
        if ((((Object)(value)) instanceof PYTRA_TID_FLOAT)) {
            return _tid_float();
        }
        if ((((Object)(value)) instanceof PYTRA_TID_STR)) {
            return _tid_str();
        }
        if ((((Object)(value)) instanceof PYTRA_TID_LIST)) {
            return _tid_list();
        }
        if ((((Object)(value)) instanceof PYTRA_TID_DICT)) {
            return _tid_dict();
        }
        if ((((Object)(value)) instanceof PYTRA_TID_SET)) {
            return _tid_set();
        }
        long tagged = _try_runtime_tagged_type_id(value);
        if (((tagged) >= (0L))) {
            return tagged;
        }
        return _tid_object();
    }

    public static boolean py_tid_is_subtype(long actual_type_id, long expected_type_id) {
        _ensure_builtins();
        _ensure_type_ranges();
        if ((!(_TYPE_ORDER.contains(actual_type_id)))) {
            return false;
        }
        if ((!(_TYPE_ORDER.contains(expected_type_id)))) {
            return false;
        }
        Object actual_order = _TYPE_ORDER.get((int)((((actual_type_id) < 0L) ? (((long)(_TYPE_ORDER.size())) + (actual_type_id)) : (actual_type_id))));
        Object expected_min = _TYPE_MIN.get((int)((((expected_type_id) < 0L) ? (((long)(_TYPE_MIN.size())) + (expected_type_id)) : (expected_type_id))));
        Object expected_max = _TYPE_MAX.get((int)((((expected_type_id) < 0L) ? (((long)(_TYPE_MAX.size())) + (expected_type_id)) : (expected_type_id))));
        return (((expected_min) <= (actual_order)) && ((actual_order) <= (expected_max)));
    }

    public static boolean py_tid_issubclass(long actual_type_id, long expected_type_id) {
        return null;
    }

    public static boolean py_tid_isinstance(Any value, long expected_type_id) {
        return null;
    }

    public static void _py_reset_type_registry_for_test() {
        _TYPE_IDS.clear();
        _TYPE_BASE.clear();
        _TYPE_CHILDREN.clear();
        _TYPE_ORDER.clear();
        _TYPE_MIN.clear();
        _TYPE_MAX.clear();
        _TYPE_STATE.clear();
        _TYPE_STATE.set((int)(((("next_user_type_id") < 0L) ? (((long)(_TYPE_STATE.size())) + ("next_user_type_id")) : ("next_user_type_id"))), _tid_user_base());
        _TYPE_STATE.set((int)(((("ranges_dirty") < 0L) ? (((long)(_TYPE_STATE.size())) + ("ranges_dirty")) : ("ranges_dirty"))), 1L);
        _ensure_builtins();
    }

    public static void main(String[] args) {
    }
}
