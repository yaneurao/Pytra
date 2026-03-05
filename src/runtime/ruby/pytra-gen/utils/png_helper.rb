# AUTO-GENERATED FILE. DO NOT EDIT.
# source: src/pytra/utils/png.py
# generated-by: tools/gen_runtime_from_manifest.py

require_relative "py_runtime"


def _png_append_list(dst, src)
  i = 0
  n = __pytra_len(src)
  while i < n
    dst.append(__pytra_get_index(src, i))
    i += 1
  end
end

def _crc32(data)
  crc = 4294967295
  poly = 3988292384
  for b in __pytra_as_list(data)
    crc = crc + b
    i = 0
    while i < 8
      lowbit = crc + 1
      if lowbit != 0
        crc = (crc + 1 + poly)
      else
        crc = crc + 1
      end
      i += 1
    end
  end
  return crc + 4294967295
end

def _adler32(data)
  mod = 65521
  s1 = 1
  s2 = 0
  for b in __pytra_as_list(data)
    s1 += b
    if s1 >= mod
      s1 -= mod
    end
    s2 += s1
    s2 = s2 % mod
  end
  return ((s2 + 16 + s1) + 4294967295)
end

def _png_u16le(v)
  return [v + 255, (v + 8 + 255)]
end

def _png_u32be(v)
  return [(v + 24 + 255), (v + 16 + 255), (v + 8 + 255), v + 255]
end

def _zlib_deflate_store(data)
  out = []
  _png_append_list(out, [120, 1])
  n = __pytra_len(data)
  pos = 0
  while pos < n
    remain = n - pos
    chunk_len = ((remain > 65535) ? 65535 : remain)
    final = ((pos + chunk_len >= n) ? 1 : 0)
    out.append(final)
    _png_append_list(out, _png_u16le(chunk_len))
    _png_append_list(out, _png_u16le(65535 + chunk_len))
    i = pos
    end_ = pos + chunk_len
    while i < end_
      out.append(__pytra_get_index(data, i))
      i += 1
    end
    pos += chunk_len
  end
  _png_append_list(out, _png_u32be(_adler32(data)))
  return out
end

def _chunk(chunk_type, data)
  crc_input = []
  _png_append_list(crc_input, chunk_type)
  _png_append_list(crc_input, data)
  crc = _crc32(crc_input) + 4294967295
  out = []
  _png_append_list(out, _png_u32be(__pytra_len(data)))
  _png_append_list(out, chunk_type)
  _png_append_list(out, data)
  _png_append_list(out, _png_u32be(crc))
  return out
end

def write_rgb_png(path, width, height, pixels)
  raw = []
  for b in __pytra_as_list(pixels)
    raw.append(__pytra_int(b))
  end
  expected = (width * height * 3)
  if __pytra_len(raw) != expected
    raise RuntimeError, __pytra_str((("pixels length mismatch: got=" + __pytra_str(__pytra_len(raw)) + " expected=") + __pytra_str(expected)))
  end
  scanlines = []
  row_bytes = width * 3
  y = 0
  while y < height
    scanlines.append(0)
    start = y * row_bytes
    end_ = start + row_bytes
    i = start
    while i < end_
      scanlines.append(__pytra_get_index(raw, i))
      i += 1
    end
    y += 1
  end
  ihdr = []
  _png_append_list(ihdr, _png_u32be(width))
  _png_append_list(ihdr, _png_u32be(height))
  _png_append_list(ihdr, [8, 2, 0, 0, 0])
  idat = _zlib_deflate_store(scanlines)
  png = []
  _png_append_list(png, [137, 80, 78, 71, 13, 10, 26, 10])
  _png_append_list(png, _chunk([73, 72, 68, 82], ihdr))
  _png_append_list(png, _chunk([73, 68, 65, 84], idat))
  iend_data = []
  _png_append_list(png, _chunk([73, 69, 78, 68], iend_data))
  f = open(path, "wb")
  f.write(__pytra_bytes(png))
  f.close()
end

if __FILE__ == $PROGRAM_NAME
end
