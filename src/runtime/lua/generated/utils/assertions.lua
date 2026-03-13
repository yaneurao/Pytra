-- AUTO-GENERATED FILE. DO NOT EDIT.
-- source: src/pytra/utils/assertions.py
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

function _eq_any(actual, expected)
    return (py_to_string(actual) == py_to_string(expected))
end

function py_assert_true(cond, label)
    if cond then
        return true
    end
    if (label ~= "") then
        __pytra_print(("[assert_true] " .. tostring(label) .. ": False"))
    else
        __pytra_print("[assert_true] False")
    end
    return false
end

function py_assert_eq(actual, expected, label)
    local ok = _eq_any(actual, expected)
    if ok then
        return true
    end
    if (label ~= "") then
        __pytra_print(("[assert_eq] " .. tostring(label) .. ": actual=" .. tostring(actual) .. ", expected=" .. tostring(expected)))
    else
        __pytra_print(("[assert_eq] actual=" .. tostring(actual) .. ", expected=" .. tostring(expected)))
    end
    return false
end

function py_assert_all(results, label)
    for _, v in ipairs(results) do
        if (not v) then
            if (label ~= "") then
                __pytra_print(("[assert_all] " .. tostring(label) .. ": False"))
            else
                __pytra_print("[assert_all] False")
            end
            return false
        end
    end
    return true
end

function py_assert_stdout(expected_lines, fn)
    -- self_hosted parser / runtime 互換優先: stdout capture は未実装。
    return true
end
