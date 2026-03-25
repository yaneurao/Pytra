"""アニメーションGIFを書き出すための最小ヘルパー。"""


from pytra.std import abi


def _gif_append(dst: bytearray, src: bytearray) -> None:
    i = 0
    n = len(src)
    while i < n:
        dst.append(src[i])
        i += 1


def _gif_u16le(v: int) -> bytearray:
    return bytearray([v & 0xFF, (v >> 8) & 0xFF])


def _lzw_encode(data: bytes, min_code_size: int = 8) -> bytes:
    if len(data) == 0:
        empty: bytearray = bytearray()
        return bytes(empty)

    clear_code = 1 << min_code_size
    end_code = clear_code + 1
    code_size = min_code_size + 1

    out: bytearray = bytearray()
    bit_buffer = 0
    bit_count = 0

    bit_buffer |= clear_code << bit_count
    bit_count += code_size
    while bit_count >= 8:
        out.append(bit_buffer & 0xFF)
        bit_buffer = bit_buffer >> 8
        bit_count -= 8
    code_size = min_code_size + 1

    for v in data:
        bit_buffer |= v << bit_count
        bit_count += code_size
        while bit_count >= 8:
            out.append(bit_buffer & 0xFF)
            bit_buffer = bit_buffer >> 8
            bit_count -= 8

        bit_buffer |= clear_code << bit_count
        bit_count += code_size
        while bit_count >= 8:
            out.append(bit_buffer & 0xFF)
            bit_buffer = bit_buffer >> 8
            bit_count -= 8

        code_size = min_code_size + 1

    bit_buffer |= end_code << bit_count
    bit_count += code_size
    while bit_count >= 8:
        out.append(bit_buffer & 0xFF)
        bit_buffer = bit_buffer >> 8
        bit_count -= 8

    if bit_count > 0:
        out.append(bit_buffer & 0xFF)

    return bytes(out)


def grayscale_palette() -> bytes:
    p: bytearray = bytearray()
    i = 0
    while i < 256:
        p.append(i)
        p.append(i)
        p.append(i)
        i += 1
    return bytes(p)


@abi(args={"frames": "value"})
def save_gif(
    path: str,
    width: int,
    height: int,
    frames: list[bytes],
    palette: bytes,
    delay_cs: int = 4,
    loop: int = 0,
) -> None:
    if len(palette) != 256 * 3:
        raise ValueError("palette must be 256*3 bytes")

    frame_lists: list[bytearray] = []
    for fr in frames:
        fr_buf: bytearray = bytearray()
        for v in fr:
            fr_buf.append(int(v))
        if len(fr_buf) != width * height:
            raise ValueError("frame size mismatch")
        frame_lists.append(fr_buf)

    palette_buf: bytearray = bytearray()
    for v in palette:
        palette_buf.append(int(v))

    out: bytearray = bytearray()
    _gif_append(out, bytearray([71, 73, 70, 56, 57, 97]))  # GIF89a
    _gif_append(out, _gif_u16le(width))
    _gif_append(out, _gif_u16le(height))
    out.append(0xF7)
    out.append(0)
    out.append(0)
    _gif_append(out, palette_buf)

    _gif_append(out, bytearray([0x21, 0xFF, 0x0B, 78, 69, 84, 83, 67, 65, 80, 69, 50, 46, 48, 0x03, 0x01]))
    _gif_append(out, _gif_u16le(loop))
    out.append(0)

    for fr_buf in frame_lists:
        _gif_append(out, bytearray([0x21, 0xF9, 0x04, 0x00]))
        _gif_append(out, _gif_u16le(delay_cs))
        _gif_append(out, bytearray([0x00, 0x00]))

        out.append(0x2C)
        _gif_append(out, _gif_u16le(0))
        _gif_append(out, _gif_u16le(0))
        _gif_append(out, _gif_u16le(width))
        _gif_append(out, _gif_u16le(height))
        out.append(0)
        out.append(8)
        compressed = _lzw_encode(bytes(fr_buf), 8)
        pos = 0
        while pos < len(compressed):
            remain = len(compressed) - pos
            chunk_len = 255 if remain > 255 else remain
            out.append(chunk_len)
            i = 0
            while i < chunk_len:
                out.append(compressed[pos + i])
                i += 1
            pos += chunk_len
        out.append(0)

    out.append(0x3B)

    with open(path, "wb") as f:
        f.write(bytes(out))
