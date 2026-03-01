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
local perf_counter = __pytra_perf_counter
local grayscale_palette = __pytra_grayscale_palette
local save_gif = __pytra_save_gif

-- 12: Sample that outputs intermediate states of bubble sort as a GIF.

function render(values, w, h)
    frame = (function(__v) if type(__v) == "number" then local __n = math.max(0, math.floor(tonumber(__v) or 0)); local __out = {}; for __i = 1, __n do __out[#__out + 1] = 0 end; return __out elseif type(__v) == "table" then local __out = {}; for __i = 1, #__v do __out[#__out + 1] = __v[__i] end; return __out else return {} end end)((w * h))
    n = #(values)
    bar_w = (w / n)
    local __hoisted_cast_1 = (tonumber(n) or 0.0)
    local __hoisted_cast_2 = (tonumber(h) or 0.0)
    for i = 0, (n) - 1, 1 do
        x0 = (math.floor(tonumber((i * bar_w)) or 0))
        x1 = (math.floor(tonumber(((i + 1) * bar_w)) or 0))
        if (x1 <= x0) then
            x1 = (x0 + 1)
        end
        bh = (math.floor(tonumber(((values[(((i) < 0) and (#(values) + (i) + 1) or ((i) + 1))] / __hoisted_cast_1) * __hoisted_cast_2)) or 0))
        y = (h - bh)
        for y = y, (h) - 1, 1 do
            for x = x0, (x1) - 1, 1 do
                frame[(((((y * w) + x)) < 0) and (#(frame) + (((y * w) + x)) + 1) or ((((y * w) + x)) + 1))] = 255
                ::__pytra_continue_3::
            end
            ::__pytra_continue_2::
        end
        ::__pytra_continue_1::
    end
    return (function(__v) if type(__v) == "number" then local __n = math.max(0, math.floor(tonumber(__v) or 0)); local __out = {}; for __i = 1, __n do __out[#__out + 1] = 0 end; return __out elseif type(__v) == "table" then local __out = {}; for __i = 1, #__v do __out[#__out + 1] = __v[__i] end; return __out elseif type(__v) == "string" then local __out = {}; for __i = 1, #__v do __out[#__out + 1] = string.byte(__v, __i) end; return __out else return {} end end)(frame)
end

function run_12_sort_visualizer()
    w = 320
    h = 180
    n = 124
    out_path = "sample/out/12_sort_visualizer.gif"
    
    start = perf_counter()
    local values = {  }
    for i = 0, (n) - 1, 1 do
        table.insert(values, (((i * 37) + 19) % n))
        ::__pytra_continue_4::
    end
    local frames = { render(values, w, h) }
    frame_stride = 16
    
    op = 0
    for i = 0, (n) - 1, 1 do
        swapped = false
        for j = 0, (((n - i) - 1)) - 1, 1 do
            if (values[(((j) < 0) and (#(values) + (j) + 1) or ((j) + 1))] > values[((((j + 1)) < 0) and (#(values) + ((j + 1)) + 1) or (((j + 1)) + 1))]) then
                local __pytra_tuple_7 = { values[((((j + 1)) < 0) and (#(values) + ((j + 1)) + 1) or (((j + 1)) + 1))], values[(((j) < 0) and (#(values) + (j) + 1) or ((j) + 1))] }
                values[(((j) < 0) and (#(values) + (j) + 1) or ((j) + 1))] = __pytra_tuple_7[1]
                values[((((j + 1)) < 0) and (#(values) + ((j + 1)) + 1) or (((j + 1)) + 1))] = __pytra_tuple_7[2]
                swapped = true
            end
            if ((op % frame_stride) == 0) then
                table.insert(frames, render(values, w, h))
            end
            op = op + 1
            ::__pytra_continue_6::
        end
        if (not swapped) then
            break
        end
        ::__pytra_continue_5::
    end
    save_gif(out_path, w, h, frames, grayscale_palette())
    elapsed = (perf_counter() - start)
    __pytra_print("output:", out_path)
    __pytra_print("frames:", #(frames))
    __pytra_print("elapsed_sec:", elapsed)
end


run_12_sort_visualizer()
