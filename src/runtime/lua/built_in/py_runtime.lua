-- Auto-generated canonical Lua runtime for Pytra native backend.
-- Source of truth: src/runtime/lua/native/built_in/py_runtime.lua

local __pytra_runtime_source = debug.getinfo(1, "S").source
local __pytra_runtime_dir = ""
if type(__pytra_runtime_source) == "string" and string.sub(__pytra_runtime_source, 1, 1) == "@" then
    __pytra_runtime_dir = string.match(string.sub(__pytra_runtime_source, 2), "^(.*[/\\])") or ""
end
-- image_runtime is now provided via linker (png/gif modules)

local function __pytra_table_move(src, first, last, offset, dst)
    local target = dst or src
    if first > last then
        return target
    end
    if target == src and offset > first and offset <= last then
        local i = last
        local j = offset + (last - first)
        while i >= first do
            target[j] = src[i]
            i = i - 1
            j = j - 1
        end
        return target
    end
    local i = first
    local j = offset
    while i <= last do
        target[j] = src[i]
        i = i + 1
        j = j + 1
    end
    return target
end

function __pytra_print(...)
    local argc = select("#", ...)
    if argc == 0 then
        io.write("\n")
        return
    end
    local parts = {}
    for i = 1, argc do
        local v = select(i, ...)
        parts[i] = __pytra_repr(v)
    end
    io.write(table.concat(parts, " ") .. "\n")
end

function __pytra_repr(v)
    if v == true then
        return "True"
    end
    if v == false then
        return "False"
    end
    if v == nil then
        return "None"
    end
    local tv = type(v)
    if tv == "number" then
        if math.type ~= nil and math.type(v) == "float" and v == math.floor(v) then
            return string.format("%.1f", v)
        end
        local abs_v = math.abs(v)
        if abs_v ~= 0 and (abs_v < 1e-6 or abs_v >= 1e16) then
            return string.format("%.17g", v)
        end
        return tostring(v)
    end
    if tv == "string" then
        return v
    end
    if tv ~= "table" then
        return tostring(v)
    end
    if type(v.msg) == "string" then
        return v.msg
    end
    local mt = getmetatable(v)
    if type(mt) == "table" then
        local mt_str = mt.__str__
        if type(mt_str) == "function" then
            return mt_str(v)
        end
        local mt_index = mt.__index
        if type(mt_index) == "table" and type(mt_index.__str__) == "function" then
            return mt_index.__str__(v)
        end
    end
    if v.path ~= nil then
        return tostring(v.path)
    end
    if v._items ~= nil and type(v._items) == "table" then
        return __pytra_repr(v._items)
    end
    if __pytra_is_tuple(v) then
        local parts = {}
        for i = 1, #v do
            parts[#parts + 1] = __pytra_repr_value(v[i])
        end
        if #v == 1 then
            return "(" .. parts[1] .. ",)"
        end
        return "(" .. table.concat(parts, ", ") .. ")"
    end
    local n = #v
    local is_array = true
    local key_count = 0
    for k, _ in pairs(v) do
        key_count = key_count + 1
        if type(k) ~= "number" or k < 1 or math.floor(k) ~= k or k > n then
            is_array = false
        end
    end
    if is_array and key_count == n then
        local parts = {}
        for i = 1, n do
            parts[#parts + 1] = __pytra_repr_value(v[i])
        end
        return "[" .. table.concat(parts, ", ") .. "]"
    end
    local keys = {}
    for k, _ in pairs(v) do
        keys[#keys + 1] = k
    end
    table.sort(keys, function(a, b) return tostring(a) < tostring(b) end)
    local parts = {}
    for _, k in ipairs(keys) do
        parts[#parts + 1] = __pytra_repr_value(k) .. ": " .. __pytra_repr_value(v[k])
    end
    return "{" .. table.concat(parts, ", ") .. "}"
end

function py_repr(v)
    return __pytra_repr(v)
end

function __pytra_repr_value(v)
    if type(v) == "string" then
        return "'" .. v:gsub("\\", "\\\\"):gsub("'", "\\'") .. "'"
    end
    return __pytra_repr(v)
end

function __pytra_to_string(v)
    if type(v) == "table" then
        if type(v.msg) == "string" then
            return v.msg
        end
        local mt = getmetatable(v)
        if type(mt) == "table" then
            local mt_str = mt.__str__
            if type(mt_str) == "function" then
                return mt_str(v)
            end
            local mt_index = mt.__index
            if type(mt_index) == "table" and type(mt_index.__str__) == "function" then
                return mt_index.__str__(v)
            end
        end
        return __pytra_repr(v)
    end
    return tostring(v)
end

function __pytra_type_name(v)
    local tv = type(v)
    if tv ~= "table" then
        return tv
    end
    local mt = getmetatable(v)
    if type(mt) == "table" then
        if type(mt.__name) == "string" then
            return mt.__name
        end
        local mt_index = mt.__index
        if type(mt_index) == "table" and type(mt_index.__name) == "string" then
            return mt_index.__name
        end
    end
    return "table"
end

function pytra_isinstance(obj, class_tbl)
    if type(class_tbl) == "number" then
        if class_tbl == PYTRA_TID_OBJECT then
            return true
        end
        if class_tbl == PYTRA_TID_STR then
            return type(obj) == "string"
        end
        if class_tbl == PYTRA_TID_BOOL then
            return type(obj) == "boolean"
        end
        if class_tbl == PYTRA_TID_INT or class_tbl == PYTRA_TID_FLOAT then
            return type(obj) == "number"
        end
        if class_tbl == PYTRA_TID_LIST then
            if type(obj) ~= "table" then
                return false
            end
            local n = #obj
            local key_count = 0
            for k, _ in pairs(obj) do
                key_count = key_count + 1
                if type(k) ~= "number" or k < 1 or math.floor(k) ~= k or k > n then
                    return false
                end
            end
            return key_count == n
        end
        if class_tbl == PYTRA_TID_DICT or class_tbl == PYTRA_TID_SET then
            return type(obj) == "table"
        end
        return false
    end
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
    if #seq == 1 then
        local out = {}
        local item = seq[1]
        for i = 1, n do
            out[i] = item
        end
        return out
    end
    local out = {}
    for _ = 1, n do
        for i = 1, #seq do
            out[#out + 1] = seq[i]
        end
    end
    return out
end

function __pytra_tuple(items)
    local mt = { __pytra_tuple = true }
    return setmetatable(items or {}, mt)
end

function __pytra_is_tuple(v)
    if type(v) ~= "table" then
        return false
    end
    local mt = getmetatable(v)
    return type(mt) == "table" and mt.__pytra_tuple == true
end

function __pytra_equals(a, b)
    if type(a) ~= type(b) then
        return false
    end
    if type(a) ~= "table" then
        return a == b
    end
    local a_is_tuple = __pytra_is_tuple(a)
    local b_is_tuple = __pytra_is_tuple(b)
    if a_is_tuple ~= b_is_tuple then
        return false
    end
    local a_n = #a
    local b_n = #b
    local a_is_array = true
    local b_is_array = true
    local a_keys = 0
    local b_keys = 0
    for k, _ in pairs(a) do
        a_keys = a_keys + 1
        if type(k) ~= "number" or k < 1 or math.floor(k) ~= k or k > a_n then
            a_is_array = false
        end
    end
    for k, _ in pairs(b) do
        b_keys = b_keys + 1
        if type(k) ~= "number" or k < 1 or math.floor(k) ~= k or k > b_n then
            b_is_array = false
        end
    end
    if a_is_array and b_is_array and a_keys == a_n and b_keys == b_n then
        if a_n ~= b_n then
            return false
        end
        for i = 1, a_n do
            if not __pytra_equals(a[i], b[i]) then
                return false
            end
        end
        return true
    end
    if a_keys ~= b_keys then
        return false
    end
    for k, v in pairs(a) do
        if b[k] == nil and v ~= nil then
            return false
        end
        if not __pytra_equals(v, b[k]) then
            return false
        end
    end
    return true
end

function __pytra_set_key(v)
    if type(v) == "table" then
        return "__pytra__" .. __pytra_repr(v)
    end
    return v
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
    if type(v) == "number" then
        return v >= 0 and math.floor(v) or math.ceil(v)
    end
    local n = tonumber(v) or 0
    if n >= 0 then
        return math.floor(n)
    end
    return math.ceil(n)
end

function __pytra_float(v)
    if v == nil then return 0.0 end
    if type(v) == "boolean" then
        return v and 1.0 or 0.0
    end
    return (tonumber(v) or 0.0)
end

local __pytra_bytearray_mt = {}
__pytra_bytearray_mt.__index = __pytra_bytearray_mt

function __pytra_bytearray_mt:pop()
    local n = #self
    if n == 0 then
        return nil
    end
    local value = self[n]
    self[n] = nil
    return value
end

function __pytra_bytearray_mt:clear()
    for i = #self, 1, -1 do
        self[i] = nil
    end
    return nil
end

function __pytra_bytearray(v)
    if v == nil then
        return setmetatable({}, __pytra_bytearray_mt)
    end
    if type(v) == "number" then
        local n = math.max(0, __pytra_int(v))
        local out = {}
        for i = 1, n do
            out[i] = 0
        end
        return setmetatable(out, __pytra_bytearray_mt)
    end
    if type(v) == "table" then
        local out = {}
        __pytra_table_move(v, 1, #v, 1, out)
        return setmetatable(out, __pytra_bytearray_mt)
    end
    return setmetatable({}, __pytra_bytearray_mt)
end

function bytearray(v)
    return __pytra_bytearray(v)
end

function __pytra_bytearray_append(self, value)
    if type(value) == "number" then
        if value >= 0 and value < 256 and math.floor(value) == value then
            self[#self + 1] = value
            return
        end
        if value >= 0 then
            self[#self + 1] = math.floor(value)
            return
        end
        self[#self + 1] = math.ceil(value)
        return
    end
    local n = tonumber(value) or 0
    if n >= 0 then
        self[#self + 1] = math.floor(n)
        return
    end
    self[#self + 1] = math.ceil(n)
end

function __pytra_bytearray_extend(self, other)
    if type(other) ~= "table" then
        return
    end
    if #other > 0 then
        __pytra_table_move(other, 1, #other, #self + 1, self)
    end
end

function __pytra_bytearray_extend_slice(self, other, start_idx, stop_idx)
    if type(other) ~= "table" then
        return
    end
    local n = #other
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
    local from = math.floor(i) + 1
    local to = math.floor(j)
    if from <= to then
        __pytra_table_move(other, from, to, #self + 1, self)
    end
end

function __pytra_list_append(items, value)
    items[#items + 1] = value
    return nil
end

function __pytra_list_clear(items)
    for i = #items, 1, -1 do
        items[i] = nil
    end
end

function __pytra_clear(items)
    if type(items) ~= "table" then
        return
    end
    for k, _ in pairs(items) do
        items[k] = nil
    end
end

function __pytra_list_extend(items, other)
    if type(other) ~= "table" then
        return
    end
    if #other > 0 then
        __pytra_table_move(other, 1, #other, #items + 1, items)
    end
end

function __pytra_list_concat(left, right)
    local out = {}
    if type(left) == "table" then
        for i = 1, #left do
            out[#out + 1] = left[i]
        end
    end
    if type(right) == "table" then
        for i = 1, #right do
            out[#out + 1] = right[i]
        end
    end
    return out
end

function __pytra_list_index(items, value)
    if type(items) ~= "table" then
        return -1
    end
    for i = 1, #items do
        if items[i] == value then
            return i - 1
        end
    end
    return -1
end

function zip(a, b)
    local out = {}
    if type(a) ~= "table" or type(b) ~= "table" then
        return out
    end
    local n = #a
    if #b < n then n = #b end
    for i = 1, n do
        out[#out + 1] = { a[i], b[i] }
    end
    return out
end

function sum(items)
    local total = 0
    if type(items) ~= "table" then
        return total
    end
    for i = 1, #items do
        total = total + (tonumber(items[i]) or 0)
    end
    return total
end

function __pytra_bytes(v)
    if v == nil then
        return {}
    end
    if type(v) == "number" then
        local n = math.max(0, __pytra_int(v))
        local out = {}
        for i = 1, n do
            out[i] = 0
        end
        return out
    end
    if type(v) == "table" then
        local out = {}
        __pytra_table_move(v, 1, #v, 1, out)
        return out
    end
    if type(v) == "string" then
        local out = {}
        for i = 1, #v do
            out[i] = string.byte(v, i)
        end
        return out
    end
    return {}
end

function bytes(v)
    return __pytra_bytes(v)
end

function __pytra_bytes_alias(v)
    if type(v) == "table" then
        return v
    end
    return __pytra_bytes(v)
end

function __pytra_write_byte_table(f, data)
    local n = #data
    local i = 1
    local chunk_size = 2048
    while i <= n do
        local stop = i + chunk_size - 1
        if stop > n then
            stop = n
        end
        local fast = true
        local j = i
        while j <= stop do
            if type(data[j]) ~= "number" then
                fast = false
                break
            end
            j = j + 1
        end
        if fast then
            f:write(string.char(table.unpack(data, i, stop)))
        else
            local parts = {}
            local out_i = 1
            j = i
            while j <= stop do
                parts[out_i] = string.char((tonumber(data[j]) or 0) % 256)
                out_i = out_i + 1
                j = j + 1
            end
            f:write(table.concat(parts))
        end
        i = stop + 1
    end
end

function __pytra_seq_get_checked(seq, idx)
    local n = #seq
    if type(idx) == "number" and idx >= 0 and idx < n and math.floor(idx) == idx then
        return seq[idx + 1], nil
    end
    local i = tonumber(idx) or 0
    if i < 0 then
        i = i + n
    end
    if i < 0 or i >= n then
        return nil, IndexError.new("index out of range")
    end
    return seq[i + 1], nil
end

function __pytra_str_get_checked(s, idx)
    local n = #s
    if type(idx) == "number" and idx >= 0 and idx < n and math.floor(idx) == idx then
        local j_fast = idx + 1
        return string.sub(s, j_fast, j_fast), nil
    end
    local i = tonumber(idx) or 0
    if i < 0 then
        i = i + n
    end
    if i < 0 or i >= n then
        return nil, IndexError.new("string index out of range")
    end
    local j = i + 1
    return string.sub(s, j, j), nil
end

function __pytra_str_byte_get_checked(s, idx)
    local n = #s
    if type(idx) == "number" and idx >= 0 and idx < n and math.floor(idx) == idx then
        return string.byte(s, idx + 1), nil
    end
    local i = tonumber(idx) or 0
    if i < 0 then
        i = i + n
    end
    if i < 0 or i >= n then
        return nil, IndexError.new("string index out of range")
    end
    return string.byte(s, i + 1), nil
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
    local from = math.floor(i) + 1
    local to = math.floor(j)
    local out = {}
    if from <= to then
        __pytra_table_move(seq, from, to, 1, out)
    end
    return out
end

function __pytra_contains(container, value)
    local t = type(container)
    if t == "table" then
        local n = #container
        local is_array = true
        local key_count = 0
        for k, _ in pairs(container) do
            key_count = key_count + 1
            if type(k) ~= "number" or k < 1 or math.floor(k) ~= k or k > n then
                is_array = false
            end
        end
        if is_array and key_count == n then
            for i = 1, n do
                if __pytra_equals(container[i], value) then return true end
            end
            return false
        end
        local slot = __pytra_set_key(value)
        if container[slot] ~= nil then
            return true
        end
        return container[value] ~= nil
    end
    if t == "string" then
        if type(value) ~= "string" then value = tostring(value) end
        return string.find(container, value, 1, true) ~= nil
    end
    return false
end

function __pytra_truthy(value)
    if value == nil or value == false then
        return false
    end
    if type(value) == "string" then
        return #value ~= 0
    end
    if type(value) == "number" then
        return value ~= 0
    end
    if type(value) == "table" then
        if #value > 0 then
            return true
        end
        return next(value) ~= nil
    end
    return true
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

__pytra_pi = math.pi
__pytra_e = math.exp(1)

function __pytra_path_basename(path)
    if type(path) == "table" and path.path ~= nil then
        path = path.path
    end
    path = tostring(path or "")
    local name = string.match(path, "([^/]+)$")
    if name == nil or name == "" then return path end
    return name
end

function __pytra_path_parent_text(path)
    if type(path) == "table" and path.path ~= nil then
        path = path.path
    end
    path = tostring(path or "")
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
__pytra_path_mt.__tostring = function(self)
    return self.path
end

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

function __pytra_path_mt:joinpath(...)
    local out = self.path
    local parts = { ... }
    for i = 1, #parts do
        out = __pytra_path_join(out, tostring(parts[i]))
    end
    return __pytra_path_new(out)
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

function __pytra_path_splitext(path)
    local text = tostring(path)
    local idx = string.match(text, ".*()%.")
    if idx == nil then
        return text, ""
    end
    return string.sub(text, 1, idx - 1), string.sub(text, idx)
end

__pytra_path = {
    join = function(...)
        local args = { ... }
        local out = ""
        local start = 1
        if type(args[1]) == "table" then
            start = 2
        end
        for i = start, #args do
            out = __pytra_path_join(out, tostring(args[i]))
        end
        return out
    end,
    basename = function(path, maybe_path)
        if maybe_path ~= nil then
            path = maybe_path
        end
        return __pytra_path_basename(path)
    end,
    splitext = function(path, maybe_path)
        if maybe_path ~= nil then
            path = maybe_path
        end
        local root, ext = __pytra_path_splitext(path)
        return { root, ext }
    end,
    dirname = function(path, maybe_path)
        if maybe_path ~= nil then
            path = maybe_path
        end
        return __pytra_path_parent_text(path)
    end,
    exists = function(path, maybe_path)
        if maybe_path ~= nil then
            path = maybe_path
        end
        return __pytra_path_new(path):exists()
    end,
    abspath = function(path, maybe_path)
        if maybe_path ~= nil then
            path = maybe_path
        end
        local raw = tostring(path)
        if string.sub(raw, 1, 1) == "/" then
            return raw
        end
        local cwd = io.popen("pwd", "r")
        if cwd == nil then
            return raw
        end
        local base = cwd:read("*l") or ""
        cwd:close()
        if base == "" then
            return raw
        end
        if string.sub(base, -1) == "/" then
            return base .. raw
        end
        return base .. "/" .. raw
    end,
}

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

local function __pytra_json_encode_pretty(v, indent, level)
    if indent == nil then
        return __pytra_json_encode(v)
    end
    local pad = string.rep(" ", indent * level)
    local child_pad = string.rep(" ", indent * (level + 1))
    local ty = type(v)
    if v == nil or __pytra_json_is_null(v) then
        return "null"
    end
    if ty == "boolean" or ty == "number" then
        return __pytra_json_encode(v)
    end
    if ty == "string" then
        return __pytra_json_escape_string(v)
    end
    if ty ~= "table" then
        return __pytra_json_escape_string(tostring(v))
    end
    local is_arr, n = __pytra_json_is_array(v)
    if is_arr then
        if n == 0 then
            return "[]"
        end
        local parts = {}
        for i = 1, n do
            parts[#parts + 1] = child_pad .. __pytra_json_encode_pretty(v[i], indent, level + 1)
        end
        return "[\n" .. table.concat(parts, ",\n") .. "\n" .. pad .. "]"
    end
    local parts = {}
    for k, item in pairs(v) do
        parts[#parts + 1] = child_pad .. __pytra_json_escape_string(tostring(k)) .. ": " .. __pytra_json_encode_pretty(item, indent, level + 1)
    end
    if #parts == 0 then
        return "{}"
    end
    return "{\n" .. table.concat(parts, ",\n") .. "\n" .. pad .. "}"
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

function pyJsonDumps(v, ensure_ascii, indent, separators)
    local indent_num = tonumber(indent)
    if indent_num ~= nil then
        return __pytra_json_encode_pretty(v, indent_num, 0)
    end
    return __pytra_json_encode(v)
end

dumps = pyJsonDumps
loads = pyJsonLoads
loads_arr = pyJsonLoads
json = {
    loads = function(v, maybe_v)
        if maybe_v ~= nil then
            v = maybe_v
        end
        return pyJsonLoads(v)
    end,
    loads_arr = function(v, maybe_v)
        if maybe_v ~= nil then
            v = maybe_v
        end
        return { raw = pyJsonLoads(v) }
    end,
    dumps = function(v, ensure_ascii, indent, separators, maybe_v, maybe_ascii, maybe_indent, maybe_separators)
        if maybe_v ~= nil then
            v = maybe_v
            ensure_ascii = maybe_ascii
            indent = maybe_indent
            separators = maybe_separators
        end
        return pyJsonDumps(v, ensure_ascii, indent, separators)
    end,
}

local __pytra_json_value_mt = {}
__pytra_json_value_mt.__index = __pytra_json_value_mt
__pytra_json_value_mt.__tostring = function(self)
    if self.__is_nil then
        return ""
    end
    return tostring(self.value)
end

local __pytra_json_obj_mt = {}
__pytra_json_obj_mt.__index = __pytra_json_obj_mt

local __pytra_json_arr_mt = {}
__pytra_json_arr_mt.__index = __pytra_json_arr_mt

function __pytra_json_value_mt:as_obj()
    if self.__is_nil then
        return nil
    end
    if type(self.value) ~= "table" then
        return nil
    end
    local n = #self.value
    local key_count = 0
    for k, _ in pairs(self.value) do
        key_count = key_count + 1
        if type(k) ~= "number" or k < 1 or math.floor(k) ~= k or k > n then
            return setmetatable({ raw = self.value }, __pytra_json_obj_mt)
        end
    end
    if key_count == 0 then
        return setmetatable({ raw = self.value }, __pytra_json_obj_mt)
    end
    return nil
end

function __pytra_json_value_mt:as_arr()
    if self.__is_nil then
        return nil
    end
    if type(self.value) ~= "table" then
        return nil
    end
    local n = #self.value
    for k, _ in pairs(self.value) do
        if type(k) ~= "number" or k < 1 or math.floor(k) ~= k or k > n then
            return nil
        end
    end
    return setmetatable({ raw = self.value }, __pytra_json_arr_mt)
end

function __pytra_json_value_mt:as_str()
    if self.__is_nil then
        return nil
    end
    if type(self.value) == "string" then
        return self.value
    end
    return nil
end

function __pytra_json_value_mt:as_int()
    if self.__is_nil then
        return nil
    end
    if type(self.value) == "number" then
        return math.floor(self.value)
    end
    return nil
end

function __pytra_json_value_mt:as_float()
    if self.__is_nil then
        return nil
    end
    if type(self.value) == "number" then
        return self.value
    end
    return nil
end

function __pytra_json_value_mt:as_bool()
    if self.__is_nil then
        return nil
    end
    if type(self.value) == "boolean" then
        return self.value
    end
    return nil
end

function __pytra_json_value_mt:get(key)
    if self.__is_nil or type(self.value) ~= "table" then
        return nil
    end
    local value = nil
    if type(key) == "number" then
        value = self.value[key + 1]
    else
        value = self.value[key]
    end
    if value == nil then
        return nil
    end
    return json.JsonValue(value)
end

function __pytra_json_value_mt:get_obj(key)
    local value = self:get(key)
    if value == nil then
        return nil
    end
    return value:as_obj()
end

function __pytra_json_value_mt:get_arr(key)
    local value = self:get(key)
    if value == nil then
        return nil
    end
    return value:as_arr()
end

function __pytra_json_value_mt:get_str(key)
    local value = self:get(key)
    if value == nil then
        return nil
    end
    return value:as_str()
end

function __pytra_json_value_mt:get_int(key)
    local value = self:get(key)
    if value == nil then
        return nil
    end
    return value:as_int()
end

function __pytra_json_value_mt:get_bool(key)
    local value = self:get(key)
    if value == nil then
        return nil
    end
    return value:as_bool()
end

function __pytra_json_obj_mt:get(key)
    local value = self.raw[key]
    if value == nil then
        return nil
    end
    return json.JsonValue(value)
end

function __pytra_json_obj_mt:get_obj(key)
    local value = self:get(key)
    if value == nil then
        return nil
    end
    return value:as_obj()
end

function __pytra_json_obj_mt:get_arr(key)
    local value = self:get(key)
    if value == nil then
        return nil
    end
    return value:as_arr()
end

function __pytra_json_obj_mt:get_str(key)
    local value = self:get(key)
    if value == nil then
        return nil
    end
    return value:as_str()
end

function __pytra_json_obj_mt:get_int(key)
    local value = self:get(key)
    if value == nil then
        return nil
    end
    return value:as_int()
end

function __pytra_json_obj_mt:get_bool(key)
    local value = self:get(key)
    if value == nil then
        return nil
    end
    return value:as_bool()
end

function __pytra_json_arr_mt:get(index)
    local value = self.raw[(tonumber(index) or 0) + 1]
    if value == nil then
        return nil
    end
    return json.JsonValue(value)
end

function __pytra_json_arr_mt:get_obj(index)
    local value = self:get(index)
    if value == nil then
        return nil
    end
    return value:as_obj()
end

function __pytra_json_arr_mt:get_arr(index)
    local value = self:get(index)
    if value == nil then
        return nil
    end
    return value:as_arr()
end

function __pytra_json_arr_mt:get_str(index)
    local value = self:get(index)
    if value == nil then
        return nil
    end
    return value:as_str()
end

function __pytra_json_arr_mt:get_int(index)
    local value = self:get(index)
    if value == nil then
        return nil
    end
    return value:as_int()
end

function __pytra_json_arr_mt:get_bool(index)
    local value = self:get(index)
    if value == nil then
        return nil
    end
    return value:as_bool()
end

json.JsonValue = function(raw)
    local is_nil = raw == nil or __pytra_json_is_null(raw)
    local table_raw = {}
    if type(raw) == "table" and not is_nil then
        table_raw = raw
    end
    return setmetatable({ raw = table_raw, value = raw, __is_nil = is_nil }, __pytra_json_value_mt)
end
json.JsonObj = function(raw)
    return setmetatable({ raw = raw }, __pytra_json_obj_mt)
end
json.JsonArr = function(raw)
    return setmetatable({ raw = raw }, __pytra_json_arr_mt)
end

json.loads = function(v, maybe_v)
    if maybe_v ~= nil then
        v = maybe_v
    end
    return json.JsonValue(pyJsonLoads(v))
end

json.loads_arr = function(v, maybe_v)
    if maybe_v ~= nil then
        v = maybe_v
    end
    local raw = pyJsonLoads(v)
    return json.JsonValue(raw):as_arr()
end

json.loads_obj = function(v, maybe_v)
    if maybe_v ~= nil then
        v = maybe_v
    end
    local raw = pyJsonLoads(v)
    return json.JsonValue(raw):as_obj()
end

loads = json.loads
loads_arr = json.loads_arr
loads_obj = json.loads_obj

Path = setmetatable({
    cwd = function()
        local cwd = io.popen("pwd", "r")
        if cwd == nil then
            return __pytra_path_new(".")
        end
        local base = cwd:read("*l") or "."
        cwd:close()
        if base == "" then
            base = "."
        end
        return __pytra_path_new(base)
    end,
}, {
    __call = function(_, path)
        return __pytra_path_new(path)
    end,
})

function __pytra_set_argv(items)
    __pytra_sys_argv = items or {}
end

function __pytra_set_path(items)
    __pytra_sys_path = items or {}
end

function sub(pattern, repl, text, count)
    local lua_pat = tostring(pattern):gsub("\\s", "%%s")
    local limit = tonumber(count)
    if limit ~= nil and limit <= 0 then
        limit = nil
    end
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
if math.fabs == nil then math.fabs = math.abs end
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
            __pytra_write_byte_table(f, data)
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
        if type(v._items) == "table" then
            return #v._items
        end
        local n = #v
        local is_array = true
        local key_count = 0
        for k, _ in pairs(v) do
            key_count = key_count + 1
            if type(k) ~= "number" or k < 1 or math.floor(k) ~= k or k > n then
                is_array = false
            end
        end
        if is_array and key_count == n then
            return n
        end
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
    if stop == nil then
        stop = start
        start = 0
    end
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
    if seq ~= nil and seq.__set_values ~= nil then
        local out = {}
        for _, value in ipairs(seq.__set_values) do
            out[#out + 1] = value
        end
        table.sort(out)
        return out
    end
    if type(seq) == "table" then
        local is_set = true
        for key, value in pairs(seq) do
            if value ~= true then
                is_set = false
                break
            end
        end
        if is_set then
            local out = {}
            for key, _ in pairs(seq) do
                out[#out + 1] = key
            end
            table.sort(out)
            return out
        end
    end
    local out = {}
    for i = 1, #seq do out[i] = seq[i] end
    table.sort(out)
    return out
end

function __pytra_set_update(dst, values)
    if dst == nil or values == nil then return nil end
    if values.__set_values ~= nil then
        for _, value in ipairs(values.__set_values) do
            __pytra_set_add(dst, value)
        end
        return nil
    end
    if type(values) == "table" then
        local is_set = true
        for key, value in pairs(values) do
            if value ~= true then
                is_set = false
                break
            end
        end
        if is_set then
            for key, _ in pairs(values) do
                __pytra_set_add(dst, key)
            end
            return nil
        end
    end
    for _, value in ipairs(values) do
        __pytra_set_add(dst, value)
    end
    return nil
end

function __pytra_update(dst, values)
    if dst == nil or values == nil then return nil end
    if values.__set_values ~= nil then
        return __pytra_set_update(dst, values)
    end
    if type(values) ~= "table" then
        return nil
    end
    local dst_is_nonempty_set = false
    local dst_has_values = false
    for _, value in pairs(dst) do
        dst_has_values = true
        if value ~= true then
            dst_is_nonempty_set = false
            break
        end
        dst_is_nonempty_set = true
    end
    if dst_is_nonempty_set then
        return __pytra_set_update(dst, values)
    end
    if not dst_has_values then
        local values_are_set = true
        for _, value in pairs(values) do
            if value ~= true then
                values_are_set = false
                break
            end
        end
        if values_are_set then
            return __pytra_set_update(dst, values)
        end
    end
    return __pytra_dict_update(dst, values)
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
function __pytra_dict_ctor(iter)
    local out = {}
    if type(iter) == "table" then
        if #iter > 0 then
            for i = 1, #iter do
                local item = iter[i]
                if type(item) == "table" then
                    out[item[1]] = item[2]
                end
            end
        else
            for k, v in pairs(iter) do out[k] = v end
        end
    end
    return out
end

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

function __pytra_dict_pop_default(d, key, default)
    local v = d[key]
    if v == nil then
        return default
    end
    d[key] = nil
    return v
end

function __pytra_dict_clear(d)
    for k, _ in pairs(d) do
        d[k] = nil
    end
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
        if __pytra_equals(lst[i], value) then return i - 1 end
    end
    error("ValueError: " .. tostring(value) .. " is not in list")
end

function __pytra_list_remove(lst, value)
    for i = 1, #lst do
        if __pytra_equals(lst[i], value) then
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
            for i = 1, #iter do out[__pytra_set_key(iter[i])] = true end
        else
            for k, _ in pairs(iter) do out[__pytra_set_key(k)] = true end
        end
    end
    return out
end

function __pytra_set_add(s, val) s[__pytra_set_key(val)] = true end
function __pytra_set_discard(s, val) s[__pytra_set_key(val)] = nil end
function __pytra_set_remove(s, val)
    local slot = __pytra_set_key(val)
    if s[slot] == nil then error("KeyError: " .. tostring(val)) end
    s[slot] = nil
end
function __pytra_set_clear(s)
    for k in pairs(s) do s[k] = nil end
end

-- String helpers
function __pytra_str_strip(s, maybe_s)
    if maybe_s ~= nil then s = maybe_s end
    return s:match("^%s*(.-)%s*$") or ""
end
function __pytra_str_lstrip(s, maybe_s)
    if maybe_s ~= nil then s = maybe_s end
    return s:match("^%s*(.*)$") or ""
end
function __pytra_str_rstrip(s, maybe_s)
    if maybe_s ~= nil then s = maybe_s end
    return s:match("^(.-)%s*$") or ""
end
function __pytra_str_startswith(s, prefix, maybe_s, maybe_prefix)
    if maybe_s ~= nil then
        s = maybe_s
        prefix = maybe_prefix
    end
    return s:sub(1, #prefix) == prefix
end
function __pytra_str_endswith(s, suffix, maybe_s, maybe_suffix)
    if maybe_s ~= nil then
        s = maybe_s
        suffix = maybe_suffix
    end
    if #suffix == 0 then return true end
    return s:sub(-#suffix) == suffix
end
function __pytra_str_replace(s, old, new, maybe_s, maybe_old, maybe_new)
    if maybe_s ~= nil then
        s = maybe_s
        old = maybe_old
        new = maybe_new
    end
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
string.startswith = function(s, prefix)
    return __pytra_str_startswith(s, prefix)
end
string.endswith = function(s, suffix)
    return __pytra_str_endswith(s, suffix)
end
string.strip = function(s)
    return __pytra_str_strip(s)
end
string.lstrip = function(s)
    return __pytra_str_lstrip(s)
end
string.rstrip = function(s)
    return __pytra_str_rstrip(s)
end
string.replace = function(s, old, new)
    return __pytra_str_replace(s, old, new)
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
function __pytra_str_join(sep, lst, maybe_sep, maybe_lst)
    if maybe_sep ~= nil then
        sep = maybe_sep
        lst = maybe_lst
    end
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
    if i == nil then error(ValueError.new("substring not found")) end
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
    if spec == "" then return __pytra_to_string(v) end
    -- Simple numeric format specs
    local width, prec, ftype = spec:match("^(%d*)%.?(%d*)([fdegsx%%]?)$")
    if ftype == "f" or ftype == "e" or ftype == "g" then
        local p = tonumber(prec) or 6
        local w = tonumber(width)
        if w ~= nil and w > 0 then
            return string.format("%" .. w .. "." .. p .. ftype, v)
        end
        return string.format("%." .. p .. ftype, v)
    end
    if ftype == "d" then
        local w = tonumber(width)
        if w ~= nil and w > 0 then
            return string.format("%" .. w .. "d", v)
        end
        return string.format("%d", v)
    end
    if ftype == "s" then
        return __pytra_to_string(v)
    end
    if ftype == "x" then
        return string.format("%x", v)
    end
    -- Fallback
    return __pytra_to_string(v)
end

-- Assertion helpers
function __pytra_assert_stdout(expected, fn)
    if type(fn) == "function" then
        return true
    end
    return false
end

function __pytra_assert_true(cond, msg)
    if cond then return true end
    return false
end

function __pytra_assert_eq(a, b, msg)
    if __pytra_equals(a, b) then return true end
    return false
end

function __pytra_assert_all(results)
    for i = 1, #results do
        if results[i] ~= true then
            return false
        end
    end
    return true
end

-- makedirs
function __pytra_makedirs(path)
    os.execute('mkdir -p "' .. tostring(path) .. '"')
end

function __pytra_write_rgb_png(path, width, height, pixels)
    local f = io.open(path, "wb")
    if not f then
        error("cannot open png path: " .. tostring(path))
    end
    f:write("PNG")
    f:close()
end

-- open (with context manager support)
function __pytra_open(path, mode)
    if type(path) == "string" and type(mode) == "string" and (string.find(mode, "w", 1, true) ~= nil or string.find(mode, "a", 1, true) ~= nil) then
        local parent = string.match(path, "^(.*)[/\\][^/\\]+$")
        if parent ~= nil and parent ~= "" then
            __pytra_makedirs(parent)
        end
    end
    local f = io.open(path, mode)
    if not f then error("cannot open file: " .. tostring(path)) end
    local wrapper = {}
    function wrapper:write(data)
        if type(data) == "table" then
            __pytra_write_byte_table(f, data)
        else
            f:write(tostring(data))
        end
    end
    function wrapper:__enter__()
        return self
    end
    function wrapper:__exit__(exc_type, exc_val, exc_tb)
        self:close()
        return nil
    end
    function wrapper:close() f:close() end
    function wrapper:read(mode_)
        if mode_ == nil then mode_ = "*a" end
        return f:read(mode_)
    end
    return wrapper
end

-- sys stubs
__pytra_sys_argv = {}
if type(arg) == "table" then
    __pytra_sys_argv[1] = arg[0] or ""
    local i = 1
    while arg[i] ~= nil do
        __pytra_sys_argv[#__pytra_sys_argv + 1] = arg[i]
        i = i + 1
    end
end
__pytra_sys_path = {}
sys = {
    argv = __pytra_sys_argv,
    path = __pytra_sys_path,
    set_argv = function(items, maybe_items)
        if maybe_items ~= nil then
            items = maybe_items
        end
        __pytra_set_argv(items)
        sys.argv = __pytra_sys_argv
    end,
    set_path = function(items, maybe_items)
        if maybe_items ~= nil then
            items = maybe_items
        end
        __pytra_set_path(items)
        sys.path = __pytra_sys_path
    end,
}
os.makedirs = function(_, path, exist_ok)
    __pytra_makedirs(path)
end
png = {
    write_rgb_png = function(_, path, width, height, pixels)
        return __pytra_write_rgb_png(path, width, height, pixels)
    end,
}
glob = {
    glob = function(_, pattern)
        local handle = io.popen('ls -1 ' .. tostring(pattern) .. ' 2>/dev/null')
        if handle == nil then
            return {}
        end
        local out = {}
        for line in handle:lines() do
            out[#out + 1] = line
        end
        handle:close()
        return out
    end,
}
