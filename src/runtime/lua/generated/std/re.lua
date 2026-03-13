-- AUTO-GENERATED FILE. DO NOT EDIT.
-- source: src/pytra/std/re.py
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

local function __pytra_isinstance(obj, class_tbl)
    if type(obj) ~= "table" then
        return false
    end
    local mt = getmetatable(obj)
    while mt do
        if mt == class_tbl then
            return true
        end
        local parent = getmetatable(mt)
        if type(parent) == "table" and type(parent.__index) == "table" then
            mt = parent.__index
        else
            mt = nil
        end
    end
    return false
end

S = 1
Match = {}
Match.__index = Match

function Match.new(text, groups)
    local self = setmetatable({}, Match)
    self._text = text
    self._groups = groups
    return self
end

function Match:group(idx)
    if (idx == 0) then
        return self._text
    end
    if ((idx < 0) or (idx > #(self._groups))) then
        error(IndexError("group index out of range"))
    end
    return self._groups[((((idx - 1)) < 0) and (#(self._groups) + ((idx - 1)) + 1) or (((idx - 1)) + 1))]
end

function group(m, idx)
    if (m == nil) then
        return ""
    end
    local mm = m
    return mm:group(idx)
end

function strip_group(m, idx)
    return py_strip(group(m, idx))
end

function _is_ident(s)
    if (s == "") then
        return false
    end
    local h = string.sub(s, (0) + 1, 1)
    local is_head_alpha = (("a" <= h) or ("A" <= h))
    if (not (is_head_alpha or (h == "_"))) then
        return false
    end
    for _, ch in ipairs(string.sub(s, (1) + 1, #s)) do
        local is_alpha = (("a" <= ch) or ("A" <= ch))
        local is_digit = ("0" <= ch)
        if (not (is_alpha or is_digit or (ch == "_"))) then
            return false
        end
    end
    return true
end

function _is_dotted_ident(s)
    if (s == "") then
        return false
    end
    local part = ""
    for _, ch in ipairs(s) do
        if (ch == ".") then
            if (not _is_ident(part)) then
                return false
            end
            part = ""
            goto __pytra_continue_2
        end
        part = part .. ch
        ::__pytra_continue_2::
    end
    if (not _is_ident(part)) then
        return false
    end
    if (part == "") then
        return false
    end
    return true
end

function _strip_suffix_colon(s)
    local t = py_rstrip(s)
    if (#(t) == 0) then
        return ""
    end
    if (string.sub(t, ((-1)) + 1, #t) ~= ":") then
        return ""
    end
    return string.sub(t, (0) + 1, (-1))
end

function _is_space_ch(ch)
    if (ch == " ") then
        return true
    end
    if (ch == "\t") then
        return true
    end
    if (ch == "\r") then
        return true
    end
    if (ch == "\n") then
        return true
    end
    return false
end

function _is_alnum_or_underscore(ch)
    local is_alpha = (("a" <= ch) or ("A" <= ch))
    local is_digit = ("0" <= ch)
    if (is_alpha or is_digit) then
        return true
    end
    return (ch == "_")
end

function _skip_spaces(t, i)
    while (i < #(t)) do
        if (not _is_space_ch(string.sub(t, (i) + 1, (i + 1)))) then
            return i
        end
        i = i + 1
    end
    return i
end

function match(pattern, text, flags)
    -- ^([A-Za-z_][A-Za-z0-9_]*)\[(.*)\]$
    if (pattern == "^([A-Za-z_][A-Za-z0-9_]*)\\[(.*)\\]$") then
        if (not py_endswith(text, "]")) then
            return nil
        end
        local i = py_find(text, "[")
        if (i <= 0) then
            return nil
        end
        local head = string.sub(text, (0) + 1, i)
        if (not _is_ident(head)) then
            return nil
        end
        return Match.new(text, { head, string.sub(text, ((i + 1)) + 1, (-1)) })
    end
    if (pattern == "^def\\s+([A-Za-z_][A-Za-z0-9_]*)\\((.*)\\)\\s*(?:->\\s*(.+)\\s*)?:\\s*$") then
        local t = _strip_suffix_colon(text)
        if (t == "") then
            return nil
        end
        i = 0
        if (not py_startswith(t, "def")) then
            return nil
        end
        i = 3
        if ((i >= #(t)) or (not _is_space_ch(string.sub(t, (i) + 1, (i + 1))))) then
            return nil
        end
        i = _skip_spaces(t, i)
        local j = i
        while ((j < #(t)) and _is_alnum_or_underscore(string.sub(t, (j) + 1, (j + 1)))) do
            j = j + 1
        end
        local name = string.sub(t, (i) + 1, j)
        if (not _is_ident(name)) then
            return nil
        end
        local k = j
        k = _skip_spaces(t, k)
        if ((k >= #(t)) or (string.sub(t, (k) + 1, (k + 1)) ~= "(")) then
            return nil
        end
        local r = py_rfind(t, ")")
        if (r <= k) then
            return nil
        end
        local args = string.sub(t, ((k + 1)) + 1, r)
        local tail = py_strip(string.sub(t, ((r + 1)) + 1, #t))
        if (tail == "") then
            return Match.new(text, { name, args, "" })
        end
        if (not py_startswith(tail, "->")) then
            return nil
        end
        local ret = py_strip(string.sub(tail, (2) + 1, #tail))
        if (ret == "") then
            return nil
        end
        return Match.new(text, { name, args, ret })
    end
    if (pattern == "^([A-Za-z_][A-Za-z0-9_]*)\\s*:\\s*([^=]+?)(?:\\s*=\\s*(.+))?$") then
        local c = py_find(text, ":")
        if (c <= 0) then
            return nil
        end
        name = py_strip(string.sub(text, (0) + 1, c))
        if (not _is_ident(name)) then
            return nil
        end
        local rhs = string.sub(text, ((c + 1)) + 1, #text)
        local eq = py_find(rhs, "=")
        if (eq < 0) then
            local ann = py_strip(rhs)
            if (ann == "") then
                return nil
            end
            return Match.new(text, { name, ann, "" })
        end
        ann = py_strip(string.sub(rhs, (0) + 1, eq))
        local val = py_strip(string.sub(rhs, ((eq + 1)) + 1, #rhs))
        if ((ann == "") or (val == "")) then
            return nil
        end
        return Match.new(text, { name, ann, val })
    end
    if (pattern == "^[A-Za-z_][A-Za-z0-9_]*$") then
        if _is_ident(text) then
            return Match.new(text, {  })
        end
        return nil
    end
    if (pattern == "^class\\s+([A-Za-z_][A-Za-z0-9_]*)(?:\\(([A-Za-z_][A-Za-z0-9_]*)\\))?\\s*:\\s*$") then
        t = _strip_suffix_colon(text)
        if (t == "") then
            return nil
        end
        if (not py_startswith(t, "class")) then
            return nil
        end
        i = 5
        if ((i >= #(t)) or (not _is_space_ch(string.sub(t, (i) + 1, (i + 1))))) then
            return nil
        end
        i = _skip_spaces(t, i)
        j = i
        while ((j < #(t)) and _is_alnum_or_underscore(string.sub(t, (j) + 1, (j + 1)))) do
            j = j + 1
        end
        local name = string.sub(t, (i) + 1, j)
        if (not _is_ident(name)) then
            return nil
        end
        local tail = py_strip(string.sub(t, (j) + 1, #t))
        if (tail == "") then
            return Match.new(text, { name, "" })
        end
        if (not (py_startswith(tail, "(") and py_endswith(tail, ")"))) then
            return nil
        end
        local base = py_strip(string.sub(tail, (1) + 1, (-1)))
        if (not _is_ident(base)) then
            return nil
        end
        return Match.new(text, { name, base })
    end
    if (pattern == "^(any|all)\\((.+)\\)$") then
        if (py_startswith(text, "any(") and py_endswith(text, ")") and (#(text) > 5)) then
            return Match.new(text, { "any", string.sub(text, (4) + 1, (-1)) })
        end
        if (py_startswith(text, "all(") and py_endswith(text, ")") and (#(text) > 5)) then
            return Match.new(text, { "all", string.sub(text, (4) + 1, (-1)) })
        end
        return nil
    end
    if (pattern == "^\\[\\s*([A-Za-z_][A-Za-z0-9_]*)\\s+for\\s+([A-Za-z_][A-Za-z0-9_]*)\\s+in\\s+(.+)\\]$") then
        if (not (py_startswith(text, "[") and py_endswith(text, "]"))) then
            return nil
        end
        local inner = py_strip(string.sub(text, (1) + 1, (-1)))
        local m1 = " for "
        local m2 = " in "
        local i = py_find(inner, m1)
        if (i < 0) then
            return nil
        end
        local expr = py_strip(string.sub(inner, (0) + 1, i))
        local rest = string.sub(inner, ((i + #(m1))) + 1, #inner)
        local j = py_find(rest, m2)
        if (j < 0) then
            return nil
        end
        local var = py_strip(string.sub(rest, (0) + 1, j))
        local it = py_strip(string.sub(rest, ((j + #(m2))) + 1, #rest))
        if ((not _is_ident(expr)) or (not _is_ident(var)) or (it == "")) then
            return nil
        end
        return Match.new(text, { expr, var, it })
    end
    if (pattern == "^for\\s+(.+)\\s+in\\s+(.+):$") then
        t = _strip_suffix_colon(text)
        if ((t == "") or (not py_startswith(t, "for"))) then
            return nil
        end
        local rest = py_strip(string.sub(t, (3) + 1, #t))
        local i = py_find(rest, " in ")
        if (i < 0) then
            return nil
        end
        local left = py_strip(string.sub(rest, (0) + 1, i))
        local right = py_strip(string.sub(rest, ((i + 4)) + 1, #rest))
        if ((left == "") or (right == "")) then
            return nil
        end
        return Match.new(text, { left, right })
    end
    if (pattern == "^with\\s+(.+)\\s+as\\s+([A-Za-z_][A-Za-z0-9_]*)\\s*:\\s*$") then
        t = _strip_suffix_colon(text)
        if ((t == "") or (not py_startswith(t, "with"))) then
            return nil
        end
        local rest = py_strip(string.sub(t, (4) + 1, #t))
        local i = py_rfind(rest, " as ")
        if (i < 0) then
            return nil
        end
        local expr = py_strip(string.sub(rest, (0) + 1, i))
        local name = py_strip(string.sub(rest, ((i + 4)) + 1, #rest))
        if ((expr == "") or (not _is_ident(name))) then
            return nil
        end
        return Match.new(text, { expr, name })
    end
    if (pattern == "^except\\s+(.+?)\\s+as\\s+([A-Za-z_][A-Za-z0-9_]*)\\s*:\\s*$") then
        t = _strip_suffix_colon(text)
        if ((t == "") or (not py_startswith(t, "except"))) then
            return nil
        end
        local rest = py_strip(string.sub(t, (6) + 1, #t))
        local i = py_rfind(rest, " as ")
        if (i < 0) then
            return nil
        end
        local exc = py_strip(string.sub(rest, (0) + 1, i))
        local name = py_strip(string.sub(rest, ((i + 4)) + 1, #rest))
        if ((exc == "") or (not _is_ident(name))) then
            return nil
        end
        return Match.new(text, { exc, name })
    end
    if (pattern == "^except\\s+(.+?)\\s*:\\s*$") then
        t = _strip_suffix_colon(text)
        if ((t == "") or (not py_startswith(t, "except"))) then
            return nil
        end
        local rest = py_strip(string.sub(t, (6) + 1, #t))
        if (rest == "") then
            return nil
        end
        return Match.new(text, { rest })
    end
    if (pattern == "^([A-Za-z_][A-Za-z0-9_]*(?:\\.[A-Za-z_][A-Za-z0-9_]*)?)\\s*:\\s*(.+)$") then
        c = py_find(text, ":")
        if (c <= 0) then
            return nil
        end
        local target = py_strip(string.sub(text, (0) + 1, c))
        local ann = py_strip(string.sub(text, ((c + 1)) + 1, #text))
        if ((ann == "") or (not _is_dotted_ident(target))) then
            return nil
        end
        return Match.new(text, { target, ann })
    end
    if (pattern == "^([A-Za-z_][A-Za-z0-9_]*(?:\\.[A-Za-z_][A-Za-z0-9_]*)?)\\s*:\\s*([^=]+?)\\s*=\\s*(.+)$") then
        c = py_find(text, ":")
        if (c <= 0) then
            return nil
        end
        local target = py_strip(string.sub(text, (0) + 1, c))
        local rhs = string.sub(text, ((c + 1)) + 1, #text)
        local eq = py_find(rhs, "=")
        if (eq < 0) then
            return nil
        end
        local ann = py_strip(string.sub(rhs, (0) + 1, eq))
        local expr = py_strip(string.sub(rhs, ((eq + 1)) + 1, #rhs))
        if ((not _is_dotted_ident(target)) or (ann == "") or (expr == "")) then
            return nil
        end
        return Match.new(text, { target, ann, expr })
    end
    if (pattern == "^([A-Za-z_][A-Za-z0-9_]*(?:\\.[A-Za-z_][A-Za-z0-9_]*)?)\\s*(\\+=|-=|\\*=|/=|//=|%=|&=|\\|=|\\^=|<<=|>>=)\\s*(.+)$") then
        local ops = { "<<=", ">>=", "+=", "-=", "*=", "/=", "//=", "%=", "&=", "|=", "^=" }
        local op_pos = (-1)
        local op_txt = ""
        for _, op in ipairs(ops) do
            local p = py_find(text, op)
            if ((p >= 0) and ((op_pos < 0) or (p < op_pos))) then
                op_pos = p
                op_txt = op
            end
        end
        if (op_pos < 0) then
            return nil
        end
        local left = py_strip(string.sub(text, (0) + 1, op_pos))
        local right = py_strip(string.sub(text, ((op_pos + #(op_txt))) + 1, #text))
        if ((right == "") or (not _is_dotted_ident(left))) then
            return nil
        end
        return Match.new(text, { left, op_txt, right })
    end
    if (pattern == "^([A-Za-z_][A-Za-z0-9_]*)\\s*,\\s*([A-Za-z_][A-Za-z0-9_]*)\\s*=\\s*(.+)$") then
        local eq = py_find(text, "=")
        if (eq < 0) then
            return nil
        end
        local left = string.sub(text, (0) + 1, eq)
        local right = py_strip(string.sub(text, ((eq + 1)) + 1, #text))
        if (right == "") then
            return nil
        end
        local c = py_find(left, ",")
        if (c < 0) then
            return nil
        end
        local a = py_strip(string.sub(left, (0) + 1, c))
        local b = py_strip(string.sub(left, ((c + 1)) + 1, #left))
        if ((not _is_ident(a)) or (not _is_ident(b))) then
            return nil
        end
        return Match.new(text, { a, b, right })
    end
    if (pattern == "^if\\s+__name__\\s*==\\s*[\\\"']__main__[\\\"']\\s*:\\s*$") then
        t = _strip_suffix_colon(text)
        if (t == "") then
            return nil
        end
        local rest = py_strip(t)
        if (not py_startswith(rest, "if")) then
            return nil
        end
        rest = py_strip(string.sub(rest, (2) + 1, #rest))
        if (not py_startswith(rest, "__name__")) then
            return nil
        end
        rest = py_strip(string.sub(rest, (#("__name__")) + 1, #rest))
        if (not py_startswith(rest, "==")) then
            return nil
        end
        rest = py_strip(string.sub(rest, (2) + 1, #rest))
        if ((rest == "\"__main__\"") or (rest == "'__main__'")) then
            return Match.new(text, {  })
        end
        return nil
    end
    if (pattern == "^import\\s+(.+)$") then
        if (not py_startswith(text, "import")) then
            return nil
        end
        if (#(text) <= 6) then
            return nil
        end
        if (not _is_space_ch(string.sub(text, (6) + 1, 7))) then
            return nil
        end
        local rest = py_strip(string.sub(text, (7) + 1, #text))
        if (rest == "") then
            return nil
        end
        return Match.new(text, { rest })
    end
    if (pattern == "^([A-Za-z_][A-Za-z0-9_\\.]*)(?:\\s+as\\s+([A-Za-z_][A-Za-z0-9_]*))?$") then
        local parts = py_split(text, " as ", -1)
        if (#(parts) == 1) then
            local name = py_strip(parts[1])
            if (not _is_dotted_ident(name)) then
                return nil
            end
            return Match.new(text, { name, "" })
        end
        if (#(parts) == 2) then
            local name = py_strip(parts[1])
            local alias = py_strip(parts[2])
            if ((not _is_dotted_ident(name)) or (not _is_ident(alias))) then
                return nil
            end
            return Match.new(text, { name, alias })
        end
        return nil
    end
    if (pattern == "^from\\s+([A-Za-z_][A-Za-z0-9_\\.]*)\\s+import\\s+(.+)$") then
        if (not py_startswith(text, "from ")) then
            return nil
        end
        local rest = string.sub(text, (5) + 1, #text)
        local i = py_find(rest, " import ")
        if (i < 0) then
            return nil
        end
        local mod = py_strip(string.sub(rest, (0) + 1, i))
        local sym = py_strip(string.sub(rest, ((i + 8)) + 1, #rest))
        if ((not _is_dotted_ident(mod)) or (sym == "")) then
            return nil
        end
        return Match.new(text, { mod, sym })
    end
    if (pattern == "^([A-Za-z_][A-Za-z0-9_]*)(?:\\s+as\\s+([A-Za-z_][A-Za-z0-9_]*))?$") then
        local parts = py_split(text, " as ", -1)
        if (#(parts) == 1) then
            local name = py_strip(parts[1])
            if (not _is_ident(name)) then
                return nil
            end
            return Match.new(text, { name, "" })
        end
        if (#(parts) == 2) then
            local name = py_strip(parts[1])
            local alias = py_strip(parts[2])
            if ((not _is_ident(name)) or (not _is_ident(alias))) then
                return nil
            end
            return Match.new(text, { name, alias })
        end
        return nil
    end
    if (pattern == "^([A-Za-z_][A-Za-z0-9_]*)\\s*:\\s*([^=]+?)\\s*=\\s*(.+)$") then
        c = py_find(text, ":")
        if (c <= 0) then
            return nil
        end
        local name = py_strip(string.sub(text, (0) + 1, c))
        local rhs = string.sub(text, ((c + 1)) + 1, #text)
        local eq = py_find(rhs, "=")
        if (eq < 0) then
            return nil
        end
        local ann = py_strip(string.sub(rhs, (0) + 1, eq))
        local expr = py_strip(string.sub(rhs, ((eq + 1)) + 1, #rhs))
        if ((not _is_ident(name)) or (ann == "") or (expr == "")) then
            return nil
        end
        return Match.new(text, { name, ann, expr })
    end
    if (pattern == "^([A-Za-z_][A-Za-z0-9_]*)\\s*=\\s*(.+)$") then
        local eq = py_find(text, "=")
        if (eq < 0) then
            return nil
        end
        local name = py_strip(string.sub(text, (0) + 1, eq))
        local expr = py_strip(string.sub(text, ((eq + 1)) + 1, #text))
        if ((not _is_ident(name)) or (expr == "")) then
            return nil
        end
        return Match.new(text, { name, expr })
    end
    error(("unsupported regex pattern in pytra.std.re: " .. tostring(pattern)))
end

function sub(pattern, repl, text, flags)
    if (pattern == "\\s+") then
        local out = {  }
        local in_ws = false
        for _, ch in ipairs(text) do
            if ((ch == " ") or (ch == "\t") or (ch == "\n") or (ch == "\r")) then
                if (not in_ws) then
                    table.insert(out, repl)
                    in_ws = true
                end
            else
                table.insert(out, ch)
                in_ws = false
            end
        end
        return py_join("", out)
    end
    if (pattern == "\\s+#.*$") then
        local i = 0
        while (i < #(text)) do
            if ((string.sub(text, (((i) < 0) and (#(text) + (i) + 1) or ((i) + 1)), (((i) < 0) and (#(text) + (i) + 1) or ((i) + 1))) == " ") or (string.sub(text, (((i) < 0) and (#(text) + (i) + 1) or ((i) + 1)), (((i) < 0) and (#(text) + (i) + 1) or ((i) + 1))) == "\t") or (string.sub(text, (((i) < 0) and (#(text) + (i) + 1) or ((i) + 1)), (((i) < 0) and (#(text) + (i) + 1) or ((i) + 1))) == "\n") or (string.sub(text, (((i) < 0) and (#(text) + (i) + 1) or ((i) + 1)), (((i) < 0) and (#(text) + (i) + 1) or ((i) + 1))) == "\r")) then
                local j = (i + 1)
                while ((j < #(text)) and ((string.sub(text, (((j) < 0) and (#(text) + (j) + 1) or ((j) + 1)), (((j) < 0) and (#(text) + (j) + 1) or ((j) + 1))) == " ") or (string.sub(text, (((j) < 0) and (#(text) + (j) + 1) or ((j) + 1)), (((j) < 0) and (#(text) + (j) + 1) or ((j) + 1))) == "\t") or (string.sub(text, (((j) < 0) and (#(text) + (j) + 1) or ((j) + 1)), (((j) < 0) and (#(text) + (j) + 1) or ((j) + 1))) == "\n") or (string.sub(text, (((j) < 0) and (#(text) + (j) + 1) or ((j) + 1)), (((j) < 0) and (#(text) + (j) + 1) or ((j) + 1))) == "\r"))) do
                    j = j + 1
                end
                if ((j < #(text)) and (string.sub(text, (((j) < 0) and (#(text) + (j) + 1) or ((j) + 1)), (((j) < 0) and (#(text) + (j) + 1) or ((j) + 1))) == "#")) then
                    return (string.sub(text, (0) + 1, i) .. repl)
                end
            end
            i = i + 1
        end
        return text
    end
    if (pattern == "[^0-9A-Za-z_]") then
        local out = {  }
        for _, ch in ipairs(text) do
            if (__pytra_str_isalnum(ch) or (ch == "_")) then
                table.insert(out, ch)
            else
                table.insert(out, repl)
            end
        end
        return py_join("", out)
    end
    error(("unsupported regex sub pattern in pytra.std.re: " .. tostring(pattern)))
end
