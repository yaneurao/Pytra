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

    bit_buffer |= clear_code << bit_count
    bit_count += code_size
    while bit_count >= 8:
        out.append(bit_buffer & 0xFF)
        bit_buffer >>= 8
        bit_count -= 8
    code_size = min_code_size + 1

    for v in data:
        bit_buffer |= v << bit_count
        bit_count += code_size
        while bit_count >= 8:
            out.append(bit_buffer & 0xFF)
            bit_buffer >>= 8
            bit_count -= 8

        bit_buffer |= clear_code << bit_count
        bit_count += code_size
        while bit_count >= 8:
            out.append(bit_buffer & 0xFF)
            bit_buffer >>= 8
            bit_count -= 8

        code_size = min_code_size + 1

    bit_buffer |= end_code << bit_count
    bit_count += code_size
    while bit_count >= 8:
        out.append(bit_buffer & 0xFF)
        bit_buffer >>= 8
        bit_count -= 8

    if bit_count > 0:
        out.append(bit_buffer & 0xFF)

    return bytes(out)


def grayscale_palette() -> bytes:
    """0..255のグレースケールパレットを返す。"""
    p = bytearray()
    i = 0
    while i < 256:
        p.append(i)
        p.append(i)
        p.append(i)
        i += 1
    return bytes(p)

def _append_u16le(out: bytearray, value: int) -> None:
    out.append(value & 0xFF)
    out.append((value >> 8) & 0xFF)


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
    _append_u16le(out, width)
    _append_u16le(out, height)
    out.append(0xF7)  # GCT flag=1, color resolution=7, table size=7 (256)
    out.append(0)  # background index
    out.append(0)  # pixel aspect ratio
    out.extend(palette)

    # Netscape loop extension
    out.extend(b"\x21\xFF\x0BNETSCAPE2.0\x03\x01")
    _append_u16le(out, loop)
    out.append(0)

    for fr in frames:
        out.extend(b"\x21\xF9\x04\x00")
        _append_u16le(out, delay_cs)
        out.extend(b"\x00\x00")

        out.append(0x2C)
        _append_u16le(out, 0)
        _append_u16le(out, 0)
        _append_u16le(out, width)
        _append_u16le(out, height)
        out.append(0)  # no local color table

        out.append(8)  # min LZW code size
        compressed = _lzw_encode(fr, 8)
        pos = 0
        while pos < len(compressed):
            chunk_len = len(compressed) - pos
            if chunk_len > 255:
                chunk_len = 255
            out.append(chunk_len)
            i = 0
            while i < chunk_len:
                out.append(compressed[pos + i])
                i += 1
            pos += chunk_len
        out.append(0)

    out.append(0x3B)

    f = open(path, "wb")
    f.write(out)
    f.close()
