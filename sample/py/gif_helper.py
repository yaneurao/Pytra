"""アニメーションGIFを書き出すための最小ヘルパー。"""

from __future__ import annotations


def _lzw_encode_indexed(data: bytes, min_code_size: int = 8) -> bytes:
    """GIF向けLZW圧縮（インデックスカラー列）を返す。"""
    clear_code = 1 << min_code_size
    end_code = clear_code + 1

    dictionary: dict[bytes, int] = {bytes([i]): i for i in range(clear_code)}
    next_code = end_code + 1
    code_size = min_code_size + 1
    max_code = (1 << code_size) - 1

    codes: list[int] = [clear_code]
    w = b""

    for k in data:
        wk = w + bytes([k])
        if wk in dictionary:
            w = wk
            continue

        if w:
            codes.append(dictionary[w])

        if next_code < 4096:
            dictionary[wk] = next_code
            next_code += 1
            if next_code > max_code and code_size < 12:
                code_size += 1
                max_code = (1 << code_size) - 1
        else:
            codes.append(clear_code)
            dictionary = {bytes([i]): i for i in range(clear_code)}
            next_code = end_code + 1
            code_size = min_code_size + 1
            max_code = (1 << code_size) - 1

        w = bytes([k])

    if w:
        codes.append(dictionary[w])
    codes.append(end_code)

    # LSB-first bit packing
    out = bytearray()
    bit_buffer = 0
    bit_count = 0

    dictionary = {bytes([i]): i for i in range(clear_code)}
    next_code = end_code + 1
    code_size = min_code_size + 1
    max_code = (1 << code_size) - 1

    w = b""
    idx = 0
    while idx < len(codes):
        code = codes[idx]
        idx += 1

        bit_buffer |= code << bit_count
        bit_count += code_size
        while bit_count >= 8:
            out.append(bit_buffer & 0xFF)
            bit_buffer >>= 8
            bit_count -= 8

        if code == clear_code:
            dictionary = {bytes([i]): i for i in range(clear_code)}
            next_code = end_code + 1
            code_size = min_code_size + 1
            max_code = (1 << code_size) - 1
            w = b""
            continue

        if code == end_code:
            break

        if not w:
            w = bytes([code])
            continue

        if code < len(dictionary):
            entry = list(dictionary.keys())[list(dictionary.values()).index(code)]
        else:
            entry = w + w[:1]

        if next_code < 4096:
            dictionary[w + entry[:1]] = next_code
            next_code += 1
            if next_code > max_code and code_size < 12:
                code_size += 1
                max_code = (1 << code_size) - 1

        w = entry

    if bit_count > 0:
        out.append(bit_buffer & 0xFF)

    return bytes(out)


def _lzw_encode(data: bytes, min_code_size: int = 8) -> bytes:
    """GIF用LZW圧縮を実行（辞書管理を標準的に実装）。"""
    clear_code = 1 << min_code_size
    end_code = clear_code + 1

    dictionary: dict[bytes, int] = {bytes([i]): i for i in range(clear_code)}
    next_code = end_code + 1
    code_size = min_code_size + 1

    codes: list[int] = [clear_code]
    s = bytes([data[0]])
    for c in data[1:]:
        sc = s + bytes([c])
        if sc in dictionary:
            s = sc
            continue

        codes.append(dictionary[s])
        if next_code < 4096:
            dictionary[sc] = next_code
            next_code += 1
            if next_code == (1 << code_size) and code_size < 12:
                code_size += 1
        else:
            codes.append(clear_code)
            dictionary = {bytes([i]): i for i in range(clear_code)}
            next_code = end_code + 1
            code_size = min_code_size + 1

        s = bytes([c])

    codes.append(dictionary[s])
    codes.append(end_code)

    # codesを再計算しながら可変ビット幅で詰める
    dictionary = {bytes([i]): i for i in range(clear_code)}
    next_code = end_code + 1
    code_size = min_code_size + 1

    out = bytearray()
    bit_buffer = 0
    bit_count = 0

    def emit(code: int, bits: int) -> None:
        nonlocal bit_buffer, bit_count
        bit_buffer |= code << bit_count
        bit_count += bits
        while bit_count >= 8:
            out.append(bit_buffer & 0xFF)
            bit_buffer >>= 8
            bit_count -= 8

    emit(clear_code, code_size)
    s = bytes([data[0]])
    for c in data[1:]:
        sc = s + bytes([c])
        if sc in dictionary:
            s = sc
            continue

        emit(dictionary[s], code_size)
        if next_code < 4096:
            dictionary[sc] = next_code
            next_code += 1
            if next_code == (1 << code_size) and code_size < 12:
                code_size += 1
        else:
            emit(clear_code, code_size)
            dictionary = {bytes([i]): i for i in range(clear_code)}
            next_code = end_code + 1
            code_size = min_code_size + 1

        s = bytes([c])

    emit(dictionary[s], code_size)
    emit(end_code, code_size)

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
