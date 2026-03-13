-- AUTO-GENERATED FILE. DO NOT EDIT.
-- source: src/pytra/built_in/iter_ops.py
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

function py_reversed_object(values)
    local out = {  }
    for _, value in ipairs(values) do
        table.insert(out, value)
    end
    return reversed(out)
end

function py_enumerate_object(values, start)
    local out = {  }
    local i = start
    for _, value in ipairs(values) do
        table.insert(out, { i, value })
        i = i + 1
    end
    return out
end
