"""PNG 書き出しユーティリティ（Python実行用）。

このモジュールは sample/py のスクリプトから利用し、
RGB 8bit バッファを PNG ファイルとして保存する。
"""



def _png_append(dst: bytearray, src: bytearray) -> None:
    dst.extend(src)


def _crc32(data: bytearray) -> int:
    crc = 0xFFFFFFFF
    poly = 0xEDB88320
    for b in data:
        crc = crc ^ b
        i = 0
        while i < 8:
            lowbit = crc & 1
            if lowbit != 0:
                crc = (crc >> 1) ^ poly
            else:
                crc = crc >> 1
            i += 1
    return crc ^ 0xFFFFFFFF


def _adler32(data: bytearray) -> int:
    mod = 65521
    s1 = 1
    s2 = 0
    for b in data:
        s1 += b
        if s1 >= mod:
            s1 -= mod
        s2 += s1
        s2 = s2 % mod
    return ((s2 << 16) | s1) & 0xFFFFFFFF


def _png_u16le(v: int) -> bytearray:
    return bytearray([v & 0xFF, (v >> 8) & 0xFF])


def _png_u32be(v: int) -> bytearray:
    return bytearray([(v >> 24) & 0xFF, (v >> 16) & 0xFF, (v >> 8) & 0xFF, v & 0xFF])


def _zlib_deflate_store(data: bytearray) -> bytearray:
    out: bytearray = bytearray()
    _png_append(out, bytearray([0x78, 0x01]))
    n = len(data)
    pos = 0
    while pos < n:
        remain = n - pos
        chunk_len = 65535 if remain > 65535 else remain
        final = 1 if (pos + chunk_len) >= n else 0
        out.append(final)
        _png_append(out, _png_u16le(chunk_len))
        _png_append(out, _png_u16le(0xFFFF ^ chunk_len))
        out.extend(data[pos:pos + chunk_len])
        pos += chunk_len
    _png_append(out, _png_u32be(_adler32(data)))
    return out


def _chunk(chunk_type: bytearray, data: bytearray) -> bytearray:
    crc_input: bytearray = bytearray()
    _png_append(crc_input, chunk_type)
    _png_append(crc_input, data)
    crc = _crc32(crc_input) & 0xFFFFFFFF
    out: bytearray = bytearray()
    _png_append(out, _png_u32be(len(data)))
    _png_append(out, chunk_type)
    _png_append(out, data)
    _png_append(out, _png_u32be(crc))
    return out


def write_rgb_png(path: str, width: int, height: int, pixels: bytes) -> None:
    raw: bytearray = bytearray()
    raw.extend(pixels)
    expected = width * height * 3
    if len(raw) != expected:
        raise ValueError("pixels length mismatch: got=" + str(len(raw)) + " expected=" + str(expected))

    scanlines: bytearray = bytearray()
    row_bytes = width * 3
    y = 0
    while y < height:
        scanlines.append(0)
        start = y * row_bytes
        scanlines.extend(raw[start:start + row_bytes])
        y += 1

    ihdr: bytearray = bytearray()
    _png_append(ihdr, _png_u32be(width))
    _png_append(ihdr, _png_u32be(height))
    _png_append(ihdr, bytearray([8, 2, 0, 0, 0]))
    idat = _zlib_deflate_store(scanlines)

    png: bytearray = bytearray()
    _png_append(png, bytearray([137, 80, 78, 71, 13, 10, 26, 10]))
    _png_append(png, _chunk(bytearray([73, 72, 68, 82]), ihdr))
    _png_append(png, _chunk(bytearray([73, 68, 65, 84]), idat))
    iend_data: bytearray = bytearray()
    _png_append(png, _chunk(bytearray([73, 69, 78, 68]), iend_data))

    f = open(path, "wb")
    try:
        f.write(bytes(png))
    finally:
        f.close()
