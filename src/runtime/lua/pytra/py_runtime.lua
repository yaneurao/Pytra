-- Auto-generated canonical Lua runtime for Pytra native backend.
-- Source of truth: src/runtime/lua/pytra/py_runtime.lua

function __pytra_print(...)
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

function __pytra_repeat_seq(a, b)
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

function __pytra_truthy(v)
    if v == nil then return false end
    local t = type(v)
    if t == "boolean" then return v end
    if t == "number" then return v ~= 0 end
    if t == "string" then return #v ~= 0 end
    if t == "table" then return next(v) ~= nil end
    return true
end

function __pytra_contains(container, value)
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

function __pytra_str_isdigit(s)
    if type(s) ~= "string" or #s == 0 then return false end
    for i = 1, #s do
        local b = string.byte(s, i)
        if b < 48 or b > 57 then return false end
    end
    return true
end

function __pytra_str_isalpha(s)
    if type(s) ~= "string" or #s == 0 then return false end
    for i = 1, #s do
        local b = string.byte(s, i)
        local is_upper = (b >= 65 and b <= 90)
        local is_lower = (b >= 97 and b <= 122)
        if not (is_upper or is_lower) then return false end
    end
    return true
end

function __pytra_str_isalnum(s)
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

function __pytra_perf_counter()
    return os.clock()
end

function __pytra_math_module()
    local m = {}
    for k, v in pairs(math) do
        m[k] = v
    end
    if m.fabs == nil then m.fabs = math.abs end
    if m.log10 == nil then m.log10 = function(x) return math.log(x, 10) end end
    if m.pow == nil then m.pow = function(a, b) return (a ^ b) end end
    return m
end

function __pytra_path_basename(path)
    local name = string.match(path, "([^/]+)$")
    if name == nil or name == "" then return path end
    return name
end

function __pytra_path_parent_text(path)
    local parent = string.match(path, "^(.*)/[^/]*$")
    if parent == nil or parent == "" then return "." end
    return parent
end

function __pytra_path_stem(path)
    local name = __pytra_path_basename(path)
    local stem = string.match(name, "^(.*)%.")
    if stem == nil or stem == "" then return name end
    return stem
end

local __pytra_path_mt = {}
__pytra_path_mt.__index = __pytra_path_mt

function __pytra_path_join(left, right)
    if left == "" or left == "." then return right end
    if string.sub(left, -1) == "/" then return left .. right end
    return left .. "/" .. right
end

function __pytra_path_new(path)
    local text = tostring(path)
    local obj = { path = text }
    setmetatable(obj, __pytra_path_mt)
    obj.name = __pytra_path_basename(text)
    obj.stem = __pytra_path_stem(text)
    local parent_text = __pytra_path_parent_text(text)
    if parent_text ~= text then
        obj.parent = setmetatable({ path = parent_text }, __pytra_path_mt)
        obj.parent.name = __pytra_path_basename(parent_text)
        obj.parent.stem = __pytra_path_stem(parent_text)
        obj.parent.parent = nil
    else
        obj.parent = nil
    end
    return obj
end

function __pytra_path_mt.__div(lhs, rhs)
    local left = lhs.path
    local right = tostring(rhs)
    if type(rhs) == "table" and rhs.path ~= nil then
        right = rhs.path
    end
    return __pytra_path_new(__pytra_path_join(left, right))
end

function __pytra_path_mt:exists()
    local f = io.open(self.path, "rb")
    if f ~= nil then
        f:close()
        return true
    end
    local ok = os.execute('test -e "' .. self.path .. '"')
    if type(ok) == "boolean" then return ok end
    if type(ok) == "number" then return ok == 0 end
    return false
end

function __pytra_path_mt:mkdir()
    os.execute('mkdir -p "' .. self.path .. '"')
end

function __pytra_path_mt:write_text(text)
    local f = assert(io.open(self.path, "wb"))
    f:write(tostring(text))
    f:close()
end

function __pytra_path_mt:read_text()
    local f = assert(io.open(self.path, "rb"))
    local data = f:read("*a")
    f:close()
    return data
end

function __pytra_u16le(n)
    local v = math.floor(tonumber(n) or 0) & 0xFFFF
    return string.char(v & 0xFF, (v >> 8) & 0xFF)
end

function __pytra_to_byte_table(data)
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

function __pytra_bytes_from_table(data)
    local parts = {}
    for i = 1, #data do
        parts[#parts + 1] = string.char(data[i])
    end
    return table.concat(parts)
end

function __pytra_gif_lzw_encode(data, min_code_size)
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

function __pytra_grayscale_palette()
    local out = {}
    for i = 0, 255 do
        out[#out + 1] = i
        out[#out + 1] = i
        out[#out + 1] = i
    end
    return out
end

function __pytra_save_gif(path, width, height, frames, palette, delay_cs, loop)
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

function __pytra_gif_module()
    return {
        grayscale_palette = __pytra_grayscale_palette,
        save_gif = function(...)
            local path, width, height, frames, palette, delay_cs, loop = ...
            return __pytra_save_gif(path, width, height, frames, palette, delay_cs, loop)
        end,
    }
end

function __pytra_u32be(n)
    local v = math.floor(tonumber(n) or 0) & 0xFFFFFFFF
    return string.char((v >> 24) & 0xFF, (v >> 16) & 0xFF, (v >> 8) & 0xFF, v & 0xFF)
end

local __pytra_crc_table = nil
function __pytra_init_crc_table()
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

function __pytra_png_crc32(data)
    __pytra_init_crc_table()
    local c = 0xFFFFFFFF
    for i = 1, #data do
        local b = string.byte(data, i)
        local idx = (c ~ b) & 0xFF
        c = ((c >> 8) ~ __pytra_crc_table[idx]) & 0xFFFFFFFF
    end
    return (~c) & 0xFFFFFFFF
end

function __pytra_png_adler32(data)
    local s1 = 1
    local s2 = 0
    for i = 1, #data do
        s1 = (s1 + string.byte(data, i)) % 65521
        s2 = (s2 + s1) % 65521
    end
    return ((s2 << 16) | s1) & 0xFFFFFFFF
end

function __pytra_png_chunk(kind, data)
    local payload = data or ""
    local crc = __pytra_png_crc32(kind .. payload)
    return __pytra_u32be(#payload) .. kind .. payload .. __pytra_u32be(crc)
end

function __pytra_zlib_store(raw)
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

function __pytra_write_rgb_png(path, width, height, pixels)
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

function __pytra_png_module()
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

function __pytra_isinstance(obj, class_tbl)
    if type(obj) ~= "table" then
        return false
    end
    local mt = getmetatable(obj)
    while mt do
        if mt == class_tbl then
            return true
        end
        local parent = getmetatable(mt)
        if type(parent) == "table" and type(parent.__index) == "table" then
            mt = parent.__index
        else
            mt = nil
        end
    end
    return false
end
