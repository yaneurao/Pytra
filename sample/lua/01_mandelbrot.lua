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

local perf_counter = __pytra_perf_counter
local png = __pytra_png_module()

-- 01: Sample that outputs the Mandelbrot set as a PNG image.
-- Syntax is kept straightforward with future transpilation in mind.

function escape_count(cx, cy, max_iter)
    local x = 0.0
    local y = 0.0
    for i = 0, (max_iter) - 1, 1 do
        local x2 = (x * x)
        local y2 = (y * y)
        if ((x2 + y2) > 4.0) then
            return i
        end
        y = (((2.0 * x) * y) + cy)
        x = ((x2 - y2) + cx)
        ::__pytra_continue_1::
    end
    return max_iter
end

function color_map(iter_count, max_iter)
    if (iter_count >= max_iter) then
        return { 0, 0, 0 }
    end
    local t = (iter_count / max_iter)
    local r = (math.floor(tonumber((255.0 * (t * t))) or 0))
    local g = (math.floor(tonumber((255.0 * t)) or 0))
    local b = (math.floor(tonumber((255.0 * (1.0 - t))) or 0))
    return { r, g, b }
end

function render_mandelbrot(width, height, max_iter, x_min, x_max, y_min, y_max)
    local pixels = {}
    local __hoisted_cast_1 = (tonumber((height - 1)) or 0.0)
    local __hoisted_cast_2 = (tonumber((width - 1)) or 0.0)
    local __hoisted_cast_3 = (tonumber(max_iter) or 0.0)
    
    for y = 0, (height) - 1, 1 do
        local py = (y_min + ((y_max - y_min) * (y / __hoisted_cast_1)))
        
        for x = 0, (width) - 1, 1 do
            local px = (x_min + ((x_max - x_min) * (x / __hoisted_cast_2)))
            local it = escape_count(px, py, max_iter)
            local r = nil
            local g = nil
            local b = nil
            if (it >= max_iter) then
                r = 0
                g = 0
                b = 0
            else
                local t = (it / __hoisted_cast_3)
                r = (math.floor(tonumber((255.0 * (t * t))) or 0))
                g = (math.floor(tonumber((255.0 * t)) or 0))
                b = (math.floor(tonumber((255.0 * (1.0 - t))) or 0))
            end
            table.insert(pixels, r)
            table.insert(pixels, g)
            table.insert(pixels, b)
            ::__pytra_continue_3::
        end
        ::__pytra_continue_2::
    end
    return pixels
end

function run_mandelbrot()
    local width = 1600
    local height = 1200
    local max_iter = 1000
    local out_path = "sample/out/01_mandelbrot.png"
    
    local start = perf_counter()
    
    local pixels = render_mandelbrot(width, height, max_iter, (-2.2), 1.0, (-1.2), 1.2)
    png.write_rgb_png(out_path, width, height, pixels)
    
    local elapsed = (perf_counter() - start)
    __pytra_print("output:", out_path)
    __pytra_print("size:", width, "x", height)
    __pytra_print("max_iter:", max_iter)
    __pytra_print("elapsed_sec:", elapsed)
end


run_mandelbrot()
