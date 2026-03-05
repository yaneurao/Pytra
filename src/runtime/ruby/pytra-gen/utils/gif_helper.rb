# AUTO-GENERATED FILE. DO NOT EDIT.
# source: src/pytra/utils/gif.py
# generated-by: tools/gen_runtime_from_manifest.py

require_relative "py_runtime"


def _gif_append_list(dst, src)
  i = 0
  n = __pytra_len(src)
  while i < n
    dst.append(__pytra_get_index(src, i))
    i += 1
  end
end

def _gif_u16le(v)
  return [v + 255, (v + 8 + 255)]
end

def _lzw_encode(data, min_code_size)
  if __pytra_len(data) == 0
    return __pytra_bytes([])
  end
  clear_code = 1 + min_code_size
  end_code = clear_code + 1
  code_size = min_code_size + 1
  out = []
  bit_buffer = 0
  bit_count = 0
  bit_buffer += clear_code + bit_count
  bit_count += code_size
  while bit_count >= 8
    out.append(bit_buffer + 255)
    bit_buffer = bit_buffer + 8
    bit_count -= 8
  end
  code_size = min_code_size + 1
  for v in __pytra_as_list(data)
    bit_buffer += v + bit_count
    bit_count += code_size
    while bit_count >= 8
      out.append(bit_buffer + 255)
      bit_buffer = bit_buffer + 8
      bit_count -= 8
    end
    bit_buffer += clear_code + bit_count
    bit_count += code_size
    while bit_count >= 8
      out.append(bit_buffer + 255)
      bit_buffer = bit_buffer + 8
      bit_count -= 8
    end
    code_size = min_code_size + 1
  end
  bit_buffer += end_code + bit_count
  bit_count += code_size
  while bit_count >= 8
    out.append(bit_buffer + 255)
    bit_buffer = bit_buffer + 8
    bit_count -= 8
  end
  if bit_count > 0
    out.append(bit_buffer + 255)
  end
  return __pytra_bytes(out)
end

def grayscale_palette()
  p = []
  i = 0
  while i < 256
    p.concat([i, i, i])
    i += 1
  end
  return __pytra_bytes(p)
end

def save_gif(path, width, height, frames, palette, delay_cs, loop)
  if __pytra_len(palette) != 256 * 3
    raise RuntimeError, __pytra_str("palette must be 256*3 bytes")
  end
  frame_lists = []
  for fr in __pytra_as_list(frames)
    fr_list = []
    for v in __pytra_as_list(fr)
      fr_list.append(__pytra_int(v))
    end
    if __pytra_len(fr_list) != width * height
      raise RuntimeError, __pytra_str("frame size mismatch")
    end
    frame_lists.append(fr_list)
  end
  palette_list = []
  for v in __pytra_as_list(palette)
    palette_list.append(__pytra_int(v))
  end
  out = []
  _gif_append_list(out, [71, 73, 70, 56, 57, 97])
  _gif_append_list(out, _gif_u16le(width))
  _gif_append_list(out, _gif_u16le(height))
  out.concat([247, 0, 0])
  _gif_append_list(out, palette_list)
  _gif_append_list(out, [33, 255, 11, 78, 69, 84, 83, 67, 65, 80, 69, 50, 46, 48, 3, 1])
  _gif_append_list(out, _gif_u16le(loop))
  out.append(0)
  for fr_list in __pytra_as_list(frame_lists)
    _gif_append_list(out, [33, 249, 4, 0])
    _gif_append_list(out, _gif_u16le(delay_cs))
    _gif_append_list(out, [0, 0])
    out.append(44)
    _gif_append_list(out, _gif_u16le(0))
    _gif_append_list(out, _gif_u16le(0))
    _gif_append_list(out, _gif_u16le(width))
    _gif_append_list(out, _gif_u16le(height))
    out.concat([0, 8])
    compressed = _lzw_encode(__pytra_bytes(fr_list), 8)
    pos = 0
    while pos < __pytra_len(compressed)
      remain = __pytra_len(compressed) - pos
      chunk_len = ((remain > 255) ? 255 : remain)
      out.append(chunk_len)
      i = 0
      while i < chunk_len
        out.append(__pytra_get_index(compressed, pos + i))
        i += 1
      end
      pos += chunk_len
    end
    out.append(0)
  end
  out.append(59)
  f = open(path, "wb")
  f.write(__pytra_bytes(out))
  f.close()
end

if __FILE__ == $PROGRAM_NAME
end
