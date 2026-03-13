-- AUTO-GENERATED FILE. DO NOT EDIT.
-- source: src/pytra/std/pathlib.py
-- generated-by: tools/gen_runtime_from_manifest.py

dofile((debug.getinfo(1, "S").source:sub(2):match("^(.*[\\/])") or "") .. "py_runtime.lua")

local py_glob = { glob = function(_pattern) return {} end }
local os = { getcwd = function() return '.' end, mkdir = function(_p) end, makedirs = function(_p, _exist_ok) end }
local path = { join = function(a, b) return tostring(a) .. '/' .. tostring(b) end, dirname = function(_p) return '' end, basename = function(p) return tostring(p) end, splitext = function(p) return { tostring(p), '' } end, abspath = function(p) return tostring(p) end, exists = function(_p) return false end }

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

Path = {}
Path.__index = Path

function Path.new(value)
    local self = setmetatable({}, Path)
    self._value = value
    return self
end

function Path:__str__()
    return self._value
end

function Path:__repr__()
    return (("Path(" .. self._value) .. ")")
end

function Path:__fspath__()
    return self._value
end

function Path:__truediv__(rhs)
    return Path.new(path.join(self._value, rhs))
end

function Path:parent()
    local parent_txt = path.dirname(self._value)
    if (parent_txt == "") then
        parent_txt = "."
    end
    return Path.new(parent_txt)
end

function Path:parents()
    local out = {  }
    local current = path.dirname(self._value)
    while true do
        if (current == "") then
            current = "."
        end
        table.insert(out, Path.new(current))
        local next_current = path.dirname(current)
        if (next_current == "") then
            next_current = "."
        end
        if (next_current == current) then
            break
        end
        current = next_current
    end
    return out
end

function Path:name()
    return path.basename(self._value)
end

function Path:suffix()
    local __pytra_tuple_2 = path.splitext(path.basename(self._value))
    local _ = __pytra_tuple_2[1]
    local ext = __pytra_tuple_2[2]
    return ext
end

function Path:stem()
    local __pytra_tuple_3 = path.splitext(path.basename(self._value))
    local root = __pytra_tuple_3[1]
    local _ = __pytra_tuple_3[2]
    return root
end

function Path:resolve()
    return Path.new(path.abspath(self._value))
end

function Path:exists()
    return path.exists(self._value)
end

function Path:mkdir(parents, exist_ok)
    if parents then
        os.makedirs(self._value, exist_ok)
        return nil
    end
    if (exist_ok and path.exists(self._value)) then
        return nil
    end
    os.mkdir(self._value)
end

function Path:read_text(encoding)
    local f = open(self._value, "r", encoding)
    return f:read()
end

function Path:write_text(text, encoding)
    local f = open(self._value, "w", encoding)
    return f:write(text)
end

function Path:glob(pattern)
    local paths = py_glob.glob(path.join(self._value, pattern))
    local out = {  }
    for _, p in ipairs(paths) do
        table.insert(out, Path.new(p))
    end
    return out
end

function Path:cwd()
    return Path.new(os.getcwd())
end
