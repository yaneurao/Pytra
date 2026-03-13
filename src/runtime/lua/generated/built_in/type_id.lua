-- AUTO-GENERATED FILE. DO NOT EDIT.
-- source: src/pytra/built_in/type_id.py
-- generated-by: tools/gen_runtime_from_manifest.py

dofile((debug.getinfo(1, "S").source:sub(2):match("^(.*[\\/])") or "") .. "py_runtime.lua")

local function __pytra_obj_type_id(value)
    if type(value) ~= "table" then
        return nil
    end
    local tagged = rawget(value, "PYTRA_TYPE_ID")
    if tagged ~= nil then
        return tagged
    end
    local mt = getmetatable(value)
    if type(mt) == "table" then
        return rawget(mt, "PYTRA_TYPE_ID")
    end
    return nil
end

local _TYPE_IDS = {  }
local _TYPE_BASE = {}
local _TYPE_CHILDREN = {}
local _TYPE_ORDER = {}
local _TYPE_MIN = {}
local _TYPE_MAX = {}
local _TYPE_STATE = {}
function _tid_none()
    return 0
end

function _tid_bool()
    return 1
end

function _tid_int()
    return 2
end

function _tid_float()
    return 3
end

function _tid_str()
    return 4
end

function _tid_list()
    return 5
end

function _tid_dict()
    return 6
end

function _tid_set()
    return 7
end

function _tid_object()
    return 8
end

function _tid_user_base()
    return 1000
end

function _make_int_list_0()
    local out = {  }
    return out
end

function _make_int_list_1(a0)
    local out = {  }
    table.insert(out, a0)
    return out
end

function _contains_int(items, value)
    local i = 0
    while (i < #(items)) do
        if (items[(((i) < 0) and (#(items) + (i) + 1) or ((i) + 1))] == value) then
            return true
        end
        i = i + 1
    end
    return false
end

function _copy_int_list(items)
    local out = {  }
    local i = 0
    while (i < #(items)) do
        table.insert(out, items[(((i) < 0) and (#(items) + (i) + 1) or ((i) + 1))])
        i = i + 1
    end
    return out
end

function _sorted_ints(items)
    local out = _copy_int_list(items)
    local i = 0
    while (i < #(out)) do
        local j = (i + 1)
        while (j < #(out)) do
            if (out[(((j) < 0) and (#(out) + (j) + 1) or ((j) + 1))] < out[(((i) < 0) and (#(out) + (i) + 1) or ((i) + 1))]) then
                local tmp = out[(((i) < 0) and (#(out) + (i) + 1) or ((i) + 1))]
                out[(((i) < 0) and (#(out) + (i) + 1) or ((i) + 1))] = out[(((j) < 0) and (#(out) + (j) + 1) or ((j) + 1))]
                out[(((j) < 0) and (#(out) + (j) + 1) or ((j) + 1))] = tmp
            end
            j = j + 1
        end
        i = i + 1
    end
    return out
end

function _register_type_node(type_id, base_type_id)
    if (not _contains_int(_TYPE_IDS, type_id)) then
        table.insert(_TYPE_IDS, type_id)
    end
    _TYPE_BASE[(((type_id) < 0) and (#(_TYPE_BASE) + (type_id) + 1) or ((type_id) + 1))] = base_type_id
    if (not __pytra_contains(_TYPE_CHILDREN, type_id)) then
        _TYPE_CHILDREN[(((type_id) < 0) and (#(_TYPE_CHILDREN) + (type_id) + 1) or ((type_id) + 1))] = _make_int_list_0()
    end
    if (base_type_id < 0) then
        return nil
    end
    if (not __pytra_contains(_TYPE_CHILDREN, base_type_id)) then
        _TYPE_CHILDREN[(((base_type_id) < 0) and (#(_TYPE_CHILDREN) + (base_type_id) + 1) or ((base_type_id) + 1))] = _make_int_list_0()
    end
    local children = _TYPE_CHILDREN[(((base_type_id) < 0) and (#(_TYPE_CHILDREN) + (base_type_id) + 1) or ((base_type_id) + 1))]
    if (not _contains_int(children, type_id)) then
        table.insert(children, type_id)
        _TYPE_CHILDREN[(((base_type_id) < 0) and (#(_TYPE_CHILDREN) + (base_type_id) + 1) or ((base_type_id) + 1))] = children
    end
end

function _sorted_child_type_ids(type_id)
    local children = _make_int_list_0()
    if __pytra_contains(_TYPE_CHILDREN, type_id) then
        children = _TYPE_CHILDREN[(((type_id) < 0) and (#(_TYPE_CHILDREN) + (type_id) + 1) or ((type_id) + 1))]
    end
    return _sorted_ints(children)
end

function _collect_root_type_ids()
    local roots = {  }
    local i = 0
    while (i < #(_TYPE_IDS)) do
        local tid = _TYPE_IDS[(((i) < 0) and (#(_TYPE_IDS) + (i) + 1) or ((i) + 1))]
        local base_tid = (-1)
        if __pytra_contains(_TYPE_BASE, tid) then
            base_tid = _TYPE_BASE[(((tid) < 0) and (#(_TYPE_BASE) + (tid) + 1) or ((tid) + 1))]
        end
        if ((base_tid < 0) or (not __pytra_contains(_TYPE_BASE, base_tid))) then
            table.insert(roots, tid)
        end
        i = i + 1
    end
    return _sorted_ints(roots)
end

function _assign_type_ranges_dfs(type_id, next_order)
    _TYPE_ORDER[(((type_id) < 0) and (#(_TYPE_ORDER) + (type_id) + 1) or ((type_id) + 1))] = next_order
    _TYPE_MIN[(((type_id) < 0) and (#(_TYPE_MIN) + (type_id) + 1) or ((type_id) + 1))] = next_order
    local cur = (next_order + 1)
    local children = _sorted_child_type_ids(type_id)
    local i = 0
    while (i < #(children)) do
        cur = _assign_type_ranges_dfs(children[(((i) < 0) and (#(children) + (i) + 1) or ((i) + 1))], cur)
        i = i + 1
    end
    _TYPE_MAX[(((type_id) < 0) and (#(_TYPE_MAX) + (type_id) + 1) or ((type_id) + 1))] = (cur - 1)
    return cur
end

function _recompute_type_ranges()
    _TYPE_ORDER:clear()
    _TYPE_MIN:clear()
    _TYPE_MAX:clear()
    
    local next_order = 0
    local roots = _collect_root_type_ids()
    local i = 0
    while (i < #(roots)) do
        next_order = _assign_type_ranges_dfs(roots[(((i) < 0) and (#(roots) + (i) + 1) or ((i) + 1))], next_order)
        i = i + 1
    end
    local all_ids = _sorted_ints(_TYPE_IDS)
    i = 0
    while (i < #(all_ids)) do
        local tid = all_ids[(((i) < 0) and (#(all_ids) + (i) + 1) or ((i) + 1))]
        if (not __pytra_contains(_TYPE_ORDER, tid)) then
            next_order = _assign_type_ranges_dfs(tid, next_order)
        end
        i = i + 1
    end
end

function _mark_type_ranges_dirty()
    _TYPE_STATE[((("ranges_dirty") < 0) and (#(_TYPE_STATE) + ("ranges_dirty") + 1) or (("ranges_dirty") + 1))] = 1
end

function _mark_type_ranges_clean()
    _TYPE_STATE[((("ranges_dirty") < 0) and (#(_TYPE_STATE) + ("ranges_dirty") + 1) or (("ranges_dirty") + 1))] = 0
end

function _is_type_ranges_dirty()
    return ((function(__tbl, __key, __default) local __val = __tbl[__key]; if __val == nil then return __default end; return __val end)(_TYPE_STATE, "ranges_dirty", 1) ~= 0)
end

function _ensure_type_ranges()
    if _is_type_ranges_dirty() then
        _recompute_type_ranges()
        _mark_type_ranges_clean()
    end
end

function _ensure_builtins()
    if (not __pytra_contains(_TYPE_STATE, "next_user_type_id")) then
        _TYPE_STATE[((("next_user_type_id") < 0) and (#(_TYPE_STATE) + ("next_user_type_id") + 1) or (("next_user_type_id") + 1))] = _tid_user_base()
    end
    if (not __pytra_contains(_TYPE_STATE, "ranges_dirty")) then
        _TYPE_STATE[((("ranges_dirty") < 0) and (#(_TYPE_STATE) + ("ranges_dirty") + 1) or (("ranges_dirty") + 1))] = 1
    end
    if (#(_TYPE_IDS) > 0) then
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

function _normalize_base_type_id(base_type_id)
    _ensure_builtins()
    if (not false) then
        error("base type_id must be int")
    end
    if (not __pytra_contains(_TYPE_BASE, base_type_id)) then
        error(("unknown base type_id: " .. tostring(base_type_id)))
    end
    return base_type_id
end

function py_tid_register_class_type(base_type_id)
    _ensure_builtins()
    local base_tid = _normalize_base_type_id(base_type_id)
    
    local tid = _TYPE_STATE[((("next_user_type_id") < 0) and (#(_TYPE_STATE) + ("next_user_type_id") + 1) or (("next_user_type_id") + 1))]
    while __pytra_contains(_TYPE_BASE, tid) do
        tid = tid + 1
    end
    _TYPE_STATE[((("next_user_type_id") < 0) and (#(_TYPE_STATE) + ("next_user_type_id") + 1) or (("next_user_type_id") + 1))] = (tid + 1)
    
    _register_type_node(tid, base_tid)
    _mark_type_ranges_dirty()
    return tid
end

function py_tid_register_known_class_type(type_id, base_type_id)
    _ensure_builtins()
    if (not false) then
        error("type_id must be int")
    end
    if (type_id < _tid_user_base()) then
        error(("user type_id must be >= " .. tostring(_tid_user_base())))
    end
    local base_tid = _normalize_base_type_id(base_type_id)
    if __pytra_contains(_TYPE_BASE, type_id) then
        if (_TYPE_BASE[(((type_id) < 0) and (#(_TYPE_BASE) + (type_id) + 1) or ((type_id) + 1))] ~= base_tid) then
            error("type_id already registered with different base")
        end
        return type_id
    end
    _register_type_node(type_id, base_tid)
    local next_user_type_id = _TYPE_STATE[((("next_user_type_id") < 0) and (#(_TYPE_STATE) + ("next_user_type_id") + 1) or (("next_user_type_id") + 1))]
    if (type_id >= next_user_type_id) then
        _TYPE_STATE[((("next_user_type_id") < 0) and (#(_TYPE_STATE) + ("next_user_type_id") + 1) or (("next_user_type_id") + 1))] = (type_id + 1)
    end
    _mark_type_ranges_dirty()
    return type_id
end

function _try_runtime_tagged_type_id(value)
    local tagged = __pytra_obj_type_id(value)
    if false then
        local tagged_id = __pytra_int(tagged)
        if __pytra_contains(_TYPE_BASE, tagged_id) then
            return tagged_id
        end
    end
    return (-1)
end

function py_tid_runtime_type_id(value)
    _ensure_builtins()
    if (value == nil) then
        return _tid_none()
    end
    if false then
        return _tid_bool()
    end
    if false then
        return _tid_int()
    end
    if false then
        return _tid_float()
    end
    if false then
        return _tid_str()
    end
    if false then
        return _tid_list()
    end
    if false then
        return _tid_dict()
    end
    if false then
        return _tid_set()
    end
    local tagged = _try_runtime_tagged_type_id(value)
    if (tagged >= 0) then
        return tagged
    end
    return _tid_object()
end

function py_tid_is_subtype(actual_type_id, expected_type_id)
    _ensure_builtins()
    _ensure_type_ranges()
    if (not __pytra_contains(_TYPE_ORDER, actual_type_id)) then
        return false
    end
    if (not __pytra_contains(_TYPE_ORDER, expected_type_id)) then
        return false
    end
    local actual_order = _TYPE_ORDER[(((actual_type_id) < 0) and (#(_TYPE_ORDER) + (actual_type_id) + 1) or ((actual_type_id) + 1))]
    local expected_min = _TYPE_MIN[(((expected_type_id) < 0) and (#(_TYPE_MIN) + (expected_type_id) + 1) or ((expected_type_id) + 1))]
    local expected_max = _TYPE_MAX[(((expected_type_id) < 0) and (#(_TYPE_MAX) + (expected_type_id) + 1) or ((expected_type_id) + 1))]
    return ((expected_min <= actual_order) and (actual_order <= expected_max))
end

function py_tid_issubclass(actual_type_id, expected_type_id)
    return py_tid_is_subtype(actual_type_id, expected_type_id)
end

function py_tid_isinstance(value, expected_type_id)
    return py_tid_is_subtype(__pytra_obj_type_id(value), expected_type_id)
end

function _py_reset_type_registry_for_test()
    _TYPE_IDS:clear()
    _TYPE_BASE:clear()
    _TYPE_CHILDREN:clear()
    _TYPE_ORDER:clear()
    _TYPE_MIN:clear()
    _TYPE_MAX:clear()
    _TYPE_STATE:clear()
    _TYPE_STATE[((("next_user_type_id") < 0) and (#(_TYPE_STATE) + ("next_user_type_id") + 1) or (("next_user_type_id") + 1))] = _tid_user_base()
    _TYPE_STATE[((("ranges_dirty") < 0) and (#(_TYPE_STATE) + ("ranges_dirty") + 1) or (("ranges_dirty") + 1))] = 1
    _ensure_builtins()
end
