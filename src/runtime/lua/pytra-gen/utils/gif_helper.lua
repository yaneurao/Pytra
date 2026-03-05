-- AUTO-GENERATED FILE. DO NOT EDIT.
-- source: src/pytra/utils/gif.py
-- generated-by: tools/gen_runtime_from_manifest.py

dofile((debug.getinfo(1, "S").source:sub(2):match("^(.*[\\/])") or "") .. "py_runtime.lua")

-- from __future__ import annotations as annotations (not yet mapped)

"アニメーションGIFを書き出すための最小ヘルパー。"
function _gif_append_list(dst, src)
    i = 0
    n = #(src)
    while (i < n) do
        table.insert(dst, src[(((i) < 0) and (#(src) + (i) + 1) or ((i) + 1))])
        i = i + 1
    end
end

function _gif_u16le(v)
    return { (v + 255), ((v + 8) + 255) }
end

function _lzw_encode(data, min_code_size)
    if (#(data) == 0) then
        return __pytra_bytes({  })
    end
    clear_code = (1 + min_code_size)
    end_code = (clear_code + 1)
    code_size = (min_code_size + 1)
    
    local out = {  }
    bit_buffer = 0
    bit_count = 0
    
    bit_buffer = bit_buffer + (clear_code + bit_count)
    bit_count = bit_count + code_size
    while (bit_count >= 8) do
        table.insert(out, (bit_buffer + 255))
        bit_buffer = (bit_buffer + 8)
        bit_count = bit_count - 8
    end
    code_size = (min_code_size + 1)
    
    for _, v in ipairs(data) do
        bit_buffer = bit_buffer + (v + bit_count)
        bit_count = bit_count + code_size
        while (bit_count >= 8) do
            table.insert(out, (bit_buffer + 255))
            bit_buffer = (bit_buffer + 8)
            bit_count = bit_count - 8
        end
        bit_buffer = bit_buffer + (clear_code + bit_count)
        bit_count = bit_count + code_size
        while (bit_count >= 8) do
            table.insert(out, (bit_buffer + 255))
            bit_buffer = (bit_buffer + 8)
            bit_count = bit_count - 8
        end
        code_size = (min_code_size + 1)
    end
    bit_buffer = bit_buffer + (end_code + bit_count)
    bit_count = bit_count + code_size
    while (bit_count >= 8) do
        table.insert(out, (bit_buffer + 255))
        bit_buffer = (bit_buffer + 8)
        bit_count = bit_count - 8
    end
    if (bit_count > 0) then
        table.insert(out, (bit_buffer + 255))
    end
    return __pytra_bytes(out)
end

function grayscale_palette()
    local p = {  }
    i = 0
    while (i < 256) do
        table.move({i, i, i}, 1, 3, #(p) + 1, p)
        i = i + 1
    end
    return __pytra_bytes(p)
end

function save_gif(path, width, height, frames, palette, delay_cs, loop)
    if (#(palette) ~= (256 * 3)) then
        error("palette must be 256*3 bytes")
    end
    local frame_lists = {  }
    for _, fr in ipairs(frames) do
        local fr_list = {  }
        for _, v in ipairs(fr) do
            table.insert(fr_list, __pytra_int(v))
        end
        if (#(fr_list) ~= (width * height)) then
            error("frame size mismatch")
        end
        table.insert(frame_lists, fr_list)
    end
    local palette_list = {  }
    for _, v in ipairs(palette) do
        table.insert(palette_list, __pytra_int(v))
    end
    local out = {  }
    _gif_append_list(out, { 71, 73, 70, 56, 57, 97 })
    _gif_append_list(out, _gif_u16le(width))
    _gif_append_list(out, _gif_u16le(height))
    table.move({247, 0, 0}, 1, 3, #(out) + 1, out)
    _gif_append_list(out, palette_list)
    
    _gif_append_list(out, { 33, 255, 11, 78, 69, 84, 83, 67, 65, 80, 69, 50, 46, 48, 3, 1 })
    _gif_append_list(out, _gif_u16le(loop))
    table.insert(out, 0)
    
    for _, fr_list in ipairs(frame_lists) do
        _gif_append_list(out, { 33, 249, 4, 0 })
        _gif_append_list(out, _gif_u16le(delay_cs))
        _gif_append_list(out, { 0, 0 })
        
        table.insert(out, 44)
        _gif_append_list(out, _gif_u16le(0))
        _gif_append_list(out, _gif_u16le(0))
        _gif_append_list(out, _gif_u16le(width))
        _gif_append_list(out, _gif_u16le(height))
        table.move({0, 8}, 1, 2, #(out) + 1, out)
        compressed = _lzw_encode(__pytra_bytes(fr_list), 8)
        pos = 0
        while (pos < #(compressed)) do
            remain = (#(compressed) - pos)
            chunk_len = (((remain > 255)) and (255) or (remain))
            table.insert(out, chunk_len)
            i = 0
            while (i < chunk_len) do
                table.insert(out, compressed[((((pos + i)) < 0) and (#(compressed) + ((pos + i)) + 1) or (((pos + i)) + 1))])
                i = i + 1
            end
            pos = pos + chunk_len
        end
        table.insert(out, 0)
    end
    table.insert(out, 59)
    
    f = open(path, "wb")
    f:write(__pytra_bytes(out))
    f:close()
end
