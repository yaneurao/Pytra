"""PNG 書き出しユーティリティ（Python実行用）。

このモジュールは sample/py のスクリプトから利用し、
RGB 8bit バッファを PNG ファイルとして保存する。
"""

from __future__ import annotations


def _png_append_list(dst: list[int], src: list[int]) -> None:
    i = 0
    n = len(src)
    while i < n:
        dst.append(src[i])
        i += 1


def _crc32(data: list[int]) -> int:
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


def _adler32(data: list[int]) -> int:
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


def _png_u16le(v: int) -> list[int]:
    return [v & 0xFF, (v >> 8) & 0xFF]


def _png_u32be(v: int) -> list[int]:
    return [(v >> 24) & 0xFF, (v >> 16) & 0xFF, (v >> 8) & 0xFF, v & 0xFF]


def _zlib_deflate_store(data: list[int]) -> list[int]:
    out: list[int] = []
    _png_append_list(out, [0x78, 0x01])
    n = len(data)
    pos = 0
    while pos < n:
        remain = n - pos
        chunk_len = 65535 if remain > 65535 else remain
        final = 1 if (pos + chunk_len) >= n else 0
        out.append(final)
        _png_append_list(out, _png_u16le(chunk_len))
        _png_append_list(out, _png_u16le(0xFFFF ^ chunk_len))
        i = pos
        end = pos + chunk_len
        while i < end:
            out.append(data[i])
            i += 1
        pos += chunk_len
    _png_append_list(out, _png_u32be(_adler32(data)))
    return out


def _chunk(chunk_type: list[int], data: list[int]) -> list[int]:
    crc_input: list[int] = []
    _png_append_list(crc_input, chunk_type)
    _png_append_list(crc_input, data)
    crc = _crc32(crc_input) & 0xFFFFFFFF
    out: list[int] = []
    _png_append_list(out, _png_u32be(len(data)))
    _png_append_list(out, chunk_type)
    _png_append_list(out, data)
    _png_append_list(out, _png_u32be(crc))
    return out


def write_rgb_png(path: str, width: int, height: int, pixels: bytes) -> None:
    raw: list[int] = []
    for b in pixels:
        raw.append(int(b))
    expected = width * height * 3
    if len(raw) != expected:
        raise ValueError("pixels length mismatch: got=" + str(len(raw)) + " expected=" + str(expected))

    scanlines: list[int] = []
    row_bytes = width * 3
    y = 0
    while y < height:
        scanlines.append(0)
        start = y * row_bytes
        end = start + row_bytes
        i = start
        while i < end:
            scanlines.append(raw[i])
            i += 1
        y += 1

    ihdr: list[int] = []
    _png_append_list(ihdr, _png_u32be(width))
    _png_append_list(ihdr, _png_u32be(height))
    _png_append_list(ihdr, [8, 2, 0, 0, 0])
    idat = _zlib_deflate_store(scanlines)

    png: list[int] = []
    _png_append_list(png, [137, 80, 78, 71, 13, 10, 26, 10])
    _png_append_list(png, _chunk([73, 72, 68, 82], ihdr))
    _png_append_list(png, _chunk([73, 68, 65, 84], idat))
    iend_data: list[int] = []
    _png_append_list(png, _chunk([73, 69, 78, 68], iend_data))

    with open(path, "wb") as f:
        f.write(bytes(png))
