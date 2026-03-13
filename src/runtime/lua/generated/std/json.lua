-- AUTO-GENERATED FILE. DO NOT EDIT.
-- source: src/pytra/std/json.py
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

local _EMPTY = ""
local _COMMA_NL = ",\n"
local _HEX_DIGITS = "0123456789abcdef"
function _is_ws(ch)
    return ((ch == " ") or (ch == "\t") or (ch == "\r") or (ch == "\n"))
end

function _is_digit(ch)
    return ((ch >= "0") and (ch <= "9"))
end

function _hex_value(ch)
    if ((ch >= "0") and (ch <= "9")) then
        return __pytra_int(ch)
    end
    if ((ch == "a") or (ch == "A")) then
        return 10
    end
    if ((ch == "b") or (ch == "B")) then
        return 11
    end
    if ((ch == "c") or (ch == "C")) then
        return 12
    end
    if ((ch == "d") or (ch == "D")) then
        return 13
    end
    if ((ch == "e") or (ch == "E")) then
        return 14
    end
    if ((ch == "f") or (ch == "F")) then
        return 15
    end
    error("invalid json unicode escape")
end

function _int_from_hex4(hx)
    if (#(hx) ~= 4) then
        error("invalid json unicode escape")
    end
    local v0 = _hex_value(string.sub(hx, (0) + 1, 1))
    local v1 = _hex_value(string.sub(hx, (1) + 1, 2))
    local v2 = _hex_value(string.sub(hx, (2) + 1, 3))
    local v3 = _hex_value(string.sub(hx, (3) + 1, 4))
    return ((((v0 * 4096) + (v1 * 256)) + (v2 * 16)) + v3)
end

function _hex4(code)
    local v = (code % 65536)
    local d3 = (v % 16)
    v = (v // 16)
    local d2 = (v % 16)
    v = (v // 16)
    local d1 = (v % 16)
    v = (v // 16)
    local d0 = (v % 16)
    local p0 = __pytra_slice(_HEX_DIGITS, d0, (d0 + 1))
    local p1 = __pytra_slice(_HEX_DIGITS, d1, (d1 + 1))
    local p2 = __pytra_slice(_HEX_DIGITS, d2, (d2 + 1))
    local p3 = __pytra_slice(_HEX_DIGITS, d3, (d3 + 1))
    return (((p0 .. p1) .. p2) .. p3)
end

function _json_array_items(raw)
    return list(raw)
end

function _json_new_array()
    return list()
end

function _json_obj_require(raw, key)
    for _, __it_2 in ipairs(raw:items()) do
        local k = __it_2[1]
        local value = __it_2[2]
        if (k == key) then
            return value
        end
    end
    error(("json object key not found: " .. key))
end

function _json_indent_value(indent)
    if (indent == nil) then
        error("json indent is required")
    end
    local indent_i = indent
    return indent_i
end

JsonObj = {}
JsonObj.__index = JsonObj

function JsonObj.new(raw)
    local self = setmetatable({}, JsonObj)
    self.raw = raw
    return self
end

function JsonObj:get(key)
    if (not __pytra_contains(self.raw, key)) then
        return nil
    end
    local value = _json_obj_require(self.raw, key)
    return JsonValue.new(value)
end

function JsonObj:get_obj(key)
    if (not __pytra_contains(self.raw, key)) then
        return nil
    end
    local value = _json_obj_require(self.raw, key)
    return JsonValue.new(value):as_obj()
end

function JsonObj:get_arr(key)
    if (not __pytra_contains(self.raw, key)) then
        return nil
    end
    local value = _json_obj_require(self.raw, key)
    return JsonValue.new(value):as_arr()
end

function JsonObj:get_str(key)
    if (not __pytra_contains(self.raw, key)) then
        return nil
    end
    local value = _json_obj_require(self.raw, key)
    return JsonValue.new(value):as_str()
end

function JsonObj:get_int(key)
    if (not __pytra_contains(self.raw, key)) then
        return nil
    end
    local value = _json_obj_require(self.raw, key)
    return JsonValue.new(value):as_int()
end

function JsonObj:get_float(key)
    if (not __pytra_contains(self.raw, key)) then
        return nil
    end
    local value = _json_obj_require(self.raw, key)
    return JsonValue.new(value):as_float()
end

function JsonObj:get_bool(key)
    if (not __pytra_contains(self.raw, key)) then
        return nil
    end
    local value = _json_obj_require(self.raw, key)
    return JsonValue.new(value):as_bool()
end

JsonArr = {}
JsonArr.__index = JsonArr

function JsonArr.new(raw)
    local self = setmetatable({}, JsonArr)
    self.raw = raw
    return self
end

function JsonArr:get(index)
    if ((index < 0) or (index >= #(_json_array_items(self.raw)))) then
        return nil
    end
    return JsonValue.new(_json_array_items(self.raw)[(((index) < 0) and (#(_json_array_items(self.raw)) + (index) + 1) or ((index) + 1))])
end

function JsonArr:get_obj(index)
    if ((index < 0) or (index >= #(_json_array_items(self.raw)))) then
        return nil
    end
    return JsonValue.new(_json_array_items(self.raw)[(((index) < 0) and (#(_json_array_items(self.raw)) + (index) + 1) or ((index) + 1))]):as_obj()
end

function JsonArr:get_arr(index)
    if ((index < 0) or (index >= #(_json_array_items(self.raw)))) then
        return nil
    end
    return JsonValue.new(_json_array_items(self.raw)[(((index) < 0) and (#(_json_array_items(self.raw)) + (index) + 1) or ((index) + 1))]):as_arr()
end

function JsonArr:get_str(index)
    if ((index < 0) or (index >= #(_json_array_items(self.raw)))) then
        return nil
    end
    return JsonValue.new(_json_array_items(self.raw)[(((index) < 0) and (#(_json_array_items(self.raw)) + (index) + 1) or ((index) + 1))]):as_str()
end

function JsonArr:get_int(index)
    if ((index < 0) or (index >= #(_json_array_items(self.raw)))) then
        return nil
    end
    return JsonValue.new(_json_array_items(self.raw)[(((index) < 0) and (#(_json_array_items(self.raw)) + (index) + 1) or ((index) + 1))]):as_int()
end

function JsonArr:get_float(index)
    if ((index < 0) or (index >= #(_json_array_items(self.raw)))) then
        return nil
    end
    return JsonValue.new(_json_array_items(self.raw)[(((index) < 0) and (#(_json_array_items(self.raw)) + (index) + 1) or ((index) + 1))]):as_float()
end

function JsonArr:get_bool(index)
    if ((index < 0) or (index >= #(_json_array_items(self.raw)))) then
        return nil
    end
    return JsonValue.new(_json_array_items(self.raw)[(((index) < 0) and (#(_json_array_items(self.raw)) + (index) + 1) or ((index) + 1))]):as_bool()
end

JsonValue = {}
JsonValue.__index = JsonValue

function JsonValue.new(raw)
    local self = setmetatable({}, JsonValue)
    self.raw = raw
    return self
end

function JsonValue:as_obj()
    local raw = self.raw
    if false then
        local raw_obj = dict(raw)
        return JsonObj.new(raw_obj)
    end
    return nil
end

function JsonValue:as_arr()
    local raw = self.raw
    if false then
        local raw_arr = list(raw)
        return JsonArr.new(raw_arr)
    end
    return nil
end

function JsonValue:as_str()
    local raw = self.raw
    if false then
        return raw
    end
    return nil
end

function JsonValue:as_int()
    local raw = self.raw
    if false then
        return nil
    end
    if false then
        local raw_i = __pytra_int(raw)
        return raw_i
    end
    return nil
end

function JsonValue:as_float()
    local raw = self.raw
    if false then
        local raw_f = __pytra_float(raw)
        return raw_f
    end
    return nil
end

function JsonValue:as_bool()
    local raw = self.raw
    if false then
        local raw_b = __pytra_truthy(raw)
        return raw_b
    end
    return nil
end

_JsonParser = {}
_JsonParser.__index = _JsonParser

function _JsonParser.new(text)
    local self = setmetatable({}, _JsonParser)
    self.text = text
    self.n = #(text)
    self.i = 0
    return self
end

function _JsonParser:parse()
    self:_skip_ws()
    local out = self:_parse_value()
    self:_skip_ws()
    if (self.i ~= self.n) then
        error("invalid json: trailing characters")
    end
    return out
end

function _JsonParser:_skip_ws()
    while ((self.i < self.n) and _is_ws(string.sub(self.text, (((self.i) < 0) and (#(self.text) + (self.i) + 1) or ((self.i) + 1)), (((self.i) < 0) and (#(self.text) + (self.i) + 1) or ((self.i) + 1))))) do
        self.i = self.i + 1
    end
end

function _JsonParser:_parse_value()
    if (self.i >= self.n) then
        error("invalid json: unexpected end")
    end
    local ch = string.sub(self.text, (((self.i) < 0) and (#(self.text) + (self.i) + 1) or ((self.i) + 1)), (((self.i) < 0) and (#(self.text) + (self.i) + 1) or ((self.i) + 1)))
    if (ch == "{") then
        return self:_parse_object()
    end
    if (ch == "[") then
        return self:_parse_array()
    end
    if (ch == "\"") then
        return self:_parse_string()
    end
    if ((ch == "t") and (string.sub(self.text, (self.i) + 1, (self.i + 4)) == "true")) then
        self.i = self.i + 4
        return true
    end
    if ((ch == "f") and (string.sub(self.text, (self.i) + 1, (self.i + 5)) == "false")) then
        self.i = self.i + 5
        return false
    end
    if ((ch == "n") and (string.sub(self.text, (self.i) + 1, (self.i + 4)) == "null")) then
        self.i = self.i + 4
        return nil
    end
    return self:_parse_number()
end

function _JsonParser:_parse_object()
    local out = {}
    self.i = self.i + 1
    self:_skip_ws()
    if ((self.i < self.n) and (string.sub(self.text, (((self.i) < 0) and (#(self.text) + (self.i) + 1) or ((self.i) + 1)), (((self.i) < 0) and (#(self.text) + (self.i) + 1) or ((self.i) + 1))) == "}")) then
        self.i = self.i + 1
        return out
    end
    while true do
        self:_skip_ws()
        if ((self.i >= self.n) or (string.sub(self.text, (((self.i) < 0) and (#(self.text) + (self.i) + 1) or ((self.i) + 1)), (((self.i) < 0) and (#(self.text) + (self.i) + 1) or ((self.i) + 1))) ~= "\"")) then
            error("invalid json object key")
        end
        local key = self:_parse_string()
        self:_skip_ws()
        if ((self.i >= self.n) or (string.sub(self.text, (((self.i) < 0) and (#(self.text) + (self.i) + 1) or ((self.i) + 1)), (((self.i) < 0) and (#(self.text) + (self.i) + 1) or ((self.i) + 1))) ~= ":")) then
            error("invalid json object: missing ':'")
        end
        self.i = self.i + 1
        self:_skip_ws()
        out[key] = self:_parse_value()
        self:_skip_ws()
        if (self.i >= self.n) then
            error("invalid json object: unexpected end")
        end
        local ch = string.sub(self.text, (((self.i) < 0) and (#(self.text) + (self.i) + 1) or ((self.i) + 1)), (((self.i) < 0) and (#(self.text) + (self.i) + 1) or ((self.i) + 1)))
        self.i = self.i + 1
        if (ch == "}") then
            return out
        end
        if (ch ~= ",") then
            error("invalid json object separator")
        end
    end
end

function _JsonParser:_parse_array()
    local out = _json_new_array()
    self.i = self.i + 1
    self:_skip_ws()
    if ((self.i < self.n) and (string.sub(self.text, (((self.i) < 0) and (#(self.text) + (self.i) + 1) or ((self.i) + 1)), (((self.i) < 0) and (#(self.text) + (self.i) + 1) or ((self.i) + 1))) == "]")) then
        self.i = self.i + 1
        return out
    end
    while true do
        self:_skip_ws()
        table.insert(out, self:_parse_value())
        self:_skip_ws()
        if (self.i >= self.n) then
            error("invalid json array: unexpected end")
        end
        local ch = string.sub(self.text, (((self.i) < 0) and (#(self.text) + (self.i) + 1) or ((self.i) + 1)), (((self.i) < 0) and (#(self.text) + (self.i) + 1) or ((self.i) + 1)))
        self.i = self.i + 1
        if (ch == "]") then
            return out
        end
        if (ch ~= ",") then
            error("invalid json array separator")
        end
    end
end

function _JsonParser:_parse_string()
    if (string.sub(self.text, (((self.i) < 0) and (#(self.text) + (self.i) + 1) or ((self.i) + 1)), (((self.i) < 0) and (#(self.text) + (self.i) + 1) or ((self.i) + 1))) ~= "\"") then
        error("invalid json string")
    end
    self.i = self.i + 1
    local out_chars = {  }
    while (self.i < self.n) do
        local ch = string.sub(self.text, (((self.i) < 0) and (#(self.text) + (self.i) + 1) or ((self.i) + 1)), (((self.i) < 0) and (#(self.text) + (self.i) + 1) or ((self.i) + 1)))
        self.i = self.i + 1
        if (ch == "\"") then
            return _join_strs(out_chars, _EMPTY)
        end
        if (ch == "\\") then
            if (self.i >= self.n) then
                error("invalid json string escape")
            end
            local esc = string.sub(self.text, (((self.i) < 0) and (#(self.text) + (self.i) + 1) or ((self.i) + 1)), (((self.i) < 0) and (#(self.text) + (self.i) + 1) or ((self.i) + 1)))
            self.i = self.i + 1
            if (esc == "\"") then
                table.insert(out_chars, "\"")
            else
                if (esc == "\\") then
                    table.insert(out_chars, "\\")
                else
                    if (esc == "/") then
                        table.insert(out_chars, "/")
                    else
                        if (esc == "b") then
                            table.insert(out_chars, "")
                        else
                            if (esc == "f") then
                                table.insert(out_chars, "")
                            else
                                if (esc == "n") then
                                    table.insert(out_chars, "\n")
                                else
                                    if (esc == "r") then
                                        table.insert(out_chars, "\r")
                                    else
                                        if (esc == "t") then
                                            table.insert(out_chars, "\t")
                                        else
                                            if (esc == "u") then
                                                if ((self.i + 4) > self.n) then
                                                    error("invalid json unicode escape")
                                                end
                                                local hx = string.sub(self.text, (self.i) + 1, (self.i + 4))
                                                self.i = self.i + 4
                                                table.insert(out_chars, chr(_int_from_hex4(hx)))
                                            else
                                                error("invalid json escape")
                                            end
                                        end
                                    end
                                end
                            end
                        end
                    end
                end
            end
        else
            table.insert(out_chars, ch)
        end
    end
    error("unterminated json string")
end

function _JsonParser:_parse_number()
    local start = self.i
    if (string.sub(self.text, (((self.i) < 0) and (#(self.text) + (self.i) + 1) or ((self.i) + 1)), (((self.i) < 0) and (#(self.text) + (self.i) + 1) or ((self.i) + 1))) == "-") then
        self.i = self.i + 1
    end
    if (self.i >= self.n) then
        error("invalid json number")
    end
    if (string.sub(self.text, (((self.i) < 0) and (#(self.text) + (self.i) + 1) or ((self.i) + 1)), (((self.i) < 0) and (#(self.text) + (self.i) + 1) or ((self.i) + 1))) == "0") then
        self.i = self.i + 1
    else
        if (not _is_digit(string.sub(self.text, (((self.i) < 0) and (#(self.text) + (self.i) + 1) or ((self.i) + 1)), (((self.i) < 0) and (#(self.text) + (self.i) + 1) or ((self.i) + 1))))) then
            error("invalid json number")
        end
        while ((self.i < self.n) and _is_digit(string.sub(self.text, (((self.i) < 0) and (#(self.text) + (self.i) + 1) or ((self.i) + 1)), (((self.i) < 0) and (#(self.text) + (self.i) + 1) or ((self.i) + 1))))) do
            self.i = self.i + 1
        end
    end
    local is_float = false
    if ((self.i < self.n) and (string.sub(self.text, (((self.i) < 0) and (#(self.text) + (self.i) + 1) or ((self.i) + 1)), (((self.i) < 0) and (#(self.text) + (self.i) + 1) or ((self.i) + 1))) == ".")) then
        is_float = true
        self.i = self.i + 1
        if ((self.i >= self.n) or (not _is_digit(string.sub(self.text, (((self.i) < 0) and (#(self.text) + (self.i) + 1) or ((self.i) + 1)), (((self.i) < 0) and (#(self.text) + (self.i) + 1) or ((self.i) + 1)))))) then
            error("invalid json number")
        end
        while ((self.i < self.n) and _is_digit(string.sub(self.text, (((self.i) < 0) and (#(self.text) + (self.i) + 1) or ((self.i) + 1)), (((self.i) < 0) and (#(self.text) + (self.i) + 1) or ((self.i) + 1))))) do
            self.i = self.i + 1
        end
    end
    if (self.i < self.n) then
        local exp_ch = string.sub(self.text, (((self.i) < 0) and (#(self.text) + (self.i) + 1) or ((self.i) + 1)), (((self.i) < 0) and (#(self.text) + (self.i) + 1) or ((self.i) + 1)))
        if ((exp_ch == "e") or (exp_ch == "E")) then
            is_float = true
            self.i = self.i + 1
            if (self.i < self.n) then
                local sign = string.sub(self.text, (((self.i) < 0) and (#(self.text) + (self.i) + 1) or ((self.i) + 1)), (((self.i) < 0) and (#(self.text) + (self.i) + 1) or ((self.i) + 1)))
                if ((sign == "+") or (sign == "-")) then
                    self.i = self.i + 1
                end
            end
            if ((self.i >= self.n) or (not _is_digit(string.sub(self.text, (((self.i) < 0) and (#(self.text) + (self.i) + 1) or ((self.i) + 1)), (((self.i) < 0) and (#(self.text) + (self.i) + 1) or ((self.i) + 1)))))) then
                error("invalid json exponent")
            end
            while ((self.i < self.n) and _is_digit(string.sub(self.text, (((self.i) < 0) and (#(self.text) + (self.i) + 1) or ((self.i) + 1)), (((self.i) < 0) and (#(self.text) + (self.i) + 1) or ((self.i) + 1))))) do
                self.i = self.i + 1
            end
        end
    end
    local token = string.sub(self.text, (start) + 1, self.i)
    if is_float then
        local num_f = __pytra_float(token)
        return num_f
    end
    local num_i = __pytra_int(token)
    return num_i
end

function loads(text)
    return _JsonParser.new(text):parse()
end

function loads_obj(text)
    local value = _JsonParser.new(text):parse()
    if false then
        local raw_obj = dict(value)
        return JsonObj.new(raw_obj)
    end
    return nil
end

function loads_arr(text)
    local value = _JsonParser.new(text):parse()
    if false then
        local raw_arr = list(value)
        return JsonArr.new(raw_arr)
    end
    return nil
end

function _join_strs(parts, sep)
    if (#(parts) == 0) then
        return ""
    end
    local out = parts[1]
    local i = 1
    while (i < #(parts)) do
        out = ((out .. sep) .. parts[(((i) < 0) and (#(parts) + (i) + 1) or ((i) + 1))])
        i = i + 1
    end
    return out
end

function _escape_str(s, ensure_ascii)
    local out = { "\"" }
    for _, ch in ipairs(s) do
        local code = ord(ch)
        if (ch == "\"") then
            table.insert(out, "\\\"")
        else
            if (ch == "\\") then
                table.insert(out, "\\\\")
            else
                if (ch == "") then
                    table.insert(out, "\\b")
                else
                    if (ch == "") then
                        table.insert(out, "\\f")
                    else
                        if (ch == "\n") then
                            table.insert(out, "\\n")
                        else
                            if (ch == "\r") then
                                table.insert(out, "\\r")
                            else
                                if (ch == "\t") then
                                    table.insert(out, "\\t")
                                else
                                    if (ensure_ascii and (code > 127)) then
                                        table.insert(out, ("\\u" .. _hex4(code)))
                                    else
                                        table.insert(out, ch)
                                    end
                                end
                            end
                        end
                    end
                end
            end
        end
    end
    table.insert(out, "\"")
    return _join_strs(out, _EMPTY)
end

function _dump_json_list(values, ensure_ascii, indent, item_sep, key_sep, level)
    if (#(values) == 0) then
        return "[]"
    end
    if (indent == nil) then
        local dumped = {  }
        for _, x in ipairs(values) do
            local dumped_txt = _dump_json_value(x, ensure_ascii, indent, item_sep, key_sep, level)
            table.insert(dumped, dumped_txt)
        end
        return (("[" .. _join_strs(dumped, item_sep)) .. "]")
    end
    local indent_i = _json_indent_value(indent)
    local inner = {  }
    for _, x in ipairs(values) do
        local prefix = __pytra_repeat_seq(" ", (indent_i * (level + 1)))
        local value_txt = _dump_json_value(x, ensure_ascii, indent, item_sep, key_sep, (level + 1))
        table.insert(inner, (prefix .. value_txt))
    end
    return (((("[\n" .. _join_strs(inner, _COMMA_NL)) .. "\n") .. __pytra_repeat_seq(" ", (indent_i * level))) .. "]")
end

function _dump_json_dict(values, ensure_ascii, indent, item_sep, key_sep, level)
    if (#(values) == 0) then
        return "{}"
    end
    if (indent == nil) then
        local parts = {  }
        for _, __it_15 in ipairs(values:items()) do
            local k = __it_15[1]
            local x = __it_15[2]
            local k_txt = _escape_str(tostring(k), ensure_ascii)
            local v_txt = _dump_json_value(x, ensure_ascii, indent, item_sep, key_sep, level)
            table.insert(parts, ((k_txt .. key_sep) .. v_txt))
        end
        return (("{" .. _join_strs(parts, item_sep)) .. "}")
    end
    local indent_i = _json_indent_value(indent)
    local inner = {  }
    for _, __it_17 in ipairs(values:items()) do
        local k = __it_17[1]
        local x = __it_17[2]
        local prefix = __pytra_repeat_seq(" ", (indent_i * (level + 1)))
        local k_txt = _escape_str(tostring(k), ensure_ascii)
        local v_txt = _dump_json_value(x, ensure_ascii, indent, item_sep, key_sep, (level + 1))
        table.insert(inner, (((prefix .. k_txt) .. key_sep) .. v_txt))
    end
    return (((("{\n" .. _join_strs(inner, _COMMA_NL)) .. "\n") .. __pytra_repeat_seq(" ", (indent_i * level))) .. "}")
end

function _dump_json_value(v, ensure_ascii, indent, item_sep, key_sep, level)
    if (v == nil) then
        return "null"
    end
    if false then
        local raw_b = __pytra_truthy(v)
        return (function() if __pytra_truthy(raw_b) then return ("true") else return ("false") end end)()
    end
    if false then
        return tostring(v)
    end
    if false then
        return tostring(v)
    end
    if false then
        return _escape_str(v, ensure_ascii)
    end
    if false then
        local as_list = list(v)
        return _dump_json_list(as_list, ensure_ascii, indent, item_sep, key_sep, level)
    end
    if false then
        local as_dict = dict(v)
        return _dump_json_dict(as_dict, ensure_ascii, indent, item_sep, key_sep, level)
    end
    error("json.dumps unsupported type")
end

function dumps(obj, ensure_ascii, indent, separators)
    local item_sep = ","
    local key_sep = (function() if __pytra_truthy((indent == nil)) then return (":") else return (": ") end end)()
    if (separators == nil) then
        local __pytra_tuple_18 = separators
        item_sep = __pytra_tuple_18[1]
        key_sep = __pytra_tuple_18[2]
    end
    return _dump_json_value(obj, ensure_ascii, indent, item_sep, key_sep, 0)
end
