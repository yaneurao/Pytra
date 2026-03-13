# AUTO-GENERATED FILE. DO NOT EDIT.
# source: src/pytra/built_in/type_id.py
# generated-by: tools/gen_runtime_from_manifest.py

include "py_runtime.nim"

import std/os, std/times, std/tables, std/strutils, std/math, std/sequtils

discard "Pure-Python source-of-truth for single-inheritance type_id range semantics."
var vTYPE_IDS: seq[int] = @[]
var vTYPE_BASE: Table[int, int] = initTable[string, int]()
var vTYPE_CHILDREN: Table[int, seq[int]] = initTable[string, int]()
var vTYPE_ORDER: Table[int, int] = initTable[string, int]()
var vTYPE_MIN: Table[int, int] = initTable[string, int]()
var vTYPE_MAX: Table[int, int] = initTable[string, int]()
var vTYPE_STATE: Table[string, int] = initTable[string, int]()
proc vtid_none*(): int =
  return 0

proc vtid_bool*(): int =
  return 1

proc vtid_int*(): int =
  return 2

proc vtid_float*(): int =
  return 3

proc vtid_str*(): int =
  return 4

proc vtid_list*(): int =
  return 5

proc vtid_dict*(): int =
  return 6

proc vtid_set*(): int =
  return 7

proc vtid_object*(): int =
  return 8

proc vtid_user_base*(): int =
  return 1000

proc vmake_int_list_0*(): seq[int] =
  var `out`: seq[int] = @[]
  `out` = @[] # seq[int]
  return `out`

proc vmake_int_list_1*(a0: int): seq[int] =
  var `out`: seq[int] = @[]
  `out` = @[] # seq[int]
  `out`.add(a0)
  return `out`

proc vcontains_int*(items: seq[int], value: int): bool =
  var i: int = 0
  i = 0
  while (i < items.len):
    if (items[i] == value):
      return true
    i += 1
  return false

proc vcopy_int_list*(items: seq[int]): seq[int] =
  var `out`: seq[int] = @[]
  var i: int = 0
  `out` = @[] # seq[int]
  i = 0
  while (i < items.len):
    `out`.add(items[i])
    i += 1
  return `out`

proc vsorted_ints*(items: seq[int]): seq[int] =
  var `out`: seq[int] = @[]
  var i: int = 0
  var j: int = 0
  var tmp: int = 0
  `out` = vcopy_int_list(items)
  i = 0
  while (i < `out`.len):
    j = (i + 1)
    while (j < `out`.len):
      if (`out`[j] < `out`[i]):
        tmp = `out`[i]
        `out`[i] = `out`[j]
        `out`[j] = tmp
      j += 1
    i += 1
  return `out`

proc vregister_type_node*(type_id: int, base_type_id: int) =
  if py_truthy((not py_truthy(vcontains_int(vTYPE_IDS, type_id)))):
    vTYPE_IDS.add(type_id)
  vTYPE_BASE[type_id] = base_type_id
  if (not (type_id in vTYPE_CHILDREN)):
    vTYPE_CHILDREN[type_id] = vmake_int_list_0()
  if (base_type_id < 0):
    return 
  if (not (base_type_id in vTYPE_CHILDREN)):
    vTYPE_CHILDREN[base_type_id] = vmake_int_list_0()
  var children = vTYPE_CHILDREN[base_type_id]
  if py_truthy((not py_truthy(vcontains_int(children, type_id)))):
    children.add(type_id)
    vTYPE_CHILDREN[base_type_id] = children

proc vsorted_child_type_ids*(type_id: int): seq[int] =
  var children: seq[int] = @[]
  children = vmake_int_list_0()
  if (type_id in vTYPE_CHILDREN):
    children = vTYPE_CHILDREN[type_id]
  return vsorted_ints(children)

proc vcollect_root_type_ids*(): seq[int] =
  var base_tid: int = 0
  var i: int = 0
  var roots: seq[int] = @[]
  roots = @[] # seq[int]
  i = 0
  while (i < vTYPE_IDS.len):
    var tid = vTYPE_IDS[i]
    base_tid = (-1)
    if (tid in vTYPE_BASE):
      base_tid = vTYPE_BASE[tid]
    if py_truthy(((base_tid < 0) or (not (base_tid in vTYPE_BASE)))):
      roots.add(tid)
    i += 1
  return vsorted_ints(roots)

proc vassign_type_ranges_dfs*(type_id: int, next_order: int): int =
  var children: seq[int] = @[]
  var cur: int = 0
  var i: int = 0
  vTYPE_ORDER[type_id] = next_order
  vTYPE_MIN[type_id] = next_order
  cur = (next_order + 1)
  children = vsorted_child_type_ids(type_id)
  i = 0
  while (i < children.len):
    cur = vassign_type_ranges_dfs(children[i], cur)
    i += 1
  vTYPE_MAX[type_id] = (cur - 1)
  return cur

proc vrecompute_type_ranges*() =
  var all_ids: seq[int] = @[]
  var i: int = 0
  var next_order: int = 0
  var roots: seq[int] = @[]
  var tid: int = 0
  vTYPE_ORDER.clear()
  vTYPE_MIN.clear()
  vTYPE_MAX.clear()
  next_order = 0
  roots = vcollect_root_type_ids()
  i = 0
  while (i < roots.len):
    next_order = vassign_type_ranges_dfs(roots[i], next_order)
    i += 1
  all_ids = vsorted_ints(vTYPE_IDS)
  i = 0
  while (i < all_ids.len):
    tid = all_ids[i]
    if (not (tid in vTYPE_ORDER)):
      next_order = vassign_type_ranges_dfs(tid, next_order)
    i += 1

proc vmark_type_ranges_dirty*() =
  vTYPE_STATE["ranges_dirty"] = 1

proc vmark_type_ranges_clean*() =
  vTYPE_STATE["ranges_dirty"] = 0

proc vis_type_ranges_dirty*(): bool =
  return (getOrDefault(vTYPE_STATE, "ranges_dirty", 1) != 0)

proc vensure_type_ranges*() =
  if py_truthy(vis_type_ranges_dirty()):
    vrecompute_type_ranges()
    vmark_type_ranges_clean()

proc vensure_builtins*() =
  if (not ("next_user_type_id" in vTYPE_STATE)):
    vTYPE_STATE["next_user_type_id"] = vtid_user_base()
  if (not ("ranges_dirty" in vTYPE_STATE)):
    vTYPE_STATE["ranges_dirty"] = 1
  if (vTYPE_IDS.len > 0):
    return 
  vregister_type_node(vtid_none(), (-1))
  vregister_type_node(vtid_object(), (-1))
  vregister_type_node(vtid_int(), vtid_object())
  vregister_type_node(vtid_bool(), vtid_int())
  vregister_type_node(vtid_float(), vtid_object())
  vregister_type_node(vtid_str(), vtid_object())
  vregister_type_node(vtid_list(), vtid_object())
  vregister_type_node(vtid_dict(), vtid_object())
  vregister_type_node(vtid_set(), vtid_object())
  vrecompute_type_ranges()
  vmark_type_ranges_clean()

proc vnormalize_base_type_id*(base_type_id: int): int =
  vensure_builtins()
  if py_truthy((not py_truthy(false))):
    raise newException(Exception, "base type_id must be int")
  if (not (base_type_id in vTYPE_BASE)):
    raise newException(Exception, ($("unknown base type_id: ") & $($( base_type_id ))))
  return base_type_id

proc py_tid_register_class_type*(base_type_id: int): auto =
  var base_tid: int = 0
  vensure_builtins()
  base_tid = vnormalize_base_type_id(base_type_id)
  var tid = vTYPE_STATE["next_user_type_id"]
  while (tid in vTYPE_BASE):
    tid += 1
  vTYPE_STATE["next_user_type_id"] = (tid + 1)
  vregister_type_node(tid, base_tid)
  vmark_type_ranges_dirty()
  return tid

proc py_tid_register_known_class_type*(type_id: int, base_type_id: int): int =
  var base_tid: int = 0
  vensure_builtins()
  if py_truthy((not py_truthy(false))):
    raise newException(Exception, "type_id must be int")
  if (type_id < vtid_user_base()):
    raise newException(Exception, ($("user type_id must be >= ") & $($( vtid_user_base() ))))
  base_tid = vnormalize_base_type_id(base_type_id)
  if (type_id in vTYPE_BASE):
    if (vTYPE_BASE[type_id] != base_tid):
      raise newException(Exception, "type_id already registered with different base")
    return type_id
  vregister_type_node(type_id, base_tid)
  var next_user_type_id = vTYPE_STATE["next_user_type_id"]
  if (type_id >= next_user_type_id):
    vTYPE_STATE["next_user_type_id"] = (type_id + 1)
  vmark_type_ranges_dirty()
  return type_id

proc vtry_runtime_tagged_type_id*(value: auto): int =
  var tagged: int = 0
  var tagged_id: int = 0
  tagged = 0
  if py_truthy(false):
    tagged_id = int(tagged)
    if (tagged_id in vTYPE_BASE):
      return tagged_id
  return (-1)

proc py_tid_runtime_type_id*(value: auto): int =
  var tagged: int = 0
  vensure_builtins()
  if (value == nil):
    return vtid_none()
  if py_truthy(false):
    return vtid_bool()
  if py_truthy(false):
    return vtid_int()
  if py_truthy(false):
    return vtid_float()
  if py_truthy(false):
    return vtid_str()
  if py_truthy(false):
    return vtid_list()
  if py_truthy(false):
    return vtid_dict()
  if py_truthy(false):
    return vtid_set()
  tagged = vtry_runtime_tagged_type_id(value)
  if (tagged >= 0):
    return tagged
  return vtid_object()

proc py_tid_is_subtype*(actual_type_id: int, expected_type_id: int): bool =
  vensure_builtins()
  vensure_type_ranges()
  if (not (actual_type_id in vTYPE_ORDER)):
    return false
  if (not (expected_type_id in vTYPE_ORDER)):
    return false
  var actual_order = vTYPE_ORDER[actual_type_id]
  var expected_min = vTYPE_MIN[expected_type_id]
  var expected_max = vTYPE_MAX[expected_type_id]
  return ((expected_min <= actual_order) and (actual_order <= expected_max))

proc py_tid_issubclass*(actual_type_id: int, expected_type_id: int): bool =
  return 0

proc py_tid_isinstance*(value: auto, expected_type_id: int): bool =
  return 0

proc vpy_reset_type_registry_for_test*() =
  vTYPE_IDS.clear()
  vTYPE_BASE.clear()
  vTYPE_CHILDREN.clear()
  vTYPE_ORDER.clear()
  vTYPE_MIN.clear()
  vTYPE_MAX.clear()
  vTYPE_STATE.clear()
  vTYPE_STATE["next_user_type_id"] = vtid_user_base()
  vTYPE_STATE["ranges_dirty"] = 1
  vensure_builtins()
