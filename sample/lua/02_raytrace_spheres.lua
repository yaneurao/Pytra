local function __pytra_print(...)
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

local function __pytra_repeat_seq(a, b)
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

local function __pytra_truthy(v)
    if v == nil then return false end
    local t = type(v)
    if t == "boolean" then return v end
    if t == "number" then return v ~= 0 end
    if t == "string" then return #v ~= 0 end
    if t == "table" then return next(v) ~= nil end
    return true
end

local function __pytra_contains(container, value)
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

local function __pytra_str_isdigit(s)
    if type(s) ~= "string" or #s == 0 then return false end
    for i = 1, #s do
        local b = string.byte(s, i)
        if b < 48 or b > 57 then return false end
    end
    return true
end

local function __pytra_str_isalpha(s)
    if type(s) ~= "string" or #s == 0 then return false end
    for i = 1, #s do
        local b = string.byte(s, i)
        local is_upper = (b >= 65 and b <= 90)
        local is_lower = (b >= 97 and b <= 122)
        if not (is_upper or is_lower) then return false end
    end
    return true
end

local function __pytra_str_isalnum(s)
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

local function __pytra_perf_counter()
    return os.clock()
end

local function __pytra_math_module()
    local m = {}
    for k, v in pairs(math) do
        m[k] = v
    end
    if m.fabs == nil then m.fabs = math.abs end
    if m.log10 == nil then m.log10 = function(x) return math.log(x, 10) end end
    if m.pow == nil then m.pow = function(a, b) return (a ^ b) end end
    return m
end

local function __pytra_u32be(n)
    local v = math.floor(tonumber(n) or 0) & 0xFFFFFFFF
    return string.char((v >> 24) & 0xFF, (v >> 16) & 0xFF, (v >> 8) & 0xFF, v & 0xFF)
end

local __pytra_crc_table = nil
local function __pytra_init_crc_table()
    if __pytra_crc_table ~= nil then
        return
    end
    local tbl = {}
    for i = 0, 255 do
        local c = i
        for _ = 1, 8 do
            if (c & 1) ~= 0 then
                c = ((c >> 1) ~ 0xEDB88320) & 0xFFFFFFFF
            else
                c = (c >> 1) & 0xFFFFFFFF
            end
        end
        tbl[i] = c
    end
    __pytra_crc_table = tbl
end

local function __pytra_png_crc32(data)
    __pytra_init_crc_table()
    local c = 0xFFFFFFFF
    for i = 1, #data do
        local b = string.byte(data, i)
        local idx = (c ~ b) & 0xFF
        c = ((c >> 8) ~ __pytra_crc_table[idx]) & 0xFFFFFFFF
    end
    return (~c) & 0xFFFFFFFF
end

local function __pytra_png_adler32(data)
    local s1 = 1
    local s2 = 0
    for i = 1, #data do
        s1 = (s1 + string.byte(data, i)) % 65521
        s2 = (s2 + s1) % 65521
    end
    return ((s2 << 16) | s1) & 0xFFFFFFFF
end

local function __pytra_png_chunk(kind, data)
    local payload = data or ""
    local crc = __pytra_png_crc32(kind .. payload)
    return __pytra_u32be(#payload) .. kind .. payload .. __pytra_u32be(crc)
end

local function __pytra_zlib_store(raw)
    local out = { string.char(0x78, 0x01) }
    local pos = 1
    while pos <= #raw do
        local block_len = math.min(65535, #raw - pos + 1)
        local final_block = ((pos + block_len - 1) >= #raw) and 1 or 0
        local nlen = 65535 - block_len
        out[#out + 1] = string.char(final_block, block_len & 0xFF, (block_len >> 8) & 0xFF, nlen & 0xFF, (nlen >> 8) & 0xFF)
        out[#out + 1] = string.sub(raw, pos, pos + block_len - 1)
        pos = pos + block_len
    end
    out[#out + 1] = __pytra_u32be(__pytra_png_adler32(raw))
    return table.concat(out)
end

local function __pytra_write_rgb_png(path, width, height, pixels)
    local out_path = tostring(path)
    local w = math.floor(tonumber(width) or 0)
    local h = math.floor(tonumber(height) or 0)
    if w <= 0 or h <= 0 then
        error("write_rgb_png: width/height must be positive")
    end
    if type(pixels) ~= "table" then
        error("write_rgb_png: pixels must be table")
    end
    local expected = w * h * 3
    if #pixels ~= expected then
        error("write_rgb_png: pixels length mismatch")
    end
    local scan = {}
    local idx = 1
    for _y = 1, h do
        scan[#scan + 1] = string.char(0)
        for _x = 1, w * 3 do
            local n = math.floor(tonumber(pixels[idx]) or 0)
            if n < 0 then n = 0 end
            if n > 255 then n = 255 end
            scan[#scan + 1] = string.char(n)
            idx = idx + 1
        end
    end
    local raw = table.concat(scan)
    local ihdr = __pytra_u32be(w) .. __pytra_u32be(h) .. string.char(8, 2, 0, 0, 0)
    local idat = __pytra_zlib_store(raw)
    local png_data = string.char(137, 80, 78, 71, 13, 10, 26, 10) .. __pytra_png_chunk("IHDR", ihdr) .. __pytra_png_chunk("IDAT", idat) .. __pytra_png_chunk("IEND", "")
    local fh = assert(io.open(out_path, "wb"))
    fh:write(png_data)
    fh:close()
end

local function __pytra_png_module()
    return {
        write_rgb_png = function(...)
            local argc = select("#", ...)
            if argc == 5 then
                local _, path, width, height, pixels = ...
                return __pytra_write_rgb_png(path, width, height, pixels)
            end
            local path, width, height, pixels = ...
            return __pytra_write_rgb_png(path, width, height, pixels)
        end,
        write_gif = function(...)
            error("lua runtime: write_gif is not implemented")
        end,
    }
end

local math = __pytra_math_module()
local png = __pytra_png_module()
local perf_counter = __pytra_perf_counter

-- 02: Sample that runs a mini sphere-only ray tracer and outputs a PNG image.
-- Dependencies are kept minimal (time only) for transpilation compatibility.

function clamp01(v)
    if (v < 0.0) then
        return 0.0
    end
    if (v > 1.0) then
        return 1.0
    end
    return v
end

function hit_sphere(ox, oy, oz, dx, dy, dz, cx, cy, cz, r)
    local lx = (ox - cx)
    local ly = (oy - cy)
    local lz = (oz - cz)
    
    local a = (((dx * dx) + (dy * dy)) + (dz * dz))
    local b = (2.0 * (((lx * dx) + (ly * dy)) + (lz * dz)))
    local c = ((((lx * lx) + (ly * ly)) + (lz * lz)) - (r * r))
    
    local d = ((b * b) - ((4.0 * a) * c))
    if (d < 0.0) then
        return (-1.0)
    end
    local sd = math.sqrt(d)
    local t0 = (((-b) - sd) / (2.0 * a))
    local t1 = (((-b) + sd) / (2.0 * a))
    
    if (t0 > 0.001) then
        return t0
    end
    if (t1 > 0.001) then
        return t1
    end
    return (-1.0)
end

function render(width, height, aa)
    local pixels = {}
    
    -- Camera origin
    local ox = 0.0
    local oy = 0.0
    local oz = (-3.0)
    
    -- Light direction (normalized)
    local lx = (-0.4)
    local ly = 0.8
    local lz = (-0.45)
    local __hoisted_cast_1 = (tonumber(aa) or 0.0)
    local __hoisted_cast_2 = (tonumber((height - 1)) or 0.0)
    local __hoisted_cast_3 = (tonumber((width - 1)) or 0.0)
    local __hoisted_cast_4 = (tonumber(height) or 0.0)
    
    for y = 0, (height) - 1, 1 do
        for x = 0, (width) - 1, 1 do
            local ar = 0
            local ag = 0
            local ab = 0
            
            for ay = 0, (aa) - 1, 1 do
                for ax = 0, (aa) - 1, 1 do
                    fy = ((y + ((ay + 0.5) / __hoisted_cast_1)) / __hoisted_cast_2)
                    fx = ((x + ((ax + 0.5) / __hoisted_cast_1)) / __hoisted_cast_3)
                    local sy = (1.0 - (2.0 * fy))
                    local sx = (((2.0 * fx) - 1.0) * (width / __hoisted_cast_4))
                    
                    local dx = sx
                    local dy = sy
                    local dz = 1.0
                    local inv_len = (1.0 / math.sqrt((((dx * dx) + (dy * dy)) + (dz * dz))))
                    dx = dx * inv_len
                    dy = dy * inv_len
                    dz = dz * inv_len
                    
                    local t_min = 1e+30
                    local hit_id = (-1)
                    
                    local t = hit_sphere(ox, oy, oz, dx, dy, dz, (-0.8), (-0.2), 2.2, 0.8)
                    if ((t > 0.0) and (t < t_min)) then
                        t_min = t
                        hit_id = 0
                    end
                    t = hit_sphere(ox, oy, oz, dx, dy, dz, 0.9, 0.1, 2.9, 0.95)
                    if ((t > 0.0) and (t < t_min)) then
                        t_min = t
                        hit_id = 1
                    end
                    t = hit_sphere(ox, oy, oz, dx, dy, dz, 0.0, (-1001.0), 3.0, 1000.0)
                    if ((t > 0.0) and (t < t_min)) then
                        t_min = t
                        hit_id = 2
                    end
                    local r = 0
                    local g = 0
                    local b = 0
                    
                    if (hit_id >= 0) then
                        local px = (ox + (dx * t_min))
                        local py = (oy + (dy * t_min))
                        local pz = (oz + (dz * t_min))
                        
                        local nx = 0.0
                        local ny = 0.0
                        local nz = 0.0
                        
                        if (hit_id == 0) then
                            nx = ((px + 0.8) / 0.8)
                            ny = ((py + 0.2) / 0.8)
                            nz = ((pz - 2.2) / 0.8)
                        else
                            if (hit_id == 1) then
                                nx = ((px - 0.9) / 0.95)
                                ny = ((py - 0.1) / 0.95)
                                nz = ((pz - 2.9) / 0.95)
                            else
                                nx = 0.0
                                ny = 1.0
                                nz = 0.0
                            end
                        end
                        local diff = (((nx * (-lx)) + (ny * (-ly))) + (nz * (-lz)))
                        diff = clamp01(diff)
                        
                        local base_r = 0.0
                        local base_g = 0.0
                        local base_b = 0.0
                        
                        if (hit_id == 0) then
                            base_r = 0.95
                            base_g = 0.35
                            base_b = 0.25
                        else
                            if (hit_id == 1) then
                                base_r = 0.25
                                base_g = 0.55
                                base_b = 0.95
                            else
                                local checker = ((math.floor(tonumber(((px + 50.0) * 0.8)) or 0)) + (math.floor(tonumber(((pz + 50.0) * 0.8)) or 0)))
                                if ((checker % 2) == 0) then
                                    base_r = 0.85
                                    base_g = 0.85
                                    base_b = 0.85
                                else
                                    base_r = 0.2
                                    base_g = 0.2
                                    base_b = 0.2
                                end
                            end
                        end
                        local shade = (0.12 + (0.88 * diff))
                        r = (math.floor(tonumber((255.0 * clamp01((base_r * shade)))) or 0))
                        g = (math.floor(tonumber((255.0 * clamp01((base_g * shade)))) or 0))
                        b = (math.floor(tonumber((255.0 * clamp01((base_b * shade)))) or 0))
                    else
                        local tsky = (0.5 * (dy + 1.0))
                        r = (math.floor(tonumber((255.0 * (0.65 + (0.2 * tsky)))) or 0))
                        g = (math.floor(tonumber((255.0 * (0.75 + (0.18 * tsky)))) or 0))
                        b = (math.floor(tonumber((255.0 * (0.9 + (0.08 * tsky)))) or 0))
                    end
                    ar = ar + r
                    ag = ag + g
                    ab = ab + b
                    ::__pytra_continue_4::
                end
                ::__pytra_continue_3::
            end
            samples = (aa * aa)
            table.insert(pixels, (ar // samples))
            table.insert(pixels, (ag // samples))
            table.insert(pixels, (ab // samples))
            ::__pytra_continue_2::
        end
        ::__pytra_continue_1::
    end
    return pixels
end

function run_raytrace()
    local width = 1600
    local height = 900
    local aa = 2
    local out_path = "sample/out/02_raytrace_spheres.png"
    
    local start = perf_counter()
    local pixels = render(width, height, aa)
    png.write_rgb_png(out_path, width, height, pixels)
    local elapsed = (perf_counter() - start)
    
    __pytra_print("output:", out_path)
    __pytra_print("size:", width, "x", height)
    __pytra_print("elapsed_sec:", elapsed)
end


run_raytrace()
