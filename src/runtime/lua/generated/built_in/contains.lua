-- AUTO-GENERATED FILE. DO NOT EDIT.
-- source: src/pytra/built_in/contains.py
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

function py_contains_dict_object(values, key)
    local needle = tostring(key)
    for _, cur in ipairs(values) do
        if (cur == needle) then
            return true
        end
    end
    return false
end

function py_contains_list_object(values, key)
    for _, cur in ipairs(values) do
        if (cur == key) then
            return true
        end
    end
    return false
end

function py_contains_set_object(values, key)
    for _, cur in ipairs(values) do
        if (cur == key) then
            return true
        end
    end
    return false
end

function py_contains_str_object(values, key)
    local needle = tostring(key)
    local haystack = tostring(values)
    local n = #(haystack)
    local m = #(needle)
    if (m == 0) then
        return true
    end
    local i = 0
    local last = (n - m)
    while (i <= last) do
        local j = 0
        local ok = true
        while (j < m) do
            if (string.sub(haystack, ((((i + j)) < 0) and (#(haystack) + ((i + j)) + 1) or (((i + j)) + 1)), ((((i + j)) < 0) and (#(haystack) + ((i + j)) + 1) or (((i + j)) + 1))) ~= string.sub(needle, (((j) < 0) and (#(needle) + (j) + 1) or ((j) + 1)), (((j) < 0) and (#(needle) + (j) + 1) or ((j) + 1)))) then
                ok = false
                break
            end
            j = j + 1
        end
        if ok then
            return true
        end
        i = i + 1
    end
    return false
end
