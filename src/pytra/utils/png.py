"""PNG 書き出しユーティリティ（Python実行用）。

このモジュールは sample/py のスクリプトから利用し、
RGB 8bit バッファを PNG ファイルとして保存する。
"""

from __future__ import annotations

def _crc32(data: bytes) -> int:
    """PNG chunk CRC32 を pure Python で計算する。"""
    crc = 0xFFFFFFFF
    poly = 0xEDB88320
    for b in data:
        crc ^= b
        i = 0
        while i < 8:
            if (crc & 1) != 0:
                crc = (crc >> 1) ^ poly
            else:
                crc >>= 1
            i += 1
    return crc ^ 0xFFFFFFFF


def _adler32(data: bytes) -> int:
    """zlib wrapper 用 Adler-32 を pure Python で計算する。"""
    mod = 65521
    s1 = 1
    s2 = 0
    for b in data:
        s1 += b
        if s1 >= mod:
            s1 -= mod
        s2 += s1
        s2 %= mod
    return ((s2 << 16) | s1) & 0xFFFFFFFF


def _u16le(v: int) -> bytes:
    return bytes([v & 0xFF, (v >> 8) & 0xFF])


def _u32be(v: int) -> bytes:
    return bytes([(v >> 24) & 0xFF, (v >> 16) & 0xFF, (v >> 8) & 0xFF, v & 0xFF])


def _zlib_deflate_store(data: bytes) -> bytes:
    """非圧縮 DEFLATE(stored block) を使って zlib ストリームを作る。"""
    out = bytearray()
    # zlib header: CMF=0x78(Deflate, 32K window), FLG=0x01(check bits OK, fastest)
    out.extend(b"\x78\x01")
    n = len(data)
    pos = 0
    while pos < n:
        remain = n - pos
        chunk_len = remain
        if chunk_len > 65535:
            chunk_len = 65535
        final = 0
        if (pos + chunk_len) >= n:
            final = 1
        # stored block: BTYPE=00, header bit field in LSB order (final in bit0)
        out.append(final)
        out.extend(_u16le(chunk_len))
        out.extend(_u16le(0xFFFF ^ chunk_len))
        i = 0
        while i < chunk_len:
            out.append(data[pos + i])
            i += 1
        pos += chunk_len
    out.extend(_u32be(_adler32(data)))
    return bytes(out)


def _chunk(chunk_type: bytes, data: bytes) -> bytes:
    length = _u32be(len(data))
    crc = _crc32(chunk_type + data) & 0xFFFFFFFF
    return length + chunk_type + data + _u32be(crc)


def write_rgb_png(path: str, width: int, height: int, pixels: bytes | bytearray) -> None:
    """RGBバッファを PNG として保存する。

    Args:
        path: 出力PNGファイルパス。
        width: 画像幅（pixel）。
        height: 画像高さ（pixel）。
        pixels: 長さ width*height*3 の RGB バイト列。
    """
    raw = bytes(pixels)
    expected = width * height * 3
    if len(raw) != expected:
        raise ValueError("pixels length mismatch: got=" + str(len(raw)) + " expected=" + str(expected))

    scanlines = bytearray()
    row_bytes = width * 3
    y = 0
    while y < height:
        scanlines.append(0)  # filter type 0
        start = y * row_bytes
        i = 0
        while i < row_bytes:
            scanlines.append(raw[start + i])
            i += 1
        y += 1

    ihdr = _u32be(width) + _u32be(height) + bytes([8, 2, 0, 0, 0])
    idat = _zlib_deflate_store(bytes(scanlines))

    png = bytearray()
    png.extend(b"\x89PNG\r\n\x1a\n")
    png.extend(_chunk(b"IHDR", ihdr))
    png.extend(_chunk(b"IDAT", idat))
    png.extend(_chunk(b"IEND", b""))

    f = open(path, "wb")
    f.write(png)
    f.close()
