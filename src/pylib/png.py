"""PNG 書き出しユーティリティ（Python実行用）。

このモジュールは sample/py のスクリプトから利用し、
RGB 8bit バッファを PNG ファイルとして保存する。
"""

from __future__ import annotations

import binascii
import struct
import zlib


def _chunk(chunk_type: bytes, data: bytes) -> bytes:
    length = struct.pack(">I", len(data))
    crc = binascii.crc32(chunk_type + data) & 0xFFFFFFFF
    return length + chunk_type + data + struct.pack(">I", crc)


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
        raise ValueError(f"pixels length mismatch: got={len(raw)} expected={expected}")

    scanlines = bytearray()
    row_bytes = width * 3
    y = 0
    while y < height:
        scanlines.append(0)  # filter type 0
        start = y * row_bytes
        end = start + row_bytes
        scanlines.extend(raw[start:end])
        y += 1

    ihdr = struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0)
    idat = zlib.compress(bytes(scanlines), level=6)

    png = bytearray()
    png.extend(b"\x89PNG\r\n\x1a\n")
    png.extend(_chunk(b"IHDR", ihdr))
    png.extend(_chunk(b"IDAT", idat))
    png.extend(_chunk(b"IEND", b""))

    with open(path, "wb") as f:
        f.write(png)
