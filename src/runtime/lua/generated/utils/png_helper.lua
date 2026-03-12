-- AUTO-GENERATED FILE. DO NOT EDIT.
-- source: src/pytra/utils/png.py
-- generated-by: tools/gen_runtime_from_manifest.py

dofile((debug.getinfo(1, "S").source:sub(2):match("^(.*[\\/])") or "") .. "py_runtime.lua")

"PNG 書き出しユーティリティ（Python実行用）。\n\nこのモジュールは sample/py のスクリプトから利用し、\nRGB 8bit バッファを PNG ファイルとして保存する。\n"
function _png_append_list(dst, src)
    local i = 0
    local n = #(src)
    while (i < n) do
        table.insert(dst, src[(((i) < 0) and (#(src) + (i) + 1) or ((i) + 1))])
        i = i + 1
    end
end

function _crc32(data)
    local crc = 4294967295
    local poly = 3988292384
    for _, b in ipairs(data) do
        crc = (crc ~ b)
        local i = 0
        while (i < 8) do
            local lowbit = (crc & 1)
            if (lowbit ~= 0) then
                crc = ((crc >> 1) ~ poly)
            else
                crc = (crc >> 1)
            end
            i = i + 1
        end
    end
    return (crc ~ 4294967295)
end

function _adler32(data)
    local mod = 65521
    local s1 = 1
    local s2 = 0
    for _, b in ipairs(data) do
        s1 = s1 + b
        if (s1 >= mod) then
            s1 = s1 - mod
        end
        s2 = s2 + s1
        s2 = (s2 % mod)
    end
    return (((s2 << 16) | s1) & 4294967295)
end

function _png_u16le(v)
    return { (v & 255), ((v >> 8) & 255) }
end

function _png_u32be(v)
    return { ((v >> 24) & 255), ((v >> 16) & 255), ((v >> 8) & 255), (v & 255) }
end

function _zlib_deflate_store(data)
    local out = {  }
    _png_append_list(out, { 120, 1 })
    local n = #(data)
    local pos = 0
    while (pos < n) do
        local remain = (n - pos)
        local chunk_len = (function() if __pytra_truthy((remain > 65535)) then return (65535) else return (remain) end end)()
        local final = (function() if __pytra_truthy(((pos + chunk_len) >= n)) then return (1) else return (0) end end)()
        table.insert(out, final)
        _png_append_list(out, _png_u16le(chunk_len))
        _png_append_list(out, _png_u16le((65535 ~ chunk_len)))
        local i = pos
        local _end = (pos + chunk_len)
        while (i < _end) do
            table.insert(out, data[(((i) < 0) and (#(data) + (i) + 1) or ((i) + 1))])
            i = i + 1
        end
        pos = pos + chunk_len
    end
    _png_append_list(out, _png_u32be(_adler32(data)))
    return out
end

function _chunk(chunk_type, data)
    local crc_input = {  }
    _png_append_list(crc_input, chunk_type)
    _png_append_list(crc_input, data)
    local crc = (_crc32(crc_input) & 4294967295)
    local out = {  }
    _png_append_list(out, _png_u32be(#(data)))
    _png_append_list(out, chunk_type)
    _png_append_list(out, data)
    _png_append_list(out, _png_u32be(crc))
    return out
end

function write_rgb_png(path, width, height, pixels)
    local raw = {  }
    for _, b in ipairs(pixels) do
        table.insert(raw, __pytra_int(b))
    end
    local expected = ((width * height) * 3)
    if (#(raw) ~= expected) then
        error(((("pixels length mismatch: got=" .. tostring(#(raw))) .. " expected=") .. tostring(expected)))
    end
    local scanlines = {  }
    local row_bytes = (width * 3)
    local y = 0
    while (y < height) do
        table.insert(scanlines, 0)
        local start = (y * row_bytes)
        local _end = (start + row_bytes)
        local i = start
        while (i < _end) do
            table.insert(scanlines, raw[(((i) < 0) and (#(raw) + (i) + 1) or ((i) + 1))])
            i = i + 1
        end
        y = y + 1
    end
    local ihdr = {  }
    _png_append_list(ihdr, _png_u32be(width))
    _png_append_list(ihdr, _png_u32be(height))
    _png_append_list(ihdr, { 8, 2, 0, 0, 0 })
    local idat = _zlib_deflate_store(scanlines)
    
    local png = {  }
    _png_append_list(png, { 137, 80, 78, 71, 13, 10, 26, 10 })
    _png_append_list(png, _chunk({ 73, 72, 68, 82 }, ihdr))
    _png_append_list(png, _chunk({ 73, 68, 65, 84 }, idat))
    local iend_data = {  }
    _png_append_list(png, _chunk({ 73, 69, 78, 68 }, iend_data))
    
    local f = open(path, "wb")
    f:write(__pytra_bytes(png))
    f:close()
end
