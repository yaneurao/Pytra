-- AUTO-GENERATED FILE. DO NOT EDIT.
-- source: src/pytra/built_in/string_ops.py
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

function _is_space(ch)
    return ((ch == " ") or (ch == "\t") or (ch == "\n") or (ch == "\r"))
end

function _contains_char(chars, ch)
    local i = 0
    local n = #(chars)
    while (i < n) do
        if (string.sub(chars, (((i) < 0) and (#(chars) + (i) + 1) or ((i) + 1)), (((i) < 0) and (#(chars) + (i) + 1) or ((i) + 1))) == ch) then
            return true
        end
        i = i + 1
    end
    return false
end

function _normalize_index(idx, n)
    local out = idx
    if (out < 0) then
        out = out + n
    end
    if (out < 0) then
        out = 0
    end
    if (out > n) then
        out = n
    end
    return out
end

function py_join(sep, parts)
    local n = #(parts)
    if (n == 0) then
        return ""
    end
    local out = ""
    local i = 0
    while (i < n) do
        if (i > 0) then
            out = out .. sep
        end
        out = out .. parts[(((i) < 0) and (#(parts) + (i) + 1) or ((i) + 1))]
        i = i + 1
    end
    return out
end

function py_split(s, sep, maxsplit)
    local out = {  }
    if (sep == "") then
        table.insert(out, s)
        return out
    end
    local pos = 0
    local splits = 0
    local n = #(s)
    local m = #(sep)
    local unlimited = (maxsplit < 0)
    while true do
        if ((not unlimited) and (splits >= maxsplit)) then
            break
        end
        local at = py_find_window(s, sep, pos, n)
        if (at < 0) then
            break
        end
        table.insert(out, string.sub(s, (pos) + 1, at))
        pos = (at + m)
        splits = splits + 1
    end
    table.insert(out, string.sub(s, (pos) + 1, n))
    return out
end

function py_splitlines(s)
    local out = {  }
    local n = #(s)
    local start = 0
    local i = 0
    while (i < n) do
        local ch = string.sub(s, (((i) < 0) and (#(s) + (i) + 1) or ((i) + 1)), (((i) < 0) and (#(s) + (i) + 1) or ((i) + 1)))
        if ((ch == "\n") or (ch == "\r")) then
            table.insert(out, string.sub(s, (start) + 1, i))
            if ((ch == "\r") and ((i + 1) < n) and (string.sub(s, ((((i + 1)) < 0) and (#(s) + ((i + 1)) + 1) or (((i + 1)) + 1)), ((((i + 1)) < 0) and (#(s) + ((i + 1)) + 1) or (((i + 1)) + 1))) == "\n")) then
                i = i + 1
            end
            i = i + 1
            start = i
            goto __pytra_continue_4
        end
        i = i + 1
        ::__pytra_continue_4::
    end
    if (start < n) then
        table.insert(out, string.sub(s, (start) + 1, n))
    else
        if (n > 0) then
            local last = string.sub(s, ((((n - 1)) < 0) and (#(s) + ((n - 1)) + 1) or (((n - 1)) + 1)), ((((n - 1)) < 0) and (#(s) + ((n - 1)) + 1) or (((n - 1)) + 1)))
            if ((last == "\n") or (last == "\r")) then
                table.insert(out, "")
            end
        end
    end
    return out
end

function py_count(s, needle)
    if (needle == "") then
        return (#(s) + 1)
    end
    local out = 0
    local pos = 0
    local n = #(s)
    local m = #(needle)
    while true do
        local at = py_find_window(s, needle, pos, n)
        if (at < 0) then
            return out
        end
        out = out + 1
        pos = (at + m)
    end
end

function py_lstrip(s)
    local i = 0
    local n = #(s)
    while ((i < n) and _is_space(string.sub(s, (((i) < 0) and (#(s) + (i) + 1) or ((i) + 1)), (((i) < 0) and (#(s) + (i) + 1) or ((i) + 1))))) do
        i = i + 1
    end
    return string.sub(s, (i) + 1, n)
end

function py_lstrip_chars(s, chars)
    local i = 0
    local n = #(s)
    while ((i < n) and _contains_char(chars, string.sub(s, (((i) < 0) and (#(s) + (i) + 1) or ((i) + 1)), (((i) < 0) and (#(s) + (i) + 1) or ((i) + 1))))) do
        i = i + 1
    end
    return string.sub(s, (i) + 1, n)
end

function py_rstrip(s)
    local n = #(s)
    local i = (n - 1)
    while ((i >= 0) and _is_space(string.sub(s, (((i) < 0) and (#(s) + (i) + 1) or ((i) + 1)), (((i) < 0) and (#(s) + (i) + 1) or ((i) + 1))))) do
        i = i - 1
    end
    return string.sub(s, (0) + 1, (i + 1))
end

function py_rstrip_chars(s, chars)
    local n = #(s)
    local i = (n - 1)
    while ((i >= 0) and _contains_char(chars, string.sub(s, (((i) < 0) and (#(s) + (i) + 1) or ((i) + 1)), (((i) < 0) and (#(s) + (i) + 1) or ((i) + 1))))) do
        i = i - 1
    end
    return string.sub(s, (0) + 1, (i + 1))
end

function py_strip(s)
    return py_rstrip(py_lstrip(s))
end

function py_strip_chars(s, chars)
    return py_rstrip_chars(py_lstrip_chars(s, chars), chars)
end

function py_startswith(s, prefix)
    local n = #(s)
    local m = #(prefix)
    if (m > n) then
        return false
    end
    local i = 0
    while (i < m) do
        if (string.sub(s, (((i) < 0) and (#(s) + (i) + 1) or ((i) + 1)), (((i) < 0) and (#(s) + (i) + 1) or ((i) + 1))) ~= string.sub(prefix, (((i) < 0) and (#(prefix) + (i) + 1) or ((i) + 1)), (((i) < 0) and (#(prefix) + (i) + 1) or ((i) + 1)))) then
            return false
        end
        i = i + 1
    end
    return true
end

function py_endswith(s, suffix)
    local n = #(s)
    local m = #(suffix)
    if (m > n) then
        return false
    end
    local i = 0
    local base = (n - m)
    while (i < m) do
        if (string.sub(s, ((((base + i)) < 0) and (#(s) + ((base + i)) + 1) or (((base + i)) + 1)), ((((base + i)) < 0) and (#(s) + ((base + i)) + 1) or (((base + i)) + 1))) ~= string.sub(suffix, (((i) < 0) and (#(suffix) + (i) + 1) or ((i) + 1)), (((i) < 0) and (#(suffix) + (i) + 1) or ((i) + 1)))) then
            return false
        end
        i = i + 1
    end
    return true
end

function py_find(s, needle)
    return py_find_window(s, needle, 0, #(s))
end

function py_find_window(s, needle, start, _end)
    local n = #(s)
    local m = #(needle)
    local lo = _normalize_index(start, n)
    local up = _normalize_index(_end, n)
    if (up < lo) then
        return (-1)
    end
    if (m == 0) then
        return lo
    end
    local i = lo
    local last = (up - m)
    while (i <= last) do
        local j = 0
        local ok = true
        while (j < m) do
            if (string.sub(s, ((((i + j)) < 0) and (#(s) + ((i + j)) + 1) or (((i + j)) + 1)), ((((i + j)) < 0) and (#(s) + ((i + j)) + 1) or (((i + j)) + 1))) ~= string.sub(needle, (((j) < 0) and (#(needle) + (j) + 1) or ((j) + 1)), (((j) < 0) and (#(needle) + (j) + 1) or ((j) + 1)))) then
                ok = false
                break
            end
            j = j + 1
        end
        if ok then
            return i
        end
        i = i + 1
    end
    return (-1)
end

function py_rfind(s, needle)
    return py_rfind_window(s, needle, 0, #(s))
end

function py_rfind_window(s, needle, start, _end)
    local n = #(s)
    local m = #(needle)
    local lo = _normalize_index(start, n)
    local up = _normalize_index(_end, n)
    if (up < lo) then
        return (-1)
    end
    if (m == 0) then
        return up
    end
    local i = (up - m)
    while (i >= lo) do
        local j = 0
        local ok = true
        while (j < m) do
            if (string.sub(s, ((((i + j)) < 0) and (#(s) + ((i + j)) + 1) or (((i + j)) + 1)), ((((i + j)) < 0) and (#(s) + ((i + j)) + 1) or (((i + j)) + 1))) ~= string.sub(needle, (((j) < 0) and (#(needle) + (j) + 1) or ((j) + 1)), (((j) < 0) and (#(needle) + (j) + 1) or ((j) + 1)))) then
                ok = false
                break
            end
            j = j + 1
        end
        if ok then
            return i
        end
        i = i - 1
    end
    return (-1)
end

function py_replace(s, oldv, newv)
    if (oldv == "") then
        return s
    end
    local out = ""
    local n = #(s)
    local m = #(oldv)
    local i = 0
    while (i < n) do
        if (((i + m) <= n) and (py_find_window(s, oldv, i, (i + m)) == i)) then
            out = out .. newv
            i = i + m
        else
            out = out .. string.sub(s, (((i) < 0) and (#(s) + (i) + 1) or ((i) + 1)), (((i) < 0) and (#(s) + (i) + 1) or ((i) + 1)))
            i = i + 1
        end
    end
    return out
end
