-- AUTO-GENERATED FILE. DO NOT EDIT.
-- source: src/pytra/built_in/numeric_ops.py
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

function sum(values)
    if (#(values) == 0) then
        return 0
    end
    local acc = (values[1] - values[1])
    local i = 0
    local n = #(values)
    while (i < n) do
        acc = acc + values[(((i) < 0) and (#(values) + (i) + 1) or ((i) + 1))]
        i = i + 1
    end
    return acc
end

function py_min(a, b)
    if (a < b) then
        return a
    end
    return b
end

function py_max(a, b)
    if (a > b) then
        return a
    end
    return b
end
