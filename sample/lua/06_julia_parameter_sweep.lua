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

-- 06: Sample that sweeps Julia-set parameters and outputs a GIF.

function julia_palette()
    -- Keep index 0 black for points inside the set; build a high-saturation gradient for the rest.
    palette = (function(__v) if type(__v) == "number" then local __n = math.max(0, math.floor(tonumber(__v) or 0)); local __out = {}; for __i = 1, __n do __out[#__out + 1] = 0 end; return __out elseif type(__v) == "table" then local __out = {}; for __i = 1, #__v do __out[#__out + 1] = __v[__i] end; return __out else return {} end end)((256 * 3))
    palette[1] = 0
    palette[2] = 0
    palette[3] = 0
    for i = 1, (256) - 1, 1 do
        t = ((i - 1) / 254.0)
        r = (math.floor(tonumber((255.0 * ((((9.0 * (1.0 - t)) * t) * t) * t))) or 0))
        g = (math.floor(tonumber((255.0 * ((((15.0 * (1.0 - t)) * (1.0 - t)) * t) * t))) or 0))
        b = (math.floor(tonumber((255.0 * ((((8.5 * (1.0 - t)) * (1.0 - t)) * (1.0 - t)) * t))) or 0))
        palette[(((((i * 3) + 0)) < 0) and (#(palette) + (((i * 3) + 0)) + 1) or ((((i * 3) + 0)) + 1))] = r
        palette[(((((i * 3) + 1)) < 0) and (#(palette) + (((i * 3) + 1)) + 1) or ((((i * 3) + 1)) + 1))] = g
        palette[(((((i * 3) + 2)) < 0) and (#(palette) + (((i * 3) + 2)) + 1) or ((((i * 3) + 2)) + 1))] = b
        ::__pytra_continue_1::
    end
    return (function(__v) if type(__v) == "number" then local __n = math.max(0, math.floor(tonumber(__v) or 0)); local __out = {}; for __i = 1, __n do __out[#__out + 1] = 0 end; return __out elseif type(__v) == "table" then local __out = {}; for __i = 1, #__v do __out[#__out + 1] = __v[__i] end; return __out elseif type(__v) == "string" then local __out = {}; for __i = 1, #__v do __out[#__out + 1] = string.byte(__v, __i) end; return __out else return {} end end)(palette)
end

function render_frame(width, height, cr, ci, max_iter, phase)
    frame = (function(__v) if type(__v) == "number" then local __n = math.max(0, math.floor(tonumber(__v) or 0)); local __out = {}; for __i = 1, __n do __out[#__out + 1] = 0 end; return __out elseif type(__v) == "table" then local __out = {}; for __i = 1, #__v do __out[#__out + 1] = __v[__i] end; return __out else return {} end end)((width * height))
    local __hoisted_cast_1 = (tonumber((height - 1)) or 0.0)
    local __hoisted_cast_2 = (tonumber((width - 1)) or 0.0)
    for y = 0, (height) - 1, 1 do
        row_base = (y * width)
        zy0 = ((-1.2) + (2.4 * (y / __hoisted_cast_1)))
        for x = 0, (width) - 1, 1 do
            zx = ((-1.8) + (3.6 * (x / __hoisted_cast_2)))
            zy = zy0
            i = 0
            while (i < max_iter) do
                zx2 = (zx * zx)
                zy2 = (zy * zy)
                if ((zx2 + zy2) > 4.0) then
                    break
                end
                zy = (((2.0 * zx) * zy) + ci)
                zx = ((zx2 - zy2) + cr)
                i = i + 1
                ::__pytra_continue_4::
            end
            if (i >= max_iter) then
                frame[((((row_base + x)) < 0) and (#(frame) + ((row_base + x)) + 1) or (((row_base + x)) + 1))] = 0
            else
                -- Add a small frame phase so colors flow smoothly.
                color_index = (1 + ((((i * 224) // max_iter) + phase) % 255))
                frame[((((row_base + x)) < 0) and (#(frame) + ((row_base + x)) + 1) or (((row_base + x)) + 1))] = color_index
            end
            ::__pytra_continue_3::
        end
        ::__pytra_continue_2::
    end
    return (function(__v) if type(__v) == "number" then local __n = math.max(0, math.floor(tonumber(__v) or 0)); local __out = {}; for __i = 1, __n do __out[#__out + 1] = 0 end; return __out elseif type(__v) == "table" then local __out = {}; for __i = 1, #__v do __out[#__out + 1] = __v[__i] end; return __out elseif type(__v) == "string" then local __out = {}; for __i = 1, #__v do __out[#__out + 1] = string.byte(__v, __i) end; return __out else return {} end end)(frame)
end

function run_06_julia_parameter_sweep()
    width = 320
    height = 240
    frames_n = 72
    max_iter = 180
    out_path = "sample/out/06_julia_parameter_sweep.gif"
    
    start = perf_counter()
    local frames = {  }
    -- Orbit an ellipse around a known visually good region to reduce flat blown highlights.
    center_cr = (-0.745)
    center_ci = 0.186
    radius_cr = 0.12
    radius_ci = 0.1
    -- Add start and phase offsets so GitHub thumbnails do not appear too dark.
    -- Tune it to start in a red-leaning color range.
    start_offset = 20
    phase_offset = 180
    local __hoisted_cast_3 = (tonumber(frames_n) or 0.0)
    for i = 0, (frames_n) - 1, 1 do
        t = (((i + start_offset) % frames_n) / __hoisted_cast_3)
        angle = ((2.0 * math.pi) * t)
        cr = (center_cr + (radius_cr * math.cos(angle)))
        ci = (center_ci + (radius_ci * math.sin(angle)))
        phase = ((phase_offset + (i * 5)) % 255)
        table.insert(frames, render_frame(width, height, cr, ci, max_iter, phase))
        ::__pytra_continue_5::
    end
    save_gif(out_path, width, height, frames, julia_palette())
    elapsed = (perf_counter() - start)
    __pytra_print("output:", out_path)
    __pytra_print("frames:", frames_n)
    __pytra_print("elapsed_sec:", elapsed)
end


run_06_julia_parameter_sweep()
