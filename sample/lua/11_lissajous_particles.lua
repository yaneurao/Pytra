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

-- 11: Sample that outputs Lissajous-motion particles as a GIF.

function color_palette()
    p = {}
    for i = 0, (256) - 1, 1 do
        r = i
        g = ((i * 3) % 256)
        b = (255 - i)
        table.insert(p, r)
        table.insert(p, g)
        table.insert(p, b)
        ::__pytra_continue_1::
    end
    return (function(__v) if type(__v) == "number" then local __n = math.max(0, math.floor(tonumber(__v) or 0)); local __out = {}; for __i = 1, __n do __out[#__out + 1] = 0 end; return __out elseif type(__v) == "table" then local __out = {}; for __i = 1, #__v do __out[#__out + 1] = __v[__i] end; return __out elseif type(__v) == "string" then local __out = {}; for __i = 1, #__v do __out[#__out + 1] = string.byte(__v, __i) end; return __out else return {} end end)(p)
end

function run_11_lissajous_particles()
    w = 320
    h = 240
    frames_n = 360
    particles = 48
    out_path = "sample/out/11_lissajous_particles.gif"
    
    start = perf_counter()
    local frames = {  }
    
    for t = 0, (frames_n) - 1, 1 do
        frame = (function(__v) if type(__v) == "number" then local __n = math.max(0, math.floor(tonumber(__v) or 0)); local __out = {}; for __i = 1, __n do __out[#__out + 1] = 0 end; return __out elseif type(__v) == "table" then local __out = {}; for __i = 1, #__v do __out[#__out + 1] = __v[__i] end; return __out else return {} end end)((w * h))
        local __hoisted_cast_1 = (tonumber(t) or 0.0)
        
        for p = 0, (particles) - 1, 1 do
            phase = (p * 0.261799)
            x = (math.floor(tonumber(((w * 0.5) + ((w * 0.38) * math.sin(((0.11 * __hoisted_cast_1) + (phase * 2.0)))))) or 0))
            y = (math.floor(tonumber(((h * 0.5) + ((h * 0.38) * math.sin(((0.17 * __hoisted_cast_1) + (phase * 3.0)))))) or 0))
            color = (30 + ((p * 9) % 220))
            
            for dy = (-2), (3) - 1, 1 do
                for dx = (-2), (3) - 1, 1 do
                    xx = (x + dx)
                    yy = (y + dy)
                    if ((xx >= 0) and (xx < w) and (yy >= 0) and (yy < h)) then
                        d2 = ((dx * dx) + (dy * dy))
                        if (d2 <= 4) then
                            idx = ((yy * w) + xx)
                            v = (color - (d2 * 20))
                            v = math.max(0, v)
                            if (v > frame[(((idx) < 0) and (#(frame) + (idx) + 1) or ((idx) + 1))]) then
                                frame[(((idx) < 0) and (#(frame) + (idx) + 1) or ((idx) + 1))] = v
                            end
                        end
                    end
                    ::__pytra_continue_5::
                end
                ::__pytra_continue_4::
            end
            ::__pytra_continue_3::
        end
        table.insert(frames, (function(__v) if type(__v) == "number" then local __n = math.max(0, math.floor(tonumber(__v) or 0)); local __out = {}; for __i = 1, __n do __out[#__out + 1] = 0 end; return __out elseif type(__v) == "table" then local __out = {}; for __i = 1, #__v do __out[#__out + 1] = __v[__i] end; return __out elseif type(__v) == "string" then local __out = {}; for __i = 1, #__v do __out[#__out + 1] = string.byte(__v, __i) end; return __out else return {} end end)(frame))
        ::__pytra_continue_2::
    end
    save_gif(out_path, w, h, frames, color_palette())
    elapsed = (perf_counter() - start)
    __pytra_print("output:", out_path)
    __pytra_print("frames:", frames_n)
    __pytra_print("elapsed_sec:", elapsed)
end


run_11_lissajous_particles()
