-- AUTO-GENERATED FILE. DO NOT EDIT.
-- source: src/pytra/built_in/sequence.py
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

function py_range(start, stop, step)
    local out = {  }
    if (step == 0) then
        return out
    end
    if (step > 0) then
        local i = start
        while (i < stop) do
            table.insert(out, i)
            i = i + step
        end
    else
        i = start
        while (i > stop) do
            table.insert(out, i)
            i = i + step
        end
    end
    return out
end

function py_repeat(v, n)
    if (n <= 0) then
        return ""
    end
    local out = ""
    local i = 0
    while (i < n) do
        out = out .. v
        i = i + 1
    end
    return out
end
