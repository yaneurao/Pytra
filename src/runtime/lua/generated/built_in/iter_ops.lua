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
    local i = (#(values) - 1)
    while (i >= 0) do
        table.insert(out, values[(((i) < 0) and (#(values) + (i) + 1) or ((i) + 1))])
        i = i - 1
    end
    return out
end

function py_enumerate_object(values, start)
    local out = {  }
    local i = 0
    local n = #(values)
    while (i < n) do
        table.insert(out, { (start + i), values[(((i) < 0) and (#(values) + (i) + 1) or ((i) + 1))] })
        i = i + 1
    end
    return out
end
