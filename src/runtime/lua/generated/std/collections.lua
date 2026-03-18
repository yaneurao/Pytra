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

deque = {}
deque.__index = deque

function deque.new()
    local self = setmetatable({}, deque)
    self._items = {  }
    return self
end

function deque:append(value)
    table.insert(self._items, value)
end

function deque:appendleft(value)
    self._items:insert(0, value)
end

function deque:pop()
    if (#(self._items) == 0) then
        error(IndexError("pop from empty deque"))
    end
    return table.remove(self._items)
end

function deque:popleft()
    if (#(self._items) == 0) then
        error(IndexError("pop from empty deque"))
    end
    local item = self._items[1]
    self._items = __pytra_slice(self._items, 1, nil)
    return item
end

function deque:__len__()
    return #(self._items)
end

function deque:clear()
    self._items = {  }
end
