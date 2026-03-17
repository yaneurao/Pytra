-- AUTO-GENERATED FILE. DO NOT EDIT.
-- source: src/pytra/std/sys.py
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

local argv = extern(__s.argv)
local path = extern(__s.path)
stderr = extern(__s.stderr)
stdout = extern(__s.stdout)
function exit(code)
    __s:exit(code)
end

function set_argv(values)
    argv:clear()
    for _, v in ipairs(values) do
        table.insert(argv, v)
    end
end

function set_path(values)
    path:clear()
    for _, v in ipairs(values) do
        table.insert(path, v)
    end
end

function write_stderr(text)
    __s.stderr:write(text)
end

function write_stdout(text)
    __s.stdout:write(text)
end
