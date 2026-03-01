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

local function __pytra_u16le(n)
    local v = math.floor(tonumber(n) or 0) & 0xFFFF
    return string.char(v & 0xFF, (v >> 8) & 0xFF)
end

local function __pytra_to_byte_table(data)
    if type(data) == "string" then
        local out = {}
        for i = 1, #data do
            out[#out + 1] = string.byte(data, i)
        end
        return out
    end
    if type(data) == "table" then
        local out = {}
        for i = 1, #data do
            local n = math.floor(tonumber(data[i]) or 0)
            if n < 0 then n = 0 end
            if n > 255 then n = 255 end
            out[#out + 1] = n
        end
        return out
    end
    return {}
end

local function __pytra_bytes_from_table(data)
    local parts = {}
    for i = 1, #data do
        parts[#parts + 1] = string.char(data[i])
    end
    return table.concat(parts)
end

local function __pytra_gif_lzw_encode(data, min_code_size)
    if #data == 0 then return "" end
    local clear_code = 1 << min_code_size
    local end_code = clear_code + 1
    local code_size = min_code_size + 1
    local out = {}
    local bit_buffer = 0
    local bit_count = 0
    local function emit_code(code)
        bit_buffer = bit_buffer | (code << bit_count)
        bit_count = bit_count + code_size
        while bit_count >= 8 do
            out[#out + 1] = string.char(bit_buffer & 0xFF)
            bit_buffer = bit_buffer >> 8
            bit_count = bit_count - 8
        end
    end
    emit_code(clear_code)
    code_size = min_code_size + 1
    for i = 1, #data do
        emit_code(data[i])
        emit_code(clear_code)
        code_size = min_code_size + 1
    end
    emit_code(end_code)
    if bit_count > 0 then
        out[#out + 1] = string.char(bit_buffer & 0xFF)
    end
    return table.concat(out)
end

local function __pytra_grayscale_palette()
    local out = {}
    for i = 0, 255 do
        out[#out + 1] = i
        out[#out + 1] = i
        out[#out + 1] = i
    end
    return out
end

local function __pytra_save_gif(path, width, height, frames, palette, delay_cs, loop)
    local w = math.floor(tonumber(width) or 0)
    local h = math.floor(tonumber(height) or 0)
    local delay = math.floor(tonumber(delay_cs) or 4)
    local loop_count = math.floor(tonumber(loop) or 0)
    local palette_tbl = __pytra_to_byte_table(palette)
    if #palette_tbl ~= (256 * 3) then
        error("palette must be 256*3 bytes")
    end
    local norm_frames = {}
    for i = 1, #frames do
        local fr = __pytra_to_byte_table(frames[i])
        if #fr ~= (w * h) then
            error("frame size mismatch")
        end
        norm_frames[#norm_frames + 1] = fr
    end
    local out = {}
    out[#out + 1] = "GIF89a"
    out[#out + 1] = __pytra_u16le(w)
    out[#out + 1] = __pytra_u16le(h)
    out[#out + 1] = string.char(0xF7, 0, 0)
    out[#out + 1] = __pytra_bytes_from_table(palette_tbl)
    out[#out + 1] = string.char(0x21, 0xFF, 0x0B)
    out[#out + 1] = "NETSCAPE2.0"
    out[#out + 1] = string.char(0x03, 0x01)
    out[#out + 1] = __pytra_u16le(loop_count)
    out[#out + 1] = string.char(0x00)
    for i = 1, #norm_frames do
        local fr = norm_frames[i]
        out[#out + 1] = string.char(0x21, 0xF9, 0x04, 0x00)
        out[#out + 1] = __pytra_u16le(delay)
        out[#out + 1] = string.char(0x00, 0x00)
        out[#out + 1] = string.char(0x2C)
        out[#out + 1] = __pytra_u16le(0)
        out[#out + 1] = __pytra_u16le(0)
        out[#out + 1] = __pytra_u16le(w)
        out[#out + 1] = __pytra_u16le(h)
        out[#out + 1] = string.char(0x00)
        out[#out + 1] = string.char(8)
        local compressed = __pytra_gif_lzw_encode(fr, 8)
        local pos = 1
        while pos <= #compressed do
            local chunk = string.sub(compressed, pos, pos + 254)
            out[#out + 1] = string.char(#chunk)
            out[#out + 1] = chunk
            pos = pos + #chunk
        end
        out[#out + 1] = string.char(0x00)
    end
    out[#out + 1] = string.char(0x3B)
    local f = assert(io.open(tostring(path), "wb"))
    f:write(table.concat(out))
    f:close()
end

local function __pytra_gif_module()
    return {
        grayscale_palette = __pytra_grayscale_palette,
        save_gif = function(...)
            local path, width, height, frames, palette, delay_cs, loop = ...
            return __pytra_save_gif(path, width, height, frames, palette, delay_cs, loop)
        end,
    }
end

-- from __future__ import annotations as annotations (not yet mapped)
local math = __pytra_math_module()
local perf_counter = __pytra_perf_counter
local save_gif = __pytra_save_gif

-- 16: Sample that ray-traces chaotic rotation of glass sculptures and outputs a GIF.

function clamp01(v)
    if (v < 0.0) then
        return 0.0
    end
    if (v > 1.0) then
        return 1.0
    end
    return v
end

function dot(ax, ay, az, bx, by, bz)
    return (((ax * bx) + (ay * by)) + (az * bz))
end

function length(x, y, z)
    return math.sqrt((((x * x) + (y * y)) + (z * z)))
end

function normalize(x, y, z)
    l = length(x, y, z)
    if (l < 1e-09) then
        return { 0.0, 0.0, 0.0 }
    end
    return { (x / l), (y / l), (z / l) }
end

function reflect(ix, iy, iz, nx, ny, nz)
    d = (dot(ix, iy, iz, nx, ny, nz) * 2.0)
    return { (ix - (d * nx)), (iy - (d * ny)), (iz - (d * nz)) }
end

function refract(ix, iy, iz, nx, ny, nz, eta)
    -- Simple IOR-based refraction. Return reflection direction on total internal reflection.
    cosi = (-dot(ix, iy, iz, nx, ny, nz))
    sint2 = ((eta * eta) * (1.0 - (cosi * cosi)))
    if (sint2 > 1.0) then
        return reflect(ix, iy, iz, nx, ny, nz)
    end
    cost = math.sqrt((1.0 - sint2))
    k = ((eta * cosi) - cost)
    return { ((eta * ix) + (k * nx)), ((eta * iy) + (k * ny)), ((eta * iz) + (k * nz)) }
end

function schlick(cos_theta, f0)
    m = (1.0 - cos_theta)
    return (f0 + ((1.0 - f0) * ((((m * m) * m) * m) * m)))
end

function sky_color(dx, dy, dz, tphase)
    -- Sky gradient + neon band
    t = (0.5 * (dy + 1.0))
    r = (0.06 + (0.2 * t))
    g = (0.1 + (0.25 * t))
    b = (0.16 + (0.45 * t))
    band = (0.5 + (0.5 * math.sin((((8.0 * dx) + (6.0 * dz)) + tphase))))
    r = r + (0.08 * band)
    g = g + (0.05 * band)
    b = b + (0.12 * band)
    return { clamp01(r), clamp01(g), clamp01(b) }
end

function sphere_intersect(ox, oy, oz, dx, dy, dz, cx, cy, cz, radius)
    lx = (ox - cx)
    ly = (oy - cy)
    lz = (oz - cz)
    b = (((lx * dx) + (ly * dy)) + (lz * dz))
    c = ((((lx * lx) + (ly * ly)) + (lz * lz)) - (radius * radius))
    h = ((b * b) - c)
    if (h < 0.0) then
        return (-1.0)
    end
    s = math.sqrt(h)
    t0 = ((-b) - s)
    if (t0 > 0.0001) then
        return t0
    end
    t1 = ((-b) + s)
    if (t1 > 0.0001) then
        return t1
    end
    return (-1.0)
end

function palette_332()
    -- 3-3-2 quantized palette. Lightweight quantization that stays fast after transpilation.
    p = (function(__v) if type(__v) == "number" then local __n = math.max(0, math.floor(tonumber(__v) or 0)); local __out = {}; for __i = 1, __n do __out[#__out + 1] = 0 end; return __out elseif type(__v) == "table" then local __out = {}; for __i = 1, #__v do __out[#__out + 1] = __v[__i] end; return __out else return {} end end)((256 * 3))
    local __hoisted_cast_1 = (tonumber(7) or 0.0)
    local __hoisted_cast_2 = (tonumber(3) or 0.0)
    for i = 0, (256) - 1, 1 do
        r = ((i + 5) + 7)
        g = ((i + 2) + 7)
        b = (i + 3)
        p[(((((i * 3) + 0)) < 0) and (#(p) + (((i * 3) + 0)) + 1) or ((((i * 3) + 0)) + 1))] = (math.floor(tonumber(((255 * r) / __hoisted_cast_1)) or 0))
        p[(((((i * 3) + 1)) < 0) and (#(p) + (((i * 3) + 1)) + 1) or ((((i * 3) + 1)) + 1))] = (math.floor(tonumber(((255 * g) / __hoisted_cast_1)) or 0))
        p[(((((i * 3) + 2)) < 0) and (#(p) + (((i * 3) + 2)) + 1) or ((((i * 3) + 2)) + 1))] = (math.floor(tonumber(((255 * b) / __hoisted_cast_2)) or 0))
        ::__pytra_continue_1::
    end
    return (function(__v) if type(__v) == "number" then local __n = math.max(0, math.floor(tonumber(__v) or 0)); local __out = {}; for __i = 1, __n do __out[#__out + 1] = 0 end; return __out elseif type(__v) == "table" then local __out = {}; for __i = 1, #__v do __out[#__out + 1] = __v[__i] end; return __out elseif type(__v) == "string" then local __out = {}; for __i = 1, #__v do __out[#__out + 1] = string.byte(__v, __i) end; return __out else return {} end end)(p)
end

function quantize_332(r, g, b)
    rr = (math.floor(tonumber((clamp01(r) * 255.0)) or 0))
    gg = (math.floor(tonumber((clamp01(g) * 255.0)) or 0))
    bb = (math.floor(tonumber((clamp01(b) * 255.0)) or 0))
    return ((((rr + 5) + 5) + ((gg + 5) + 2)) + (bb + 6))
end

function render_frame(width, height, frame_id, frames_n)
    t = (frame_id / frames_n)
    tphase = ((2.0 * math.pi) * t)
    
    -- Camera slowly orbits.
    cam_r = 3.0
    cam_x = (cam_r * math.cos((tphase * 0.9)))
    cam_y = (1.1 + (0.25 * math.sin((tphase * 0.6))))
    cam_z = (cam_r * math.sin((tphase * 0.9)))
    look_x = 0.0
    look_y = 0.35
    look_z = 0.0
    
    local __pytra_tuple_2 = normalize((look_x - cam_x), (look_y - cam_y), (look_z - cam_z))
    fwd_x = __pytra_tuple_2[1]
    fwd_y = __pytra_tuple_2[2]
    fwd_z = __pytra_tuple_2[3]
    local __pytra_tuple_3 = normalize(fwd_z, 0.0, (-fwd_x))
    right_x = __pytra_tuple_3[1]
    right_y = __pytra_tuple_3[2]
    right_z = __pytra_tuple_3[3]
    local __pytra_tuple_4 = normalize(((right_y * fwd_z) - (right_z * fwd_y)), ((right_z * fwd_x) - (right_x * fwd_z)), ((right_x * fwd_y) - (right_y * fwd_x)))
    up_x = __pytra_tuple_4[1]
    up_y = __pytra_tuple_4[2]
    up_z = __pytra_tuple_4[3]
    
    -- Moving glass sculpture (3 spheres) and an emissive sphere.
    s0x = (0.9 * math.cos((1.3 * tphase)))
    s0y = (0.15 + (0.35 * math.sin((1.7 * tphase))))
    s0z = (0.9 * math.sin((1.3 * tphase)))
    s1x = (1.2 * math.cos(((1.3 * tphase) + 2.094)))
    s1y = (0.1 + (0.4 * math.sin(((1.1 * tphase) + 0.8))))
    s1z = (1.2 * math.sin(((1.3 * tphase) + 2.094)))
    s2x = (1.0 * math.cos(((1.3 * tphase) + 4.188)))
    s2y = (0.2 + (0.3 * math.sin(((1.5 * tphase) + 1.9))))
    s2z = (1.0 * math.sin(((1.3 * tphase) + 4.188)))
    lr = 0.35
    lx = (2.4 * math.cos((tphase * 1.8)))
    ly = (1.8 + (0.8 * math.sin((tphase * 1.2))))
    lz = (2.4 * math.sin((tphase * 1.8)))
    
    frame = (function(__v) if type(__v) == "number" then local __n = math.max(0, math.floor(tonumber(__v) or 0)); local __out = {}; for __i = 1, __n do __out[#__out + 1] = 0 end; return __out elseif type(__v) == "table" then local __out = {}; for __i = 1, #__v do __out[#__out + 1] = __v[__i] end; return __out else return {} end end)((width * height))
    aspect = (width / height)
    fov = 1.25
    local __hoisted_cast_3 = (tonumber(height) or 0.0)
    local __hoisted_cast_4 = (tonumber(width) or 0.0)
    
    for py = 0, (height) - 1, 1 do
        row_base = (py * width)
        sy = (1.0 - ((2.0 * (py + 0.5)) / __hoisted_cast_3))
        for px = 0, (width) - 1, 1 do
            sx = ((((2.0 * (px + 0.5)) / __hoisted_cast_4) - 1.0) * aspect)
            rx = (fwd_x + (fov * ((sx * right_x) + (sy * up_x))))
            ry = (fwd_y + (fov * ((sx * right_y) + (sy * up_y))))
            rz = (fwd_z + (fov * ((sx * right_z) + (sy * up_z))))
            local __pytra_tuple_7 = normalize(rx, ry, rz)
            dx = __pytra_tuple_7[1]
            dy = __pytra_tuple_7[2]
            dz = __pytra_tuple_7[3]
            
            -- Search for the nearest hit.
            best_t = 1000000000.0
            hit_kind = 0
            r = 0.0
            g = 0.0
            b = 0.0
            
            -- Floor plane y=-1.2
            if (dy < (-1e-06)) then
                tf = (((-1.2) - cam_y) / dy)
                if ((tf > 0.0001) and (tf < best_t)) then
                    best_t = tf
                    hit_kind = 1
                end
            end
            t0 = sphere_intersect(cam_x, cam_y, cam_z, dx, dy, dz, s0x, s0y, s0z, 0.65)
            if ((t0 > 0.0) and (t0 < best_t)) then
                best_t = t0
                hit_kind = 2
            end
            t1 = sphere_intersect(cam_x, cam_y, cam_z, dx, dy, dz, s1x, s1y, s1z, 0.72)
            if ((t1 > 0.0) and (t1 < best_t)) then
                best_t = t1
                hit_kind = 3
            end
            t2 = sphere_intersect(cam_x, cam_y, cam_z, dx, dy, dz, s2x, s2y, s2z, 0.58)
            if ((t2 > 0.0) and (t2 < best_t)) then
                best_t = t2
                hit_kind = 4
            end
            if (hit_kind == 0) then
                local __pytra_tuple_8 = sky_color(dx, dy, dz, tphase)
                r = __pytra_tuple_8[1]
                g = __pytra_tuple_8[2]
                b = __pytra_tuple_8[3]
            else
                if (hit_kind == 1) then
                    hx = (cam_x + (best_t * dx))
                    hz = (cam_z + (best_t * dz))
                    cx = (math.floor(tonumber(math.floor((hx * 2.0))) or 0))
                    cz = (math.floor(tonumber(math.floor((hz * 2.0))) or 0))
                    checker = (((((cx + cz) % 2) == 0)) and (0) or (1))
                    base_r = (((checker == 0)) and (0.1) or (0.04))
                    base_g = (((checker == 0)) and (0.11) or (0.05))
                    base_b = (((checker == 0)) and (0.13) or (0.08))
                    -- Emissive sphere contribution.
                    lxv = (lx - hx)
                    lyv = (ly - (-1.2))
                    lzv = (lz - hz)
                    local __pytra_tuple_9 = normalize(lxv, lyv, lzv)
                    ldx = __pytra_tuple_9[1]
                    ldy = __pytra_tuple_9[2]
                    ldz = __pytra_tuple_9[3]
                    ndotl = math.max(ldy, 0.0)
                    ldist2 = (((lxv * lxv) + (lyv * lyv)) + (lzv * lzv))
                    glow = (8.0 / (1.0 + ldist2))
                    r = ((base_r + (0.8 * glow)) + (0.2 * ndotl))
                    g = ((base_g + (0.5 * glow)) + (0.18 * ndotl))
                    b = ((base_b + (1.0 * glow)) + (0.24 * ndotl))
                else
                    cx = 0.0
                    cy = 0.0
                    cz = 0.0
                    rad = 1.0
                    if (hit_kind == 2) then
                        cx = s0x
                        cy = s0y
                        cz = s0z
                        rad = 0.65
                    else
                        if (hit_kind == 3) then
                            cx = s1x
                            cy = s1y
                            cz = s1z
                            rad = 0.72
                        else
                            cx = s2x
                            cy = s2y
                            cz = s2z
                            rad = 0.58
                        end
                    end
                    hx = (cam_x + (best_t * dx))
                    hy = (cam_y + (best_t * dy))
                    hz = (cam_z + (best_t * dz))
                    local __pytra_tuple_10 = normalize(((hx - cx) / rad), ((hy - cy) / rad), ((hz - cz) / rad))
                    nx = __pytra_tuple_10[1]
                    ny = __pytra_tuple_10[2]
                    nz = __pytra_tuple_10[3]
                    
                    -- Simple glass shading (reflection + refraction + light highlights).
                    local __pytra_tuple_11 = reflect(dx, dy, dz, nx, ny, nz)
                    rdx = __pytra_tuple_11[1]
                    rdy = __pytra_tuple_11[2]
                    rdz = __pytra_tuple_11[3]
                    local __pytra_tuple_12 = refract(dx, dy, dz, nx, ny, nz, (1.0 / 1.45))
                    tdx = __pytra_tuple_12[1]
                    tdy = __pytra_tuple_12[2]
                    tdz = __pytra_tuple_12[3]
                    local __pytra_tuple_13 = sky_color(rdx, rdy, rdz, tphase)
                    sr = __pytra_tuple_13[1]
                    sg = __pytra_tuple_13[2]
                    sb = __pytra_tuple_13[3]
                    local __pytra_tuple_14 = sky_color(tdx, tdy, tdz, (tphase + 0.8))
                    tr = __pytra_tuple_14[1]
                    tg = __pytra_tuple_14[2]
                    tb = __pytra_tuple_14[3]
                    cosi = math.max((-(((dx * nx) + (dy * ny)) + (dz * nz))), 0.0)
                    fr = schlick(cosi, 0.04)
                    r = ((tr * (1.0 - fr)) + (sr * fr))
                    g = ((tg * (1.0 - fr)) + (sg * fr))
                    b = ((tb * (1.0 - fr)) + (sb * fr))
                    
                    lxv = (lx - hx)
                    lyv = (ly - hy)
                    lzv = (lz - hz)
                    local __pytra_tuple_15 = normalize(lxv, lyv, lzv)
                    ldx = __pytra_tuple_15[1]
                    ldy = __pytra_tuple_15[2]
                    ldz = __pytra_tuple_15[3]
                    ndotl = math.max((((nx * ldx) + (ny * ldy)) + (nz * ldz)), 0.0)
                    local __pytra_tuple_16 = normalize((ldx - dx), (ldy - dy), (ldz - dz))
                    hvx = __pytra_tuple_16[1]
                    hvy = __pytra_tuple_16[2]
                    hvz = __pytra_tuple_16[3]
                    ndoth = math.max((((nx * hvx) + (ny * hvy)) + (nz * hvz)), 0.0)
                    spec = (ndoth * ndoth)
                    spec = (spec * spec)
                    spec = (spec * spec)
                    spec = (spec * spec)
                    glow = (10.0 / (((1.0 + (lxv * lxv)) + (lyv * lyv)) + (lzv * lzv)))
                    r = r + (((0.2 * ndotl) + (0.8 * spec)) + (0.45 * glow))
                    g = g + (((0.18 * ndotl) + (0.6 * spec)) + (0.35 * glow))
                    b = b + (((0.26 * ndotl) + (1.0 * spec)) + (0.65 * glow))
                    
                    -- Slight tint variation per sphere.
                    if (hit_kind == 2) then
                        r = r * 0.95
                        g = g * 1.05
                        b = b * 1.1
                    else
                        if (hit_kind == 3) then
                            r = r * 1.08
                            g = g * 0.98
                            b = b * 1.04
                        else
                            r = r * 1.02
                            g = g * 1.1
                            b = b * 0.95
                        end
                    end
                end
            end
            -- Slightly stronger tone mapping.
            r = math.sqrt(clamp01(r))
            g = math.sqrt(clamp01(g))
            b = math.sqrt(clamp01(b))
            frame[((((row_base + px)) < 0) and (#(frame) + ((row_base + px)) + 1) or (((row_base + px)) + 1))] = quantize_332(r, g, b)
            ::__pytra_continue_6::
        end
        ::__pytra_continue_5::
    end
    return (function(__v) if type(__v) == "number" then local __n = math.max(0, math.floor(tonumber(__v) or 0)); local __out = {}; for __i = 1, __n do __out[#__out + 1] = 0 end; return __out elseif type(__v) == "table" then local __out = {}; for __i = 1, #__v do __out[#__out + 1] = __v[__i] end; return __out elseif type(__v) == "string" then local __out = {}; for __i = 1, #__v do __out[#__out + 1] = string.byte(__v, __i) end; return __out else return {} end end)(frame)
end

function run_16_glass_sculpture_chaos()
    width = 320
    height = 240
    frames_n = 72
    out_path = "sample/out/16_glass_sculpture_chaos.gif"
    
    start = perf_counter()
    local frames = {  }
    for i = 0, (frames_n) - 1, 1 do
        table.insert(frames, render_frame(width, height, i, frames_n))
        ::__pytra_continue_17::
    end
    save_gif(out_path, width, height, frames, palette_332())
    elapsed = (perf_counter() - start)
    __pytra_print("output:", out_path)
    __pytra_print("frames:", frames_n)
    __pytra_print("elapsed_sec:", elapsed)
end


run_16_glass_sculpture_chaos()
