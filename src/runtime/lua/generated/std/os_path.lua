-- AUTO-GENERATED FILE. DO NOT EDIT.
-- source: src/pytra/std/os_path.py
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

function join(a, b)
    return py_join(__path, a)
end

function dirname(p)
    return __path:dirname(p)
end

function basename(p)
    return __path:basename(p)
end

function splitext(p)
    return __path:splitext(p)
end

function abspath(p)
    return __path:abspath(p)
end

function exists(p)
    return __path:exists(p)
end
