-- AUTO-GENERATED FILE. DO NOT EDIT.
-- source: src/pytra/std/argparse.py
-- generated-by: tools/gen_runtime_from_manifest.py

dofile((debug.getinfo(1, "S").source:sub(2):match("^(.*[\\/])") or "") .. "py_runtime.lua")

local sys = { argv = (arg or {}), path = {}, stderr = { write = function(text) io.stderr:write(text) end }, stdout = { write = function(text) io.write(text) end }, exit = function(code) os.exit(tonumber(code) or 0) end, set_argv = function(_values) end, set_path = function(_values) end, write_stderr = function(text) io.stderr:write(text) end, write_stdout = function(text) io.write(text) end }

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

Namespace = {}
Namespace.__index = Namespace

function Namespace.new(values)
    local self = setmetatable({}, Namespace)
    if (values == nil) then
        self.values = {}
        return nil
    end
    self.values = values
    return self
end

_ArgSpec = {}
_ArgSpec.__index = _ArgSpec

function _ArgSpec.new(names, action, choices, default, help_text)
    local self = setmetatable({}, _ArgSpec)
    self.names = names
    self.action = action
    self.choices = choices
    self.default = default
    self.help_text = help_text
    self.is_optional = ((#(names) > 0) and py_startswith(names[1], "-"))
    if self.is_optional then
        local base = py_replace(py_lstrip_chars(names[(#(names) + (-1) + 1)], "-"), "-", "_")
        self.dest = base
    else
        self.dest = names[1]
    end
    return self
end

ArgumentParser = {}
ArgumentParser.__index = ArgumentParser

function ArgumentParser.new(description)
    local self = setmetatable({}, ArgumentParser)
    self.description = description
    self._specs = {  }
    return self
end

function ArgumentParser:add_argument(name0, name1, name2, name3, help, action, choices, default)
    local names = {  }
    if (name0 ~= "") then
        table.insert(names, name0)
    end
    if (name1 ~= "") then
        table.insert(names, name1)
    end
    if (name2 ~= "") then
        table.insert(names, name2)
    end
    if (name3 ~= "") then
        table.insert(names, name3)
    end
    if (#(names) == 0) then
        error("add_argument requires at least one name")
    end
    local spec = _ArgSpec.new(names)
    table.insert(self._specs, spec)
end

function ArgumentParser:_fail(msg)
    if (msg ~= "") then
        sys.write_stderr(("error: " .. tostring(msg) .. "\n"))
    end
    error(SystemExit(2))
end

function ArgumentParser:parse_args(argv)
    local args = nil
    if (argv == nil) then
        args = __pytra_slice(sys.argv, 1, nil)
    else
        args = list(argv)
    end
    local specs_pos = {  }
    local specs_opt = {  }
    for _, s in ipairs(self._specs) do
        if s.is_optional then
            table.insert(specs_opt, s)
        else
            table.insert(specs_pos, s)
        end
    end
    local by_name = {}
    local spec_i = 0
    for _, s in ipairs(specs_opt) do
        for _, n in ipairs(s.names) do
            by_name[n] = spec_i
        end
        spec_i = spec_i + 1
    end
    local values = {}
    for _, s in ipairs(self._specs) do
        if (s.action == "store_true") then
            values[s.dest] = (function() if __pytra_truthy((s.default == nil)) then return (__pytra_truthy(s.default)) else return (false) end end)()
        else
            if (s.default == nil) then
                values[s.dest] = s.default
            else
                values[s.dest] = nil
            end
        end
    end
    local pos_i = 0
    local i = 0
    while (i < #(args)) do
        local tok = args[(((i) < 0) and (#(args) + (i) + 1) or ((i) + 1))]
        if py_startswith(tok, "-") then
            if (not __pytra_contains(by_name, tok)) then
                self:_fail(("unknown option: " .. tostring(tok)))
            end
            local spec = specs_opt[(((by_name[tok]) < 0) and (#(specs_opt) + (by_name[tok]) + 1) or ((by_name[tok]) + 1))]
            if (spec.action == "store_true") then
                values[spec.dest] = true
                i = i + 1
                goto __pytra_continue_5
            end
            if ((i + 1) >= #(args)) then
                self:_fail(("missing value for option: " .. tostring(tok)))
            end
            local val = args[((((i + 1)) < 0) and (#(args) + ((i + 1)) + 1) or (((i + 1)) + 1))]
            if ((#(spec.choices) > 0) and (not __pytra_contains(spec.choices, val))) then
                self:_fail(("invalid choice for " .. tostring(tok) .. ": " .. tostring(val)))
            end
            values[spec.dest] = val
            i = i + 2
            goto __pytra_continue_5
        end
        if (pos_i >= #(specs_pos)) then
            self:_fail(("unexpected extra argument: " .. tostring(tok)))
        end
        spec = specs_pos[(((pos_i) < 0) and (#(specs_pos) + (pos_i) + 1) or ((pos_i) + 1))]
        values[spec.dest] = tok
        pos_i = pos_i + 1
        i = i + 1
        ::__pytra_continue_5::
    end
    if (pos_i < #(specs_pos)) then
        self:_fail(("missing required argument: " .. tostring(specs_pos[(((pos_i) < 0) and (#(specs_pos) + (pos_i) + 1) or ((pos_i) + 1))].dest)))
    end
    return values
end
