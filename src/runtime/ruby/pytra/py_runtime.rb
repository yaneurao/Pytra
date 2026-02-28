# Ruby native backend runtime helpers.

def __pytra_noop(*args)
  _ = args
  nil
end

def __pytra_assert(*args)
  _ = args
  "True"
end

def __pytra_perf_counter
  Process.clock_gettime(Process::CLOCK_MONOTONIC)
end

def __pytra_truthy(v)
  return false if v.nil?
  return v if v == true || v == false
  return v != 0 if v.is_a?(Integer)
  return v != 0.0 if v.is_a?(Float)
  return !v.empty? if v.respond_to?(:empty?)
  true
end

def __pytra_int(v)
  return 0 if v.nil?
  v.to_i
end

def __pytra_float(v)
  return 0.0 if v.nil?
  v.to_f
end

def __pytra_div(a, b)
  lhs = __pytra_float(a)
  rhs = __pytra_float(b)
  raise ZeroDivisionError, "division by zero" if rhs == 0.0
  lhs / rhs
end

def __pytra_str(v)
  return "" if v.nil?
  v.to_s
end

def __pytra_len(v)
  return 0 if v.nil?
  return v.length if v.respond_to?(:length)
  0
end

def __pytra_as_list(v)
  return v if v.is_a?(Array)
  return v.to_a if v.respond_to?(:to_a)
  []
end

def __pytra_as_dict(v)
  return v if v.is_a?(Hash)
  {}
end

def __pytra_bytearray(v = nil)
  return [] if v.nil?
  if v.is_a?(Integer)
    n = v
    n = 0 if n < 0
    return Array.new(n, 0)
  end
  if v.is_a?(String)
    return v.bytes
  end
  src = __pytra_as_list(v)
  out = []
  i = 0
  while i < src.length
    out << (__pytra_int(src[i]) & 255)
    i += 1
  end
  out
end

def __pytra_bytes(v)
  return [] if v.nil?
  return v.bytes if v.is_a?(String)
  src = __pytra_as_list(v)
  out = []
  i = 0
  while i < src.length
    out << (__pytra_int(src[i]) & 255)
    i += 1
  end
  out
end

def __pytra_range(start_v, stop_v, step_v)
  out = []
  step = __pytra_int(step_v)
  return out if step == 0
  i = __pytra_int(start_v)
  stop = __pytra_int(stop_v)
  while ((step >= 0 && i < stop) || (step < 0 && i > stop))
    out << i
    i += step
  end
  out
end

def __pytra_list_comp_range(start_v, stop_v, step_v)
  out = []
  step = __pytra_int(step_v)
  return out if step == 0
  i = __pytra_int(start_v)
  stop = __pytra_int(stop_v)
  while ((step >= 0 && i < stop) || (step < 0 && i > stop))
    out << yield(i)
    i += step
  end
  out
end

def __pytra_enumerate(v)
  src = __pytra_as_list(v)
  out = []
  i = 0
  while i < src.length
    out << [i, src[i]]
    i += 1
  end
  out
end

def __pytra_abs(v)
  x = __pytra_float(v)
  x < 0 ? -x : x
end

def __pytra_get_index(container, index)
  if container.is_a?(Array)
    i = __pytra_int(index)
    i += container.length if i < 0
    return nil if i < 0 || i >= container.length
    return container[i]
  end
  if container.is_a?(Hash)
    return container[index]
  end
  if container.is_a?(String)
    i = __pytra_int(index)
    i += container.length if i < 0
    return "" if i < 0 || i >= container.length
    return container[i] || ""
  end
  nil
end

def __pytra_set_index(container, index, value)
  if container.is_a?(Array)
    i = __pytra_int(index)
    i += container.length if i < 0
    return if i < 0 || i >= container.length
    container[i] = value
    return
  end
  if container.is_a?(Hash)
    container[index] = value
  end
end

def __pytra_slice(container, lower, upper)
  return nil if container.nil?
  lo = __pytra_int(lower)
  hi = __pytra_int(upper)
  container[lo...hi]
end

def __pytra_min(a, b)
  __pytra_float(a) < __pytra_float(b) ? a : b
end

def __pytra_max(a, b)
  __pytra_float(a) > __pytra_float(b) ? a : b
end

def __pytra_isdigit(v)
  s = __pytra_str(v)
  return false if s.empty?
  !!(s =~ /\A[0-9]+\z/)
end

def __pytra_isalpha(v)
  s = __pytra_str(v)
  return false if s.empty?
  !!(s =~ /\A[A-Za-z]+\z/)
end

def __pytra_contains(container, item)
  return false if container.nil?
  return container.key?(item) if container.is_a?(Hash)
  return container.include?(item) if container.is_a?(Array)
  return container.include?(__pytra_str(item)) if container.is_a?(String)
  false
end

def __pytra_print(*args)
  if args.empty?
    puts
    return
  end
  puts(args.map { |x| __pytra_str(x) }.join(" "))
end

def __pytra_u16le(v)
  x = __pytra_int(v) & 0xFFFF
  [x & 0xFF, (x >> 8) & 0xFF]
end

def __pytra_u32be(v)
  x = __pytra_int(v) & 0xFFFFFFFF
  [(x >> 24) & 0xFF, (x >> 16) & 0xFF, (x >> 8) & 0xFF, x & 0xFF]
end

def __pytra_crc32(data)
  bytes = __pytra_bytes(data)
  crc = 0xFFFFFFFF
  poly = 0xEDB88320
  i = 0
  while i < bytes.length
    crc ^= bytes[i]
    bit = 0
    while bit < 8
      if (crc & 1) != 0
        crc = ((crc >> 1) ^ poly) & 0xFFFFFFFF
      else
        crc = (crc >> 1) & 0xFFFFFFFF
      end
      bit += 1
    end
    i += 1
  end
  (crc ^ 0xFFFFFFFF) & 0xFFFFFFFF
end

def __pytra_adler32(data)
  bytes = __pytra_bytes(data)
  mod = 65_521
  s1 = 1
  s2 = 0
  i = 0
  while i < bytes.length
    s1 += bytes[i]
    s1 -= mod if s1 >= mod
    s2 += s1
    s2 %= mod
    i += 1
  end
  ((s2 << 16) | s1) & 0xFFFFFFFF
end

def __pytra_zlib_deflate_store(data)
  bytes = __pytra_bytes(data)
  out = [0x78, 0x01]
  n = bytes.length
  pos = 0
  while pos < n
    remain = n - pos
    chunk_len = remain > 65_535 ? 65_535 : remain
    final = (pos + chunk_len) >= n ? 1 : 0
    out << final
    out.concat(__pytra_u16le(chunk_len))
    out.concat(__pytra_u16le(0xFFFF ^ chunk_len))
    out.concat(bytes[pos, chunk_len] || [])
    pos += chunk_len
  end
  out.concat(__pytra_u32be(__pytra_adler32(bytes)))
  out
end

def __pytra_png_chunk(chunk_type, data)
  chunk_type_bytes = __pytra_bytes(chunk_type)
  payload = __pytra_bytes(data)
  out = []
  out.concat(__pytra_u32be(payload.length))
  out.concat(chunk_type_bytes)
  out.concat(payload)
  out.concat(__pytra_u32be(__pytra_crc32(chunk_type_bytes + payload)))
  out
end

def __pytra_write_bytes(path, bytes)
  File.binwrite(__pytra_str(path), __pytra_bytes(bytes).pack("C*"))
end

def write_rgb_png(path, width, height, pixels)
  raw = __pytra_bytes(pixels)
  w = __pytra_int(width)
  h = __pytra_int(height)
  expected = w * h * 3
  if raw.length != expected
    raise ArgumentError, "pixels length mismatch: got=#{raw.length} expected=#{expected}"
  end

  scanlines = []
  row_bytes = w * 3
  y = 0
  while y < h
    scanlines << 0
    start = y * row_bytes
    scanlines.concat(raw[start, row_bytes] || [])
    y += 1
  end

  ihdr = __pytra_u32be(w) + __pytra_u32be(h) + [8, 2, 0, 0, 0]
  idat = __pytra_zlib_deflate_store(scanlines)
  png = [0x89, 0x50, 0x4E, 0x47, 0x0D, 0x0A, 0x1A, 0x0A]
  png.concat(__pytra_png_chunk([0x49, 0x48, 0x44, 0x52], ihdr))
  png.concat(__pytra_png_chunk([0x49, 0x44, 0x41, 0x54], idat))
  png.concat(__pytra_png_chunk([0x49, 0x45, 0x4E, 0x44], []))
  __pytra_write_bytes(path, png)
  nil
end

def __pytra_gif_lzw_encode(data, min_code_size = 8)
  bytes = __pytra_bytes(data)
  return [] if bytes.empty?

  clear_code = 1 << __pytra_int(min_code_size)
  end_code = clear_code + 1
  code_size = __pytra_int(min_code_size) + 1

  out = []
  bit_buffer = 0
  bit_count = 0

  emit_code = lambda do |code, bits|
    bit_buffer |= (__pytra_int(code) << bit_count)
    bit_count += __pytra_int(bits)
    while bit_count >= 8
      out << (bit_buffer & 0xFF)
      bit_buffer >>= 8
      bit_count -= 8
    end
  end

  emit_code.call(clear_code, code_size)
  i = 0
  while i < bytes.length
    emit_code.call(bytes[i], code_size)
    emit_code.call(clear_code, code_size)
    i += 1
  end
  emit_code.call(end_code, code_size)
  out << (bit_buffer & 0xFF) if bit_count > 0
  out
end

def grayscale_palette
  out = []
  i = 0
  while i < 256
    out << i
    out << i
    out << i
    i += 1
  end
  out
end

def save_gif(path, width, height, frames, palette, delay_cs = 4, loop = 0)
  w = __pytra_int(width)
  h = __pytra_int(height)
  frame_pixels = w * h
  palette_bytes = __pytra_bytes(palette)
  if palette_bytes.length != 256 * 3
    raise ArgumentError, "palette must be 256*3 bytes"
  end

  src_frames = __pytra_as_list(frames)
  normalized_frames = []
  i = 0
  while i < src_frames.length
    fr = __pytra_bytes(src_frames[i])
    if fr.length != frame_pixels
      raise ArgumentError, "frame size mismatch"
    end
    normalized_frames << fr
    i += 1
  end

  out = []
  out.concat([0x47, 0x49, 0x46, 0x38, 0x39, 0x61]) # GIF89a
  out.concat(__pytra_u16le(w))
  out.concat(__pytra_u16le(h))
  out << 0xF7
  out << 0
  out << 0
  out.concat(palette_bytes)

  out.concat([0x21, 0xFF, 0x0B])
  out.concat("NETSCAPE2.0".bytes)
  out.concat([0x03, 0x01])
  out.concat(__pytra_u16le(loop))
  out << 0

  i = 0
  while i < normalized_frames.length
    fr = normalized_frames[i]
    out.concat([0x21, 0xF9, 0x04, 0x00])
    out.concat(__pytra_u16le(delay_cs))
    out.concat([0x00, 0x00])

    out << 0x2C
    out.concat(__pytra_u16le(0))
    out.concat(__pytra_u16le(0))
    out.concat(__pytra_u16le(w))
    out.concat(__pytra_u16le(h))
    out << 0

    out << 8
    compressed = __pytra_gif_lzw_encode(fr, 8)
    pos = 0
    while pos < compressed.length
      chunk = compressed[pos, 255] || []
      out << chunk.length
      out.concat(chunk)
      pos += chunk.length
    end
    out << 0
    i += 1
  end

  out << 0x3B
  __pytra_write_bytes(path, out)
  nil
end
