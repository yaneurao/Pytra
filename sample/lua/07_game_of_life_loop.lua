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

-- 07: Sample that outputs Game of Life evolution as a GIF.

function next_state(grid, w, h)
    local nxt = {  }
    for y = 0, (h) - 1, 1 do
        local row = {  }
        for x = 0, (w) - 1, 1 do
            cnt = 0
            for dy = (-1), (2) - 1, 1 do
                for dx = (-1), (2) - 1, 1 do
                    if ((dx ~= 0) or (dy ~= 0)) then
                        nx = (((x + dx) + w) % w)
                        ny = (((y + dy) + h) % h)
                        cnt = cnt + grid[(((ny) < 0) and (#(grid) + (ny) + 1) or ((ny) + 1))][(((nx) < 0) and (#(grid[(((ny) < 0) and (#(grid) + (ny) + 1) or ((ny) + 1))]) + (nx) + 1) or ((nx) + 1))]
                    end
                    ::__pytra_continue_4::
                end
                ::__pytra_continue_3::
            end
            alive = grid[(((y) < 0) and (#(grid) + (y) + 1) or ((y) + 1))][(((x) < 0) and (#(grid[(((y) < 0) and (#(grid) + (y) + 1) or ((y) + 1))]) + (x) + 1) or ((x) + 1))]
            if ((alive == 1) and ((cnt == 2) or (cnt == 3))) then
                table.insert(row, 1)
            else
                if ((alive == 0) and (cnt == 3)) then
                    table.insert(row, 1)
                else
                    table.insert(row, 0)
                end
            end
            ::__pytra_continue_2::
        end
        table.insert(nxt, row)
        ::__pytra_continue_1::
    end
    return nxt
end

function render(grid, w, h, cell)
    width = (w * cell)
    height = (h * cell)
    frame = (function(__v) if type(__v) == "number" then local __n = math.max(0, math.floor(tonumber(__v) or 0)); local __out = {}; for __i = 1, __n do __out[#__out + 1] = 0 end; return __out elseif type(__v) == "table" then local __out = {}; for __i = 1, #__v do __out[#__out + 1] = __v[__i] end; return __out else return {} end end)((width * height))
    for y = 0, (h) - 1, 1 do
        for x = 0, (w) - 1, 1 do
            v = ((grid[(((y) < 0) and (#(grid) + (y) + 1) or ((y) + 1))][(((x) < 0) and (#(grid[(((y) < 0) and (#(grid) + (y) + 1) or ((y) + 1))]) + (x) + 1) or ((x) + 1))]) and (255) or (0))
            for yy = 0, (cell) - 1, 1 do
                base = ((((y * cell) + yy) * width) + (x * cell))
                for xx = 0, (cell) - 1, 1 do
                    frame[((((base + xx)) < 0) and (#(frame) + ((base + xx)) + 1) or (((base + xx)) + 1))] = v
                    ::__pytra_continue_8::
                end
                ::__pytra_continue_7::
            end
            ::__pytra_continue_6::
        end
        ::__pytra_continue_5::
    end
    return (function(__v) if type(__v) == "number" then local __n = math.max(0, math.floor(tonumber(__v) or 0)); local __out = {}; for __i = 1, __n do __out[#__out + 1] = 0 end; return __out elseif type(__v) == "table" then local __out = {}; for __i = 1, #__v do __out[#__out + 1] = __v[__i] end; return __out elseif type(__v) == "string" then local __out = {}; for __i = 1, #__v do __out[#__out + 1] = string.byte(__v, __i) end; return __out else return {} end end)(frame)
end

function run_07_game_of_life_loop()
    w = 144
    h = 108
    cell = 4
    steps = 105
    out_path = "sample/out/07_game_of_life_loop.gif"
    
    start = perf_counter()
    local grid = (function() local __lc_out_10 = {}; for __lc_i_9 = 0, (h) - 1, 1 do table.insert(__lc_out_10, __pytra_repeat_seq({ 0 }, w)) end; return __lc_out_10 end)()
    
    -- Lay down sparse noise so the whole field is less likely to stabilize too early.
    -- Avoid large integer literals so all transpilers handle the expression consistently.
    for y = 0, (h) - 1, 1 do
        for x = 0, (w) - 1, 1 do
            noise = (((((x * 37) + (y * 73)) + ((x * y) % 19)) + ((x + y) % 11)) % 97)
            if (noise < 3) then
                grid[(((y) < 0) and (#(grid) + (y) + 1) or ((y) + 1))][(((x) < 0) and (#(grid[(((y) < 0) and (#(grid) + (y) + 1) or ((y) + 1))]) + (x) + 1) or ((x) + 1))] = 1
            end
            ::__pytra_continue_12::
        end
        ::__pytra_continue_11::
    end
    -- Place multiple well-known long-lived patterns.
    glider = { { 0, 1, 0 }, { 0, 0, 1 }, { 1, 1, 1 } }
    r_pentomino = { { 0, 1, 1 }, { 1, 1, 0 }, { 0, 1, 0 } }
    lwss = { { 0, 1, 1, 1, 1 }, { 1, 0, 0, 0, 1 }, { 0, 0, 0, 0, 1 }, { 1, 0, 0, 1, 0 } }
    
    for gy = 8, ((h - 8)) - 1, 18 do
        for gx = 8, ((w - 8)) - 1, 22 do
            kind = (((gx * 7) + (gy * 11)) % 3)
            if (kind == 0) then
                ph = #(glider)
                for py = 0, (ph) - 1, 1 do
                    pw = #(glider[(((py) < 0) and (#(glider) + (py) + 1) or ((py) + 1))])
                    for px = 0, (pw) - 1, 1 do
                        if (glider[(((py) < 0) and (#(glider) + (py) + 1) or ((py) + 1))][(((px) < 0) and (#(glider[(((py) < 0) and (#(glider) + (py) + 1) or ((py) + 1))]) + (px) + 1) or ((px) + 1))] == 1) then
                            grid[(((((gy + py) % h)) < 0) and (#(grid) + (((gy + py) % h)) + 1) or ((((gy + py) % h)) + 1))][(((((gx + px) % w)) < 0) and (#(grid[(((((gy + py) % h)) < 0) and (#(grid) + (((gy + py) % h)) + 1) or ((((gy + py) % h)) + 1))]) + (((gx + px) % w)) + 1) or ((((gx + px) % w)) + 1))] = 1
                        end
                        ::__pytra_continue_16::
                    end
                    ::__pytra_continue_15::
                end
            else
                if (kind == 1) then
                    ph = #(r_pentomino)
                    for py = 0, (ph) - 1, 1 do
                        pw = #(r_pentomino[(((py) < 0) and (#(r_pentomino) + (py) + 1) or ((py) + 1))])
                        for px = 0, (pw) - 1, 1 do
                            if (r_pentomino[(((py) < 0) and (#(r_pentomino) + (py) + 1) or ((py) + 1))][(((px) < 0) and (#(r_pentomino[(((py) < 0) and (#(r_pentomino) + (py) + 1) or ((py) + 1))]) + (px) + 1) or ((px) + 1))] == 1) then
                                grid[(((((gy + py) % h)) < 0) and (#(grid) + (((gy + py) % h)) + 1) or ((((gy + py) % h)) + 1))][(((((gx + px) % w)) < 0) and (#(grid[(((((gy + py) % h)) < 0) and (#(grid) + (((gy + py) % h)) + 1) or ((((gy + py) % h)) + 1))]) + (((gx + px) % w)) + 1) or ((((gx + px) % w)) + 1))] = 1
                            end
                            ::__pytra_continue_18::
                        end
                        ::__pytra_continue_17::
                    end
                else
                    ph = #(lwss)
                    for py = 0, (ph) - 1, 1 do
                        pw = #(lwss[(((py) < 0) and (#(lwss) + (py) + 1) or ((py) + 1))])
                        for px = 0, (pw) - 1, 1 do
                            if (lwss[(((py) < 0) and (#(lwss) + (py) + 1) or ((py) + 1))][(((px) < 0) and (#(lwss[(((py) < 0) and (#(lwss) + (py) + 1) or ((py) + 1))]) + (px) + 1) or ((px) + 1))] == 1) then
                                grid[(((((gy + py) % h)) < 0) and (#(grid) + (((gy + py) % h)) + 1) or ((((gy + py) % h)) + 1))][(((((gx + px) % w)) < 0) and (#(grid[(((((gy + py) % h)) < 0) and (#(grid) + (((gy + py) % h)) + 1) or ((((gy + py) % h)) + 1))]) + (((gx + px) % w)) + 1) or ((((gx + px) % w)) + 1))] = 1
                            end
                            ::__pytra_continue_20::
                        end
                        ::__pytra_continue_19::
                    end
                end
            end
            ::__pytra_continue_14::
        end
        ::__pytra_continue_13::
    end
    local frames = {  }
    for _ = 0, (steps) - 1, 1 do
        table.insert(frames, render(grid, w, h, cell))
        grid = next_state(grid, w, h)
        ::__pytra_continue_21::
    end
    save_gif(out_path, (w * cell), (h * cell), frames, grayscale_palette())
    elapsed = (perf_counter() - start)
    __pytra_print("output:", out_path)
    __pytra_print("frames:", steps)
    __pytra_print("elapsed_sec:", elapsed)
end


run_07_game_of_life_loop()
