-- Auto-generated canonical Lua runtime for Pytra native backend.
-- Source of truth: src/runtime/lua/pytra/py_runtime.lua

local __pytra_runtime_source = debug.getinfo(1, "S").source
local __pytra_runtime_dir = ""
if type(__pytra_runtime_source) == "string" and string.sub(__pytra_runtime_source, 1, 1) == "@" then
    __pytra_runtime_dir = string.match(string.sub(__pytra_runtime_source, 2), "^(.*[/\\])") or ""
end
dofile(__pytra_runtime_dir .. "image_runtime.lua")

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
    return math.floor(tonumber(v) or 0)
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
        if container[value] ~= nil then return true end
        for i = 1, #container do
            if container[i] == value then return true end
        end
        return false
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
