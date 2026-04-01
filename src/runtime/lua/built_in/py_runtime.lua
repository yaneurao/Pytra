-- Auto-generated canonical Lua runtime for Pytra native backend.
-- Source of truth: src/runtime/lua/native/built_in/py_runtime.lua

local __pytra_runtime_source = debug.getinfo(1, "S").source
local __pytra_runtime_dir = ""
if type(__pytra_runtime_source) == "string" and string.sub(__pytra_runtime_source, 1, 1) == "@" then
    __pytra_runtime_dir = string.match(string.sub(__pytra_runtime_source, 2), "^(.*[/\\])") or ""
end
-- image_runtime is now provided via linker (png/gif modules)

function __pytra_print(...)
    local argc = select("#", ...)
    if argc == 0 then
        io.write("\n")
        return
    end
    local parts = {}
    for i = 1, argc do
        local v = select(i, ...)
        if v == true then
            parts[i] = "True"
        elseif v == false then
            parts[i] = "False"
        elseif v == nil then
            parts[i] = "None"
        else
            parts[i] = tostring(v)
        end
    end
    io.write(table.concat(parts, " ") .. "\n")
end

function __pytra_repeat_seq(a, b)
    local seq = a
    local count = b
    if type(a) == "number" and type(b) ~= "number" then
        seq = b
        count = a
    end
    local n = math.floor(tonumber(count) or 0)
    if n <= 0 then
        if type(seq) == "string" then return "" end
        return {}
    end
    if type(seq) == "string" then
        return string.rep(seq, n)
    end
    if type(seq) ~= "table" then
        return (tonumber(a) or 0) * (tonumber(b) or 0)
    end
    local out = {}
    for _ = 1, n do
        for i = 1, #seq do
            out[#out + 1] = seq[i]
        end
    end
    return out
end

function __pytra_truthy(v)
    if v == nil then return false end
    local t = type(v)
    if t == "boolean" then return v end
    if t == "number" then return v ~= 0 end
    if t == "string" then return #v ~= 0 end
    if t == "table" then return next(v) ~= nil end
    return true
end

function __pytra_int(v)
    if v == nil then return 0 end
    local n = tonumber(v) or 0
    if n >= 0 then
        return math.floor(n)
    end
    return math.ceil(n)
end

function __pytra_float(v)
    if v == nil then return 0.0 end
    return (tonumber(v) or 0.0)
end

function __pytra_bytearray(v)
    if v == nil then
        return {}
    end
    if type(v) == "number" then
        local n = math.max(0, __pytra_int(v))
        local out = {}
        for i = 1, n do
            out[#out + 1] = 0
        end
        return out
    end
    if type(v) == "table" then
        local out = {}
        for i = 1, #v do
            out[#out + 1] = v[i]
        end
        return out
    end
    return {}
end

function __pytra_bytes(v)
    if v == nil then
        return {}
    end
    if type(v) == "number" then
        local n = math.max(0, __pytra_int(v))
        local out = {}
        for i = 1, n do
            out[#out + 1] = 0
        end
        return out
    end
    if type(v) == "table" then
        local out = {}
        for i = 1, #v do
            out[#out + 1] = v[i]
        end
        return out
    end
    if type(v) == "string" then
        local out = {}
        for i = 1, #v do
            out[#out + 1] = string.byte(v, i)
        end
        return out
    end
    return {}
end

function __pytra_slice(seq, start_idx, stop_idx)
    if type(seq) == "string" then
        local n = #seq
        local i = tonumber(start_idx) or 0
        local j = stop_idx
        if j == nil then
            j = n
        else
            j = tonumber(j) or n
        end
        if i < 0 then i = i + n end
        if j < 0 then j = j + n end
        if i < 0 then i = 0 end
        if j < 0 then j = 0 end
        if i > n then i = n end
        if j > n then j = n end
        return string.sub(seq, math.floor(i) + 1, math.floor(j))
    end
    if type(seq) ~= "table" then
        return {}
    end
    local n = #seq
    local i = tonumber(start_idx) or 0
    local j = stop_idx
    if j == nil then
        j = n
    else
        j = tonumber(j) or n
    end
    if i < 0 then i = i + n end
    if j < 0 then j = j + n end
    if i < 0 then i = 0 end
    if j < 0 then j = 0 end
    if i > n then i = n end
    if j > n then j = n end
    local out = {}
    local from = math.floor(i) + 1
    local to = math.floor(j)
    for k = from, to do
        out[#out + 1] = seq[k]
    end
    return out
end

function __pytra_contains(container, value)
    local t = type(container)
    if t == "table" then
        -- For sequence tables (array), only linear-scan;
        -- for dict tables, check key existence.
        local n = #container
        if n > 0 then
            -- Sequence: linear scan only (avoid index/key collision)
            for i = 1, n do
                if container[i] == value then return true end
            end
            return false
        end
        -- Dict: key lookup
        return container[value] ~= nil
    end
    if t == "string" then
        if type(value) ~= "string" then value = tostring(value) end
        return string.find(container, value, 1, true) ~= nil
    end
    return false
end

function __pytra_str_isdigit(s)
    if type(s) ~= "string" or #s == 0 then return false end
    for i = 1, #s do
        local b = string.byte(s, i)
        if b < 48 or b > 57 then return false end
    end
    return true
end

function __pytra_str_isalpha(s)
    if type(s) ~= "string" or #s == 0 then return false end
    for i = 1, #s do
        local b = string.byte(s, i)
        local is_upper = (b >= 65 and b <= 90)
        local is_lower = (b >= 97 and b <= 122)
        if not (is_upper or is_lower) then return false end
    end
    return true
end

function __pytra_str_isalnum(s)
    if type(s) ~= "string" or #s == 0 then return false end
    for i = 1, #s do
        local b = string.byte(s, i)
        local is_digit = (b >= 48 and b <= 57)
        local is_upper = (b >= 65 and b <= 90)
        local is_lower = (b >= 97 and b <= 122)
        if not (is_digit or is_upper or is_lower) then return false end
    end
    return true
end

function __pytra_perf_counter()
    return os.clock()
end

function __pytra_math_module()
    local m = {}
    for k, v in pairs(math) do
        m[k] = v
    end
    if m.fabs == nil then m.fabs = math.abs end
    if m.log10 == nil then m.log10 = function(x) return math.log(x, 10) end end
    if m.pow == nil then m.pow = function(a, b) return (a ^ b) end end
    return m
end

function __pytra_path_basename(path)
    local name = string.match(path, "([^/]+)$")
    if name == nil or name == "" then return path end
    return name
end

function __pytra_path_parent_text(path)
    local parent = string.match(path, "^(.*)/[^/]*$")
    if parent == nil or parent == "" then return "." end
    return parent
end

function __pytra_path_stem(path)
    local name = __pytra_path_basename(path)
    local stem = string.match(name, "^(.*)%.")
    if stem == nil or stem == "" then return name end
    return stem
end

local __pytra_path_mt = {}
__pytra_path_mt.__index = __pytra_path_mt

function __pytra_path_join(left, right)
    if left == "" or left == "." then return right end
    if string.sub(left, -1) == "/" then return left .. right end
    return left .. "/" .. right
end

function __pytra_path_new(path)
    local text = tostring(path)
    local obj = { path = text }
    setmetatable(obj, __pytra_path_mt)
    obj.name = __pytra_path_basename(text)
    obj.stem = __pytra_path_stem(text)
    local parent_text = __pytra_path_parent_text(text)
    if parent_text ~= text then
        obj.parent = setmetatable({ path = parent_text }, __pytra_path_mt)
        obj.parent.name = __pytra_path_basename(parent_text)
        obj.parent.stem = __pytra_path_stem(parent_text)
        obj.parent.parent = nil
    else
        obj.parent = nil
    end
    return obj
end

function __pytra_path_mt.__div(lhs, rhs)
    local left = lhs.path
    local right = tostring(rhs)
    if type(rhs) == "table" and rhs.path ~= nil then
        right = rhs.path
    end
    return __pytra_path_new(__pytra_path_join(left, right))
end

function __pytra_path_mt:exists()
    local f = io.open(self.path, "rb")
    if f ~= nil then
        f:close()
        return true
    end
    local ok = os.execute('test -e "' .. self.path .. '"')
    if type(ok) == "boolean" then return ok end
    if type(ok) == "number" then return ok == 0 end
    return false
end

function __pytra_path_mt:joinpath(part)
    return __pytra_path_new(__pytra_path_join(self.path, tostring(part)))
end

function __pytra_path_mt:mkdir()
    os.execute('mkdir -p "' .. self.path .. '"')
end

function __pytra_path_mt:write_text(text)
    local f = assert(io.open(self.path, "wb"))
    f:write(tostring(text))
    f:close()
end

function __pytra_path_mt:read_text()
    local f = assert(io.open(self.path, "rb"))
    local data = f:read("*a")
    f:close()
    return data
end

function Path(v)
    return __pytra_path_new(v)
end

function pyMathSqrt(v)
    return math.sqrt(__pytra_float(v))
end

function pyMathSin(v)
    return math.sin(__pytra_float(v))
end

function pyMathCos(v)
    return math.cos(__pytra_float(v))
end

function pyMathTan(v)
    return math.tan(__pytra_float(v))
end

function pyMathExp(v)
    return math.exp(__pytra_float(v))
end

function pyMathLog(v)
    return math.log(__pytra_float(v))
end

function pyMathFabs(v)
    return math.abs(__pytra_float(v))
end

function pyMathFloor(v)
    return math.floor(__pytra_float(v))
end

function pyMathCeil(v)
    return math.ceil(__pytra_float(v))
end

function pyMathPow(a, b)
    return __pytra_float(a) ^ __pytra_float(b)
end

function pyMathPi()
    return math.pi
end

function pyMathE()
    return math.exp(1.0)
end

local __pytra_json_null = { __pytra_json_null = true }

local function __pytra_json_is_null(v)
    return type(v) == "table" and v.__pytra_json_null == true
end

local function __pytra_json_skip_ws(text, i)
    local n = #text
    while i <= n do
        local ch = string.sub(text, i, i)
        if ch ~= " " and ch ~= "\t" and ch ~= "\r" and ch ~= "\n" then
            break
        end
        i = i + 1
    end
    return i
end

local function __pytra_json_utf8(cp)
    if cp <= 0x7F then
        return string.char(cp)
    end
    if cp <= 0x7FF then
        local b1 = 0xC0 + math.floor(cp / 0x40)
        local b2 = 0x80 + (cp % 0x40)
        return string.char(b1, b2)
    end
    local b1 = 0xE0 + math.floor(cp / 0x1000)
    local b2 = 0x80 + (math.floor(cp / 0x40) % 0x40)
    local b3 = 0x80 + (cp % 0x40)
    return string.char(b1, b2, b3)
end

local function __pytra_json_parse_string(text, i)
    local n = #text
    i = i + 1
    local out = {}
    while i <= n do
        local ch = string.sub(text, i, i)
        if ch == "\"" then
            return table.concat(out), i + 1
        end
        if ch == "\\" then
            i = i + 1
            if i > n then
                error("invalid json string escape")
            end
            local esc = string.sub(text, i, i)
            if esc == "\"" then
                out[#out + 1] = "\""
            elseif esc == "\\" then
                out[#out + 1] = "\\"
            elseif esc == "/" then
                out[#out + 1] = "/"
            elseif esc == "b" then
                out[#out + 1] = "\b"
            elseif esc == "f" then
                out[#out + 1] = "\f"
            elseif esc == "n" then
                out[#out + 1] = "\n"
            elseif esc == "r" then
                out[#out + 1] = "\r"
            elseif esc == "t" then
                out[#out + 1] = "\t"
            elseif esc == "u" then
                if i + 4 > n then
                    error("invalid json unicode escape")
                end
                local hx = string.sub(text, i + 1, i + 4)
                local cp = tonumber(hx, 16)
                if cp == nil then
                    error("invalid json unicode escape")
                end
                out[#out + 1] = __pytra_json_utf8(cp)
                i = i + 4
            else
                error("invalid json escape")
            end
        else
            out[#out + 1] = ch
        end
        i = i + 1
    end
    error("unterminated json string")
end

local __pytra_json_parse_value

local function __pytra_json_parse_array(text, i)
    local out = {}
    i = __pytra_json_skip_ws(text, i + 1)
    if string.sub(text, i, i) == "]" then
        return out, i + 1
    end
    while true do
        local v
        v, i = __pytra_json_parse_value(text, i)
        out[#out + 1] = v
        i = __pytra_json_skip_ws(text, i)
        local ch = string.sub(text, i, i)
        if ch == "]" then
            return out, i + 1
        end
        if ch ~= "," then
            error("invalid json array separator")
        end
        i = __pytra_json_skip_ws(text, i + 1)
    end
end

local function __pytra_json_parse_object(text, i)
    local out = {}
    i = __pytra_json_skip_ws(text, i + 1)
    if string.sub(text, i, i) == "}" then
        return out, i + 1
    end
    while true do
        if string.sub(text, i, i) ~= "\"" then
            error("invalid json object key")
        end
        local k
        k, i = __pytra_json_parse_string(text, i)
        i = __pytra_json_skip_ws(text, i)
        if string.sub(text, i, i) ~= ":" then
            error("invalid json object: missing ':'")
        end
        i = __pytra_json_skip_ws(text, i + 1)
        local v
        v, i = __pytra_json_parse_value(text, i)
        out[k] = v
        i = __pytra_json_skip_ws(text, i)
        local ch = string.sub(text, i, i)
        if ch == "}" then
            return out, i + 1
        end
        if ch ~= "," then
            error("invalid json object separator")
        end
        i = __pytra_json_skip_ws(text, i + 1)
    end
end

__pytra_json_parse_value = function(text, i)
    i = __pytra_json_skip_ws(text, i)
    local ch = string.sub(text, i, i)
    if ch == "{" then
        return __pytra_json_parse_object(text, i)
    end
    if ch == "[" then
        return __pytra_json_parse_array(text, i)
    end
    if ch == "\"" then
        return __pytra_json_parse_string(text, i)
    end
    if string.sub(text, i, i + 3) == "true" then
        return true, i + 4
    end
    if string.sub(text, i, i + 4) == "false" then
        return false, i + 5
    end
    if string.sub(text, i, i + 3) == "null" then
        return __pytra_json_null, i + 4
    end
    local token = string.match(string.sub(text, i), "^%-?%d+%.?%d*[eE]?[%+%-]?%d*")
    if token == nil or token == "" then
        error("invalid json number")
    end
    local num = tonumber(token)
    if num == nil then
        error("invalid json number")
    end
    return num, i + #token
end

local function __pytra_json_escape_string(s)
    local out = { "\"" }
    for i = 1, #s do
        local ch = string.sub(s, i, i)
        if ch == "\"" then
            out[#out + 1] = "\\\""
        elseif ch == "\\" then
            out[#out + 1] = "\\\\"
        elseif ch == "\b" then
            out[#out + 1] = "\\b"
        elseif ch == "\f" then
            out[#out + 1] = "\\f"
        elseif ch == "\n" then
            out[#out + 1] = "\\n"
        elseif ch == "\r" then
            out[#out + 1] = "\\r"
        elseif ch == "\t" then
            out[#out + 1] = "\\t"
        else
            out[#out + 1] = ch
        end
    end
    out[#out + 1] = "\""
    return table.concat(out)
end

local function __pytra_json_is_array(tbl)
    local n = 0
    for k, _ in pairs(tbl) do
        if type(k) ~= "number" or k < 1 or math.floor(k) ~= k then
            return false, 0
        end
        if k > n then n = k end
    end
    for i = 1, n do
        if rawget(tbl, i) == nil then
            return false, 0
        end
    end
    return true, n
end

local function __pytra_json_encode(v)
    if v == nil or __pytra_json_is_null(v) then
        return "null"
    end
    local tv = type(v)
    if tv == "boolean" then
        return v and "true" or "false"
    end
    if tv == "number" then
        return tostring(v)
    end
    if tv == "string" then
        return __pytra_json_escape_string(v)
    end
    if tv == "table" then
        local is_arr, n = __pytra_json_is_array(v)
        local parts = {}
        if is_arr then
            for i = 1, n do
                parts[#parts + 1] = __pytra_json_encode(v[i])
            end
            return "[" .. table.concat(parts, ",") .. "]"
        end
        for k, item in pairs(v) do
            parts[#parts + 1] = __pytra_json_escape_string(tostring(k)) .. ":" .. __pytra_json_encode(item)
        end
        return "{" .. table.concat(parts, ",") .. "}"
    end
    return __pytra_json_escape_string(tostring(v))
end

function pyJsonLoads(v)
    local text = tostring(v)
    local out, i = __pytra_json_parse_value(text, 1)
    i = __pytra_json_skip_ws(text, i)
    if i <= #text then
        error("invalid json: trailing characters")
    end
    return out
end

function pyJsonDumps(v)
    return __pytra_json_encode(v)
end

dumps = pyJsonDumps
loads = pyJsonLoads
loads_arr = pyJsonLoads

function __pytra_isinstance(obj, class_tbl)
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

function Path(path)
    return __pytra_path_new(path)
end

function __pytra_set_argv(items)
    __pytra_sys_argv = items or {}
end

function __pytra_set_path(items)
    __pytra_sys_path = items or {}
end

function sub(pattern, repl, text, count)
    local lua_pat = tostring(pattern):gsub("\\s", "%%s")
    local limit = tonumber(count)
    local out = string.gsub(tostring(text), lua_pat, tostring(repl), limit)
    return out
end

deque = {}
deque.__index = deque
deque.__len = function(self)
    return #self._items
end
function deque.new()
    return setmetatable({ _items = {} }, deque)
end
setmetatable(deque, {
    __call = function(_, ...)
        return deque.new(...)
    end,
})
function deque:append(value)
    table.insert(self._items, value)
end
function deque:appendleft(value)
    table.insert(self._items, 1, value)
end
function deque:popleft()
    return table.remove(self._items, 1)
end
function deque:pop()
    return table.remove(self._items)
end
function deque:clear()
    self._items = {}
end

ArgumentParser = {}
ArgumentParser.__index = ArgumentParser
setmetatable(ArgumentParser, {
    __call = function(_, prog)
        return setmetatable({ prog = prog or "", specs = {} }, ArgumentParser)
    end,
})
function ArgumentParser:add_argument(...)
    local spec = { flags = { ... }, action = "", choices = nil, default = nil }
    local args = { ... }
    local last = args[#args]
    if type(last) == "table" and last.flags == nil then
        spec = last
    end
    spec.flags = {}
    for i = 1, select("#", ...) do
        local item = select(i, ...)
        if type(item) == "string" then
            spec.flags[#spec.flags + 1] = item
        elseif type(item) == "table" then
            if type(item.action) == "string" then spec.action = item.action end
            if type(item.choices) == "table" then spec.choices = item.choices end
            spec.default = item.default
        end
    end
    self.specs[#self.specs + 1] = spec
end
function ArgumentParser:parse_args(argv)
    local out = {}
    local positionals = {}
    for _, spec in ipairs(self.specs) do
        local first = spec.flags[1]
        if type(first) == "string" and string.sub(first, 1, 1) ~= "-" then
            positionals[#positionals + 1] = spec
        elseif spec.default ~= nil then
            local key = string.gsub(spec.flags[#spec.flags], "^%-%-?", "")
            out[key] = spec.default
        elseif spec.action == "store_true" then
            local key = string.gsub(spec.flags[#spec.flags], "^%-%-?", "")
            out[key] = false
        end
    end
    local pos_idx = 1
    local i = 1
    while i <= #argv do
        local token = argv[i]
        if type(token) == "string" and string.sub(token, 1, 1) == "-" then
            local matched = nil
            for _, spec in ipairs(self.specs) do
                for _, flag in ipairs(spec.flags) do
                    if flag == token then
                        matched = spec
                        break
                    end
                end
                if matched ~= nil then break end
            end
            if matched ~= nil then
                local key = string.gsub(matched.flags[#matched.flags], "^%-%-?", "")
                if matched.action == "store_true" then
                    out[key] = true
                    i = i + 1
                else
                    local value = argv[i + 1]
                    out[key] = value
                    i = i + 2
                end
            else
                i = i + 1
            end
        else
            local spec = positionals[pos_idx]
            if spec ~= nil then
                local key = spec.flags[1]
                out[key] = token
                pos_idx = pos_idx + 1
            end
            i = i + 1
        end
    end
    return out
end

-- Python stdlib shim tables so that EAST-generated code like
-- `time.perf_counter()` or `math.sqrt(x)` resolves at runtime.
time = {
    perf_counter = function() return os.clock() end,
}
math = math or {}
math.pi = math.pi
math.e = 2.718281828459045

-- Python built-in `open(path, mode)` shim.
function open(path, mode)
    local f = io.open(path, mode)
    if not f then
        error("cannot open file: " .. tostring(path))
    end
    -- Return a wrapper with write(bytes_table) that converts int table to binary.
    local wrapper = {}
    function wrapper:write(data)
        if type(data) == "table" then
            local parts = {}
            for i = 1, #data do
                parts[i] = string.char(data[i] % 256)
            end
            f:write(table.concat(parts))
        else
            f:write(tostring(data))
        end
    end
    function wrapper:close()
        f:close()
    end
    return wrapper
end

-- Python built-in `ord(ch)` / `chr(n)` shims.
function ord(ch)
    return string.byte(ch, 1) or 0
end
function chr(n)
    return string.char(n % 256)
end

function __pytra_noop() end

function reversed(t)
    local out = {}
    for i = #t, 1, -1 do
        out[#out + 1] = t[i]
    end
    return out
end

function __pytra_len(v)
    if type(v) == "string" then return #v end
    if type(v) == "table" then
        local n = #v
        if n > 0 then return n end
        local count = 0
        for _ in pairs(v) do count = count + 1 end
        return count
    end
    return 0
end

function __pytra_floordiv(a, b)
    return math.floor(a / b)
end

function __pytra_range(start, stop, step)
    if step == nil then step = 1 end
    local out = {}
    if step > 0 then
        local i = start
        while i < stop do
            out[#out + 1] = i
            i = i + step
        end
    elseif step < 0 then
        local i = start
        while i > stop do
            out[#out + 1] = i
            i = i + step
        end
    end
    return out
end

function __pytra_enumerate(seq)
    local out = {}
    for i = 1, #seq do
        out[#out + 1] = {i - 1, seq[i]}
    end
    return out
end

function __pytra_reversed(seq)
    local out = {}
    for i = #seq, 1, -1 do
        out[#out + 1] = seq[i]
    end
    return out
end

function __pytra_sorted(seq)
    local out = {}
    for i = 1, #seq do out[i] = seq[i] end
    table.sort(out)
    return out
end

function __pytra_ord(ch)
    return string.byte(ch, 1) or 0
end

function __pytra_chr(n)
    return string.char(n % 256)
end

function __pytra_round(v, ndigits)
    if ndigits == nil then ndigits = 0 end
    local m = 10 ^ ndigits
    return math.floor(v * m + 0.5) / m
end

function __pytra_math_log2(x) return math.log(x) / math.log(2) end
function __pytra_math_log10(x) return math.log(x, 10) end
function __pytra_math_pow(a, b) return a ^ b end
function __pytra_math_hypot(a, b) return math.sqrt(a*a + b*b) end
function __pytra_math_isfinite(x) return x == x and x ~= math.huge and x ~= -math.huge end
function __pytra_math_isinf(x) return x == math.huge or x == -math.huge end
function __pytra_math_isnan(x) return x ~= x end

-- Dict helpers
function __pytra_dict_get(d, key, default)
    local v = d[key]
    if v == nil then return default end
    return v
end

function __pytra_dict_items(d)
    local out = {}
    for k, v in pairs(d) do
        out[#out + 1] = {k, v}
    end
    return out
end

function __pytra_dict_keys(d)
    local out = {}
    for k, _ in pairs(d) do
        out[#out + 1] = k
    end
    return out
end

function __pytra_dict_values(d)
    local out = {}
    for _, v in pairs(d) do
        out[#out + 1] = v
    end
    return out
end

function __pytra_dict_pop(d, key)
    local v = d[key]
    d[key] = nil
    return v
end

function __pytra_dict_update(d, other)
    for k, v in pairs(other) do
        d[k] = v
    end
end

function __pytra_dict_setdefault(d, key, default)
    if d[key] == nil then d[key] = default end
    return d[key]
end

-- List helpers
function __pytra_list_clear(lst)
    for i = #lst, 1, -1 do lst[i] = nil end
end

function __pytra_list_extend(lst, other)
    for i = 1, #other do
        lst[#lst + 1] = other[i]
    end
end

function __pytra_list_index(lst, value)
    for i = 1, #lst do
        if lst[i] == value then return i - 1 end
    end
    error("ValueError: " .. tostring(value) .. " is not in list")
end

function __pytra_list_remove(lst, value)
    for i = 1, #lst do
        if lst[i] == value then
            table.remove(lst, i)
            return
        end
    end
    error("ValueError: list.remove(x): x not in list")
end

function __pytra_list_reverse(lst)
    local n = #lst
    for i = 1, math.floor(n / 2) do
        lst[i], lst[n - i + 1] = lst[n - i + 1], lst[i]
    end
end

function __pytra_list_ctor(iter)
    if type(iter) == "table" then
        local out = {}
        for i = 1, #iter do out[i] = iter[i] end
        return out
    end
    return {}
end

-- Set helpers
function __pytra_set_ctor(iter)
    local out = {}
    if type(iter) == "table" then
        if #iter > 0 then
            for i = 1, #iter do out[iter[i]] = true end
        else
            for k, _ in pairs(iter) do out[k] = true end
        end
    end
    return out
end

function __pytra_set_add(s, val) s[val] = true end
function __pytra_set_discard(s, val) s[val] = nil end
function __pytra_set_remove(s, val)
    if s[val] == nil then error("KeyError: " .. tostring(val)) end
    s[val] = nil
end
function __pytra_set_clear(s)
    for k in pairs(s) do s[k] = nil end
end

-- String helpers
function __pytra_str_strip(s)
    return s:match("^%s*(.-)%s*$") or ""
end
function __pytra_str_lstrip(s)
    return s:match("^%s*(.*)$") or ""
end
function __pytra_str_rstrip(s)
    return s:match("^(.-)%s*$") or ""
end
function __pytra_str_startswith(s, prefix)
    return s:sub(1, #prefix) == prefix
end
function __pytra_str_endswith(s, suffix)
    if #suffix == 0 then return true end
    return s:sub(-#suffix) == suffix
end
function __pytra_str_replace(s, old, new)
    local result = s:gsub(old:gsub("([%(%)%.%%%+%-%*%?%[%]%^%$])", "%%%1"), new)
    return result
end
function __pytra_str_find(s, sub, start)
    if start == nil then start = 0 end
    local i = s:find(sub, start + 1, true)
    if i == nil then return -1 end
    return i - 1
end
function __pytra_str_rfind(s, sub)
    local last = -1
    local i = 1
    while true do
        local found = s:find(sub, i, true)
        if found == nil then break end
        last = found - 1
        i = found + 1
    end
    return last
end
function __pytra_str_split(s, sep)
    if sep == nil then sep = " " end
    local parts = {}
    if sep == "" then
        for i = 1, #s do parts[#parts + 1] = s:sub(i, i) end
        return parts
    end
    local pos = 1
    while true do
        local i = s:find(sep, pos, true)
        if i == nil then
            parts[#parts + 1] = s:sub(pos)
            break
        end
        parts[#parts + 1] = s:sub(pos, i - 1)
        pos = i + #sep
    end
    return parts
end
function __pytra_str_join(sep, lst)
    return table.concat(lst, sep)
end
function __pytra_str_upper(s) return s:upper() end
function __pytra_str_lower(s) return s:lower() end
function __pytra_str_count(s, sub)
    local count = 0
    local i = 1
    while true do
        local found = s:find(sub, i, true)
        if found == nil then break end
        count = count + 1
        i = found + 1
    end
    return count
end
function __pytra_str_index(s, sub)
    local i = s:find(sub, 1, true)
    if i == nil then error("ValueError: substring not found") end
    return i - 1
end
function __pytra_str_isspace(s)
    if #s == 0 then return false end
    return s:match("^%s+$") ~= nil
end

-- Ternary helper (Lua does not have ternary, and `cond and a or b` fails when a is falsy)
function __pytra_ternary(cond, a, b)
    if cond then return a else return b end
end

-- Format helper for f-strings
function __pytra_fmt(v, spec)
    if spec == "" then return tostring(v) end
    -- Simple numeric format specs
    local width, prec, ftype = spec:match("^(%d*)%.?(%d*)([fdegsx%%]?)$")
    if ftype == "f" or ftype == "e" or ftype == "g" then
        local p = tonumber(prec) or 6
        return string.format("%." .. p .. ftype, v)
    end
    if ftype == "d" then
        return string.format("%d", v)
    end
    if ftype == "s" then
        return tostring(v)
    end
    if ftype == "x" then
        return string.format("%x", v)
    end
    -- Fallback
    return tostring(v)
end

-- Assertion helpers
function __pytra_assert_stdout(expected, fn)
    -- Capture stdout
    local captured = {}
    local old_write = io.write
    io.write = function(...)
        for i = 1, select("#", ...) do
            captured[#captured + 1] = tostring(select(i, ...))
        end
    end
    fn()
    io.write = old_write
    local output = table.concat(captured)
    local lines = {}
    for line in (output .. "\n"):gmatch("([^\n]*)\n") do
        if line ~= "" then
            lines[#lines + 1] = line
        end
    end
    local ok = true
    if #lines ~= #expected then
        ok = false
    else
        for i = 1, #expected do
            if lines[i] ~= expected[i] then
                ok = false
                break
            end
        end
    end
    if ok then
        return "PASS"
    else
        return "FAIL: expected " .. table.concat(expected, ", ") .. " got " .. table.concat(lines, ", ")
    end
end

function __pytra_assert_true(cond, msg)
    if cond then return "PASS" end
    return "FAIL: " .. (msg or "assertion failed")
end

function __pytra_assert_eq(a, b, msg)
    if a == b then return "PASS" end
    return "FAIL: " .. tostring(a) .. " ~= " .. tostring(b) .. (msg and (" " .. msg) or "")
end

function __pytra_assert_all(results)
    local all_pass = true
    for i = 1, #results do
        if results[i] ~= "PASS" then
            all_pass = false
            break
        end
    end
    if all_pass then return "PASS" end
    local fails = {}
    for i = 1, #results do
        if results[i] ~= "PASS" then
            fails[#fails + 1] = results[i]
        end
    end
    return table.concat(fails, "\n")
end

-- makedirs
function __pytra_makedirs(path)
    os.execute('mkdir -p "' .. tostring(path) .. '"')
end

-- open (with context manager support)
function __pytra_open(path, mode)
    local f = io.open(path, mode)
    if not f then error("cannot open file: " .. tostring(path)) end
    local wrapper = {}
    function wrapper:write(data)
        if type(data) == "table" then
            local parts = {}
            for i = 1, #data do parts[i] = string.char(data[i] % 256) end
            f:write(table.concat(parts))
        else
            f:write(tostring(data))
        end
    end
    function wrapper:close() f:close() end
    function wrapper:read(mode_)
        if mode_ == nil then mode_ = "*a" end
        return f:read(mode_)
    end
    return wrapper
end

-- sys stubs
__pytra_sys_argv = arg or {}
__pytra_sys_path = {}
