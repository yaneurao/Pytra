-- AUTO-GENERATED FILE. DO NOT EDIT.
-- source: src/pytra/std/os.py
-- generated-by: tools/gen_runtime_from_manifest.py

dofile((debug.getinfo(1, "S").source:sub(2):match("^(.*[\\/])") or "") .. "py_runtime.lua")

local path = { join = function(a, b) return tostring(a) .. '/' .. tostring(b) end, dirname = function(_p) return '' end, basename = function(p) return tostring(p) end, splitext = function(p) return { tostring(p), '' } end, abspath = function(p) return tostring(p) end, exists = function(_p) return false end }

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

function getcwd()
    return __os:getcwd()
end

function mkdir(p)
    __os:mkdir(p)
end

function makedirs(p, exist_ok)
    __os:makedirs(p, exist_ok)
end
