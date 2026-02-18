"""アニメーションGIFを書き出すための最小ヘルパー。"""

from __future__ import annotations


def _lzw_encode(data: bytes, min_code_size: int = 8) -> bytes:
    """GIF用LZW圧縮を実行する（互換性重視: Clear+Literal方式）。"""
    if len(data) == 0:
        return b""

    clear_code = 1 << min_code_size
    end_code = clear_code + 1

    code_size = min_code_size + 1

    out = bytearray()
    bit_buffer = 0
    bit_count = 0

    def emit(code: int) -> None:
        nonlocal bit_buffer, bit_count
        bit_buffer |= code << bit_count
        bit_count += code_size
        while bit_count >= 8:
            out.append(bit_buffer & 0xFF)
            bit_buffer >>= 8
            bit_count -= 8

    def reset_table() -> None:
        nonlocal code_size
        code_size = min_code_size + 1

    emit(clear_code)
    reset_table()

    for v in data:
        emit(v)
        emit(clear_code)
        reset_table()

    emit(end_code)

    if bit_count > 0:
        out.append(bit_buffer & 0xFF)

    return bytes(out)


def grayscale_palette() -> bytes:
    """0..255のグレースケールパレットを返す。"""
    p = bytearray()
    i = 0
    while i < 256:
        p.extend((i, i, i))
        i += 1
    return bytes(p)


def save_gif(
    path: str,
    width: int,
    height: int,
    frames: list[bytes],
    palette: bytes,
    delay_cs: int = 4,
    loop: int = 0,
) -> None:
    """インデックスカラーのフレーム列をアニメーションGIFとして保存する。"""
    if len(palette) != 256 * 3:
        raise ValueError("palette must be 256*3 bytes")

    for fr in frames:
        if len(fr) != width * height:
            raise ValueError("frame size mismatch")

    out = bytearray()
    out.extend(b"GIF89a")
    out.extend(width.to_bytes(2, "little"))
    out.extend(height.to_bytes(2, "little"))
    out.append(0xF7)  # GCT flag=1, color resolution=7, table size=7 (256)
    out.append(0)  # background index
    out.append(0)  # pixel aspect ratio
    out.extend(palette)

    # Netscape loop extension
    out.extend(b"\x21\xFF\x0BNETSCAPE2.0\x03\x01")
    out.extend(loop.to_bytes(2, "little"))
    out.append(0)

    for fr in frames:
        out.extend(b"\x21\xF9\x04\x00")
        out.extend(delay_cs.to_bytes(2, "little"))
        out.extend(b"\x00\x00")

        out.append(0x2C)
        out.extend((0).to_bytes(2, "little"))
        out.extend((0).to_bytes(2, "little"))
        out.extend(width.to_bytes(2, "little"))
        out.extend(height.to_bytes(2, "little"))
        out.append(0)  # no local color table

        out.append(8)  # min LZW code size
        compressed = _lzw_encode(fr, 8)
        pos = 0
        while pos < len(compressed):
            chunk = compressed[pos : pos + 255]
            out.append(len(chunk))
            out.extend(chunk)
            pos += len(chunk)
        out.append(0)

    out.append(0x3B)

    with open(path, "wb") as f:
        f.write(out)
