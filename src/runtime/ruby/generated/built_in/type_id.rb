# AUTO-GENERATED FILE. DO NOT EDIT.
# source: src/pytra/built_in/type_id.py
# generated-by: tools/gen_runtime_from_manifest.py

require_relative "py_runtime"


def _tid_none()
  return 0
end

def _tid_bool()
  return 1
end

def _tid_int()
  return 2
end

def _tid_float()
  return 3
end

def _tid_str()
  return 4
end

def _tid_list()
  return 5
end

def _tid_dict()
  return 6
end

def _tid_set()
  return 7
end

def _tid_object()
  return 8
end

def _tid_user_base()
  return 1000
end

def _make_int_list_0()
  out = []
  return out
end

def _make_int_list_1(a0)
  out = []
  out.append(a0)
  return out
end

def _contains_int(items, value)
  i = 0
  while i < __pytra_len(items)
    if __pytra_get_index(items, i) == value
      return true
    end
    i += 1
  end
  return false
end

def _copy_int_list(items)
  out = []
  i = 0
  while i < __pytra_len(items)
    out.append(__pytra_get_index(items, i))
    i += 1
  end
  return out
end

def _sorted_ints(items)
  out = _copy_int_list(items)
  i = 0
  while i < __pytra_len(out)
    j = i + 1
    while j < __pytra_len(out)
      if __pytra_get_index(out, j) < __pytra_get_index(out, i)
        tmp = __pytra_get_index(out, i)
        __pytra_set_index(out, i, __pytra_get_index(out, j))
        __pytra_set_index(out, j, tmp)
      end
      j += 1
    end
    i += 1
  end
  return out
end

def _register_type_node(type_id, base_type_id)
  if !_contains_int(_TYPE_IDS, type_id)
    _TYPE_IDS.append(type_id)
  end
  __pytra_set_index(_TYPE_BASE, type_id, base_type_id)
  if !__pytra_contains(_TYPE_CHILDREN, type_id)
    __pytra_set_index(_TYPE_CHILDREN, type_id, _make_int_list_0())
  end
  if base_type_id < 0
    return nil
  end
  if !__pytra_contains(_TYPE_CHILDREN, base_type_id)
    __pytra_set_index(_TYPE_CHILDREN, base_type_id, _make_int_list_0())
  end
  children = __pytra_get_index(_TYPE_CHILDREN, base_type_id)
  if !_contains_int(children, type_id)
    children.append(type_id)
    __pytra_set_index(_TYPE_CHILDREN, base_type_id, children)
  end
end

def _sorted_child_type_ids(type_id)
  children = _make_int_list_0()
  if __pytra_contains(_TYPE_CHILDREN, type_id)
    children = __pytra_get_index(_TYPE_CHILDREN, type_id)
  end
  return _sorted_ints(children)
end

def _collect_root_type_ids()
  roots = []
  i = 0
  while i < __pytra_len(_TYPE_IDS)
    tid = __pytra_get_index(_TYPE_IDS, i)
    base_tid = (-1)
    if __pytra_contains(_TYPE_BASE, tid)
      base_tid = __pytra_get_index(_TYPE_BASE, tid)
    end
    if (base_tid < 0) || (!__pytra_contains(_TYPE_BASE, base_tid))
      roots.append(tid)
    end
    i += 1
  end
  return _sorted_ints(roots)
end

def _assign_type_ranges_dfs(type_id, next_order)
  __pytra_set_index(_TYPE_ORDER, type_id, next_order)
  __pytra_set_index(_TYPE_MIN, type_id, next_order)
  cur = next_order + 1
  children = _sorted_child_type_ids(type_id)
  i = 0
  while i < __pytra_len(children)
    cur = _assign_type_ranges_dfs(__pytra_get_index(children, i), cur)
    i += 1
  end
  __pytra_set_index(_TYPE_MAX, type_id, cur - 1)
  return cur
end

def _recompute_type_ranges()
  _TYPE_ORDER.clear()
  _TYPE_MIN.clear()
  _TYPE_MAX.clear()
  next_order = 0
  roots = _collect_root_type_ids()
  i = 0
  while i < __pytra_len(roots)
    next_order = _assign_type_ranges_dfs(__pytra_get_index(roots, i), next_order)
    i += 1
  end
  all_ids = _sorted_ints(_TYPE_IDS)
  i = 0
  while i < __pytra_len(all_ids)
    tid = __pytra_get_index(all_ids, i)
    if !__pytra_contains(_TYPE_ORDER, tid)
      next_order = _assign_type_ranges_dfs(tid, next_order)
    end
    i += 1
  end
end

def _mark_type_ranges_dirty()
  __pytra_set_index(_TYPE_STATE, "ranges_dirty", 1)
end

def _mark_type_ranges_clean()
  __pytra_set_index(_TYPE_STATE, "ranges_dirty", 0)
end

def _is_type_ranges_dirty()
  return (_TYPE_STATE.get("ranges_dirty", 1) != 0)
end

def _ensure_type_ranges()
  if _is_type_ranges_dirty()
    _recompute_type_ranges()
    _mark_type_ranges_clean()
  end
end

def _ensure_builtins()
  if !__pytra_contains(_TYPE_STATE, "next_user_type_id")
    __pytra_set_index(_TYPE_STATE, "next_user_type_id", _tid_user_base())
  end
  if !__pytra_contains(_TYPE_STATE, "ranges_dirty")
    __pytra_set_index(_TYPE_STATE, "ranges_dirty", 1)
  end
  if __pytra_len(_TYPE_IDS) > 0
    return nil
  end
  _register_type_node(_tid_none(), (-1))
  _register_type_node(_tid_object(), (-1))
  _register_type_node(_tid_int(), _tid_object())
  _register_type_node(_tid_bool(), _tid_int())
  _register_type_node(_tid_float(), _tid_object())
  _register_type_node(_tid_str(), _tid_object())
  _register_type_node(_tid_list(), _tid_object())
  _register_type_node(_tid_dict(), _tid_object())
  _register_type_node(_tid_set(), _tid_object())
  _recompute_type_ranges()
  _mark_type_ranges_clean()
end

def _normalize_base_type_id(base_type_id)
  _ensure_builtins()
  if !false
    raise RuntimeError, __pytra_str("base type_id must be int")
  end
  if !__pytra_contains(_TYPE_BASE, base_type_id)
    raise RuntimeError, __pytra_str("unknown base type_id: " + __pytra_str(base_type_id))
  end
  return base_type_id
end

def py_tid_register_class_type(base_type_id)
  _ensure_builtins()
  base_tid = _normalize_base_type_id(base_type_id)
  tid = __pytra_get_index(_TYPE_STATE, "next_user_type_id")
  while __pytra_contains(_TYPE_BASE, tid)
    tid += 1
  end
  __pytra_set_index(_TYPE_STATE, "next_user_type_id", tid + 1)
  _register_type_node(tid, base_tid)
  _mark_type_ranges_dirty()
  return tid
end

def py_tid_register_known_class_type(type_id, base_type_id)
  _ensure_builtins()
  if !false
    raise RuntimeError, __pytra_str("type_id must be int")
  end
  if type_id < _tid_user_base()
    raise RuntimeError, __pytra_str("user type_id must be >= " + __pytra_str(_tid_user_base()))
  end
  base_tid = _normalize_base_type_id(base_type_id)
  if __pytra_contains(_TYPE_BASE, type_id)
    if __pytra_get_index(_TYPE_BASE, type_id) != base_tid
      raise RuntimeError, __pytra_str("type_id already registered with different base")
    end
    return type_id
  end
  _register_type_node(type_id, base_tid)
  next_user_type_id = __pytra_get_index(_TYPE_STATE, "next_user_type_id")
  if type_id >= next_user_type_id
    __pytra_set_index(_TYPE_STATE, "next_user_type_id", type_id + 1)
  end
  _mark_type_ranges_dirty()
  return type_id
end

def _try_runtime_tagged_type_id(value)
  tagged = nil
  if false
    tagged_id = __pytra_int(tagged)
    if __pytra_contains(_TYPE_BASE, tagged_id)
      return tagged_id
    end
  end
  return (-1)
end

def py_tid_runtime_type_id(value)
  _ensure_builtins()
  if value == nil
    return _tid_none()
  end
  if false
    return _tid_bool()
  end
  if false
    return _tid_int()
  end
  if false
    return _tid_float()
  end
  if false
    return _tid_str()
  end
  if false
    return _tid_list()
  end
  if false
    return _tid_dict()
  end
  if false
    return _tid_set()
  end
  tagged = _try_runtime_tagged_type_id(value)
  if tagged >= 0
    return tagged
  end
  return _tid_object()
end

def py_tid_is_subtype(actual_type_id, expected_type_id)
  _ensure_builtins()
  _ensure_type_ranges()
  if !__pytra_contains(_TYPE_ORDER, actual_type_id)
    return false
  end
  if !__pytra_contains(_TYPE_ORDER, expected_type_id)
    return false
  end
  actual_order = __pytra_get_index(_TYPE_ORDER, actual_type_id)
  expected_min = __pytra_get_index(_TYPE_MIN, expected_type_id)
  expected_max = __pytra_get_index(_TYPE_MAX, expected_type_id)
  return ((expected_min <= actual_order) && (actual_order <= expected_max))
end

def py_tid_issubclass(actual_type_id, expected_type_id)
  return nil
end

def py_tid_isinstance(value, expected_type_id)
  return nil
end

def _py_reset_type_registry_for_test()
  _TYPE_IDS.clear()
  _TYPE_BASE.clear()
  _TYPE_CHILDREN.clear()
  _TYPE_ORDER.clear()
  _TYPE_MIN.clear()
  _TYPE_MAX.clear()
  _TYPE_STATE.clear()
  __pytra_set_index(_TYPE_STATE, "next_user_type_id", _tid_user_base())
  __pytra_set_index(_TYPE_STATE, "ranges_dirty", 1)
  _ensure_builtins()
end

if __FILE__ == $PROGRAM_NAME
end
