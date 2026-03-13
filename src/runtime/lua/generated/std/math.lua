-- AUTO-GENERATED FILE. DO NOT EDIT.
-- source: src/pytra/std/math.py
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

local pi = extern(__m.pi)
local e = extern(__m.e)
function sqrt(x)
    return __m:sqrt(x)
end

function sin(x)
    return __m:sin(x)
end

function cos(x)
    return __m:cos(x)
end

function tan(x)
    return __m:tan(x)
end

function exp(x)
    return __m:exp(x)
end

function log(x)
    return __m:log(x)
end

function log10(x)
    return __m:log10(x)
end

function fabs(x)
    return __m:fabs(x)
end

function floor(x)
    return __m:floor(x)
end

function ceil(x)
    return __m:ceil(x)
end

function pow(x, y)
    return __m:pow(x, y)
end
