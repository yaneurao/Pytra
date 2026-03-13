-- AUTO-GENERATED FILE. DO NOT EDIT.
-- source: src/pytra/built_in/predicates.py
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

function py_any(values)
    local i = 0
    local n = #(values)
    while (i < n) do
        if __pytra_truthy(values[(((i) < 0) and (#(values) + (i) + 1) or ((i) + 1))]) then
            return true
        end
        i = i + 1
    end
    return false
end

function py_all(values)
    local i = 0
    local n = #(values)
    while (i < n) do
        if (not __pytra_truthy(values[(((i) < 0) and (#(values) + (i) + 1) or ((i) + 1))])) then
            return false
        end
        i = i + 1
    end
    return true
end
