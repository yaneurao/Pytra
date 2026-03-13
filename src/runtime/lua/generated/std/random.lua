-- AUTO-GENERATED FILE. DO NOT EDIT.
-- source: src/pytra/std/random.py
-- generated-by: tools/gen_runtime_from_manifest.py

dofile((debug.getinfo(1, "S").source:sub(2):match("^(.*[\\/])") or "") .. "py_runtime.lua")

local _math = __pytra_math_module()

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

local _state_box = { 2463534242 }
local _gauss_has_spare = { 0 }
local _gauss_spare = { 0.0 }
function seed(value)
    local v = (value & 2147483647)
    if (v == 0) then
        v = 1
    end
    _state_box[1] = v
    _gauss_has_spare[1] = 0
end

function _next_u31()
    local s = _state_box[1]
    s = (((1103515245 * s) + 12345) & 2147483647)
    _state_box[1] = s
    return s
end

function random()
    return (_next_u31() / 2147483648.0)
end

function randint(a, b)
    local lo = a
    local hi = b
    if (hi < lo) then
        local __swap_1 = lo
        lo = hi
        hi = __swap_1
    end
    local span = ((hi - lo) + 1)
    return (lo + __pytra_int((random() * span)))
end

function choices(population, weights, k)
    local n = #(population)
    if (n <= 0) then
        return {  }
    end
    local draws = k
    if (draws < 0) then
        draws = 0
    end
    local weight_vals = {  }
    for _, w in ipairs(weights) do
        table.insert(weight_vals, w)
    end
    local out = {  }
    if (#(weight_vals) == n) then
        local total = 0.0
        for _, w in ipairs(weight_vals) do
            if (w > 0.0) then
                total = total + w
            end
        end
        if (total > 0.0) then
            for _ = 0, draws - 1 do
                local r = (random() * total)
                local acc = 0.0
                local picked_i = (n - 1)
                for i = 0, n - 1 do
                    local w = weight_vals[(((i) < 0) and (#(weight_vals) + (i) + 1) or ((i) + 1))]
                    if (w > 0.0) then
                        acc = acc + w
                    end
                    if (r < acc) then
                        picked_i = i
                        break
                    end
                end
                table.insert(out, population[(((picked_i) < 0) and (#(population) + (picked_i) + 1) or ((picked_i) + 1))])
            end
            return out
        end
    end
    for _ = 0, draws - 1 do
        table.insert(out, population[(((randint(0, (n - 1))) < 0) and (#(population) + (randint(0, (n - 1))) + 1) or ((randint(0, (n - 1))) + 1))])
    end
    return out
end

function gauss(mu, sigma)
    if (_gauss_has_spare[1] ~= 0) then
        _gauss_has_spare[1] = 0
        return (mu + (sigma * _gauss_spare[1]))
    end
    local u1 = 0.0
    while (u1 <= 1e-12) do
        u1 = random()
    end
    local u2 = random()
    local mag = _math.sqrt(((-2.0) * _math.log(u1)))
    local z0 = (mag * _math.cos(((2.0 * _math.pi) * u2)))
    local z1 = (mag * _math.sin(((2.0 * _math.pi) * u2)))
    _gauss_spare[1] = z1
    _gauss_has_spare[1] = 1
    return (mu + (sigma * z0))
end

function shuffle(xs)
    local i = (#(xs) - 1)
    while (i > 0) do
        local j = randint(0, i)
        if (j ~= i) then
            local tmp = xs[(((i) < 0) and (#(xs) + (i) + 1) or ((i) + 1))]
            xs[(((i) < 0) and (#(xs) + (i) + 1) or ((i) + 1))] = xs[(((j) < 0) and (#(xs) + (j) + 1) or ((j) + 1))]
            xs[(((j) < 0) and (#(xs) + (j) + 1) or ((j) + 1))] = tmp
        end
        i = i - 1
    end
end
