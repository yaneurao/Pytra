-- AUTO-GENERATED FILE. DO NOT EDIT.
-- source: src/pytra/built_in/zip_ops.py
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

function zip(lhs, rhs)
    local out = {  }
    local i = 0
    local n = #(lhs)
    if (#(rhs) < n) then
        n = #(rhs)
    end
    while (i < n) do
        table.insert(out, { lhs[(((i) < 0) and (#(lhs) + (i) + 1) or ((i) + 1))], rhs[(((i) < 0) and (#(rhs) + (i) + 1) or ((i) + 1))] })
        i = i + 1
    end
    return out
end
