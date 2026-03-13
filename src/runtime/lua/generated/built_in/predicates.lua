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
    for _, value in ipairs(values) do
        if __pytra_truthy(value) then
            return true
        end
    end
    return false
end

function py_all(values)
    for _, value in ipairs(values) do
        if (not __pytra_truthy(value)) then
            return false
        end
    end
    return true
end
