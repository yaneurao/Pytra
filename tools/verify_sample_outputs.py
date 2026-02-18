#!/usr/bin/env python3
from __future__ import annotations

import argparse
import os
import re
import shutil
import struct
import subprocess
import tempfile
import zlib
from dataclasses import dataclass
from pathlib import Path
from typing import Any

VERBOSE = False


@dataclass
class CaseResult:
    stem: str
    ok: bool
    stdout_ok: bool
    image_ok: bool
    message: str


def run_cmd(cmd: list[str], *, env: dict[str, str] | None = None) -> tuple[int, str]:
    p = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, env=env)
    return p.returncode, p.stdout


def vlog(msg: str) -> None:
    if VERBOSE:
        print(msg, flush=True)


def parse_output_path(stdout_text: str) -> str | None:
    m = re.search(r"^output:\s*(.+)$", stdout_text, flags=re.M)
    return m.group(1).strip() if m else None


def png_raw_rgb(path: Path) -> tuple[int, int, bytes]:
    b = path.read_bytes()
    if b[:8] != b"\x89PNG\r\n\x1a\n":
        raise ValueError("not a PNG file")
    i = 8
    w = h = bit = ctype = interlace = None
    idat_parts: list[bytes] = []
    while i < len(b):
        ln = struct.unpack(">I", b[i : i + 4])[0]
        i += 4
        typ = b[i : i + 4]
        i += 4
        dat = b[i : i + ln]
        i += ln
        i += 4  # crc
        if typ == b"IHDR":
            w, h, bit, ctype, _comp, _flt, interlace = struct.unpack(">IIBBBBB", dat)
            if bit != 8 or ctype != 2 or interlace != 0:
                raise ValueError("unsupported PNG format (only 8-bit RGB non-interlaced)")
        elif typ == b"IDAT":
            idat_parts.append(dat)
        elif typ == b"IEND":
            break
    if w is None or h is None:
        raise ValueError("invalid PNG")
    comp = zlib.decompress(b"".join(idat_parts))
    stride = w * 3
    out = bytearray(h * stride)
    src = 0
    prev = bytearray(stride)

    def paeth(a: int, b_: int, c: int) -> int:
        p = a + b_ - c
        pa = abs(p - a)
        pb = abs(p - b_)
        pc = abs(p - c)
        if pa <= pb and pa <= pc:
            return a
        if pb <= pc:
            return b_
        return c

    for y in range(h):
        f = comp[src]
        src += 1
        row = bytearray(comp[src : src + stride])
        src += stride
        if f == 1:
            for x in range(stride):
                row[x] = (row[x] + (row[x - 3] if x >= 3 else 0)) & 0xFF
        elif f == 2:
            for x in range(stride):
                row[x] = (row[x] + prev[x]) & 0xFF
        elif f == 3:
            for x in range(stride):
                left = row[x - 3] if x >= 3 else 0
                row[x] = (row[x] + ((left + prev[x]) >> 1)) & 0xFF
        elif f == 4:
            for x in range(stride):
                a = row[x - 3] if x >= 3 else 0
                b_ = prev[x]
                c = prev[x - 3] if x >= 3 else 0
                row[x] = (row[x] + paeth(a, b_, c)) & 0xFF
        elif f != 0:
            raise ValueError(f"unknown PNG filter: {f}")
        out[y * stride : (y + 1) * stride] = row
        prev = row
    return w, h, bytes(out)


def gif_lzw_decode(min_code_size: int, data: bytes) -> bytes:
    clear = 1 << min_code_size
    end = clear + 1
    next_code = end + 1
    code_size = min_code_size + 1

    table: dict[int, bytes] = {i: bytes([i]) for i in range(clear)}

    bitbuf = 0
    bits = 0
    p = 0

    def read_code() -> int | None:
        nonlocal bitbuf, bits, p
        while bits < code_size:
            if p >= len(data):
                return None
            bitbuf |= data[p] << bits
            bits += 8
            p += 1
        c = bitbuf & ((1 << code_size) - 1)
        bitbuf >>= code_size
        bits -= code_size
        return c

    out = bytearray()
    prev: bytes | None = None

    while True:
        c = read_code()
        if c is None:
            break
        if c == clear:
            table = {i: bytes([i]) for i in range(clear)}
            next_code = end + 1
            code_size = min_code_size + 1
            prev = None
            continue
        if c == end:
            break
        if c in table:
            entry = table[c]
        elif c == next_code and prev is not None:
            entry = prev + prev[:1]
        else:
            raise ValueError("broken GIF LZW stream")

        out.extend(entry)
        if prev is not None:
            if next_code < 4096:
                table[next_code] = prev + entry[:1]
                next_code += 1
                if next_code == (1 << code_size) and code_size < 12:
                    code_size += 1
        prev = entry
    return bytes(out)


def gif_frames_index(path: Path) -> list[dict[str, Any]]:
    b = path.read_bytes()
    if not (b.startswith(b"GIF87a") or b.startswith(b"GIF89a")):
        raise ValueError("not a GIF file")
    i = 6
    _w, _h, packed, _bg, _aspect = struct.unpack("<HHBBB", b[i : i + 7])
    i += 7
    gct_flag = (packed >> 7) & 1
    gct_size = 2 ** ((packed & 0x07) + 1) if gct_flag else 0
    if gct_flag:
        i += 3 * gct_size

    frames: list[dict[str, Any]] = []
    cur_delay = 0

    while i < len(b):
        block = b[i]
        i += 1
        if block == 0x3B:  # trailer
            break
        if block == 0x21:  # extension
            label = b[i]
            i += 1
            if label == 0xF9:  # GCE
                sz = b[i]
                i += 1
                if sz != 4:
                    raise ValueError("unexpected GCE size")
                _packed = b[i]
                delay = struct.unpack("<H", b[i + 1 : i + 3])[0]
                _tr = b[i + 3]
                i += 4
                _term = b[i]
                i += 1
                cur_delay = int(delay)
            else:
                # generic sub-blocks
                while True:
                    sz = b[i]
                    i += 1
                    if sz == 0:
                        break
                    i += sz
            continue
        if block == 0x2C:  # image descriptor
            left, top, w, h, ipacked = struct.unpack("<HHHHB", b[i : i + 9])
            i += 9
            lct_flag = (ipacked >> 7) & 1
            interlace = (ipacked >> 6) & 1
            lct_size = 2 ** ((ipacked & 0x07) + 1) if lct_flag else 0
            if lct_flag:
                i += 3 * lct_size
            min_code_size = b[i]
            i += 1
            data = bytearray()
            while True:
                sz = b[i]
                i += 1
                if sz == 0:
                    break
                data.extend(b[i : i + sz])
                i += sz
            idx = gif_lzw_decode(min_code_size, bytes(data))
            frames.append(
                {
                    "left": int(left),
                    "top": int(top),
                    "width": int(w),
                    "height": int(h),
                    "interlace": int(interlace),
                    "delay": int(cur_delay),
                    "index": idx,
                }
            )
            cur_delay = 0
            continue
        raise ValueError(f"unknown GIF block marker: 0x{block:02x}")

    return frames


def gif_frame_blocks(path: Path) -> list[tuple[int, int, int, int, int, int, bytes]]:
    """Parse GIF image blocks without LZW decode.

    Returns tuples of:
    (left, top, width, height, delay_cs, lzw_min_code_size, compressed_data)
    """
    b = path.read_bytes()
    if not (b.startswith(b"GIF87a") or b.startswith(b"GIF89a")):
        raise ValueError("not a GIF file")
    i = 6
    _w, _h, packed, _bg, _aspect = struct.unpack("<HHBBB", b[i : i + 7])
    i += 7
    gct_flag = (packed >> 7) & 1
    gct_size = 2 ** ((packed & 0x07) + 1) if gct_flag else 0
    if gct_flag:
        i += 3 * gct_size

    out: list[tuple[int, int, int, int, int, int, bytes]] = []
    cur_delay = 0
    while i < len(b):
        block = b[i]
        i += 1
        if block == 0x3B:
            break
        if block == 0x21:
            label = b[i]
            i += 1
            if label == 0xF9:
                sz = b[i]
                i += 1
                if sz != 4:
                    raise ValueError("unexpected GCE size")
                _packed = b[i]
                delay = struct.unpack("<H", b[i + 1 : i + 3])[0]
                _tr = b[i + 3]
                i += 4
                _term = b[i]
                i += 1
                cur_delay = int(delay)
            else:
                while True:
                    sz = b[i]
                    i += 1
                    if sz == 0:
                        break
                    i += sz
            continue
        if block == 0x2C:
            left, top, w, h, ipacked = struct.unpack("<HHHHB", b[i : i + 9])
            i += 9
            lct_flag = (ipacked >> 7) & 1
            lct_size = 2 ** ((ipacked & 0x07) + 1) if lct_flag else 0
            if lct_flag:
                i += 3 * lct_size
            min_code_size = int(b[i])
            i += 1
            data = bytearray()
            while True:
                sz = b[i]
                i += 1
                if sz == 0:
                    break
                data.extend(b[i : i + sz])
                i += sz
            out.append((int(left), int(top), int(w), int(h), int(cur_delay), min_code_size, bytes(data)))
            cur_delay = 0
            continue
        raise ValueError(f"unknown GIF block marker: 0x{block:02x}")
    return out


def compare_images(py_img: Path, cpp_img: Path) -> tuple[bool, str]:
    ext = py_img.suffix.lower()
    if ext != cpp_img.suffix.lower():
        return False, f"suffix mismatch: {py_img.suffix} vs {cpp_img.suffix}"
    if ext == ".png":
        pw, ph, pr = png_raw_rgb(py_img)
        cw, ch, cr = png_raw_rgb(cpp_img)
        if pw != cw or ph != ch:
            return False, f"png size differ: {pw}x{ph} vs {cw}x{ch}"
        if pr == cr:
            return True, "png raw equal"
        stride = pw * 3
        diff_at = -1
        for i, (a, b) in enumerate(zip(pr, cr)):
            if a != b:
                diff_at = i
                break
        if diff_at < 0:
            return False, "png raw differ (unknown position)"
        y, rem = divmod(diff_at, stride)
        x, ch_idx = divmod(rem, 3)
        ch_name = ("R", "G", "B")[ch_idx]
        return False, f"png raw differ at x={x}, y={y}, ch={ch_name}, py={pr[diff_at]}, cpp={cr[diff_at]}, expr=n/a"
    if ext == ".gif":
        # Fast path: if all GIF frame blocks (including compressed payload) match,
        # decompressed frame indices are guaranteed to match as well.
        pb = gif_frame_blocks(py_img)
        cb = gif_frame_blocks(cpp_img)
        if pb == cb:
            return True, "gif frame blocks equal (compressed + delay)"

        pf = gif_frames_index(py_img)
        cf = gif_frames_index(cpp_img)
        if len(pf) != len(cf):
            return False, f"gif frame count differ: {len(pf)} vs {len(cf)}"
        for i, (a, b) in enumerate(zip(pf, cf)):
            if (
                a["left"] != b["left"]
                or a["top"] != b["top"]
                or a["width"] != b["width"]
                or a["height"] != b["height"]
                or a["delay"] != b["delay"]
            ):
                return False, f"gif frame differ at index {i}"
            if a["index"] != b["index"]:
                diff_at = -1
                for j, (va, vb) in enumerate(zip(a["index"], b["index"])):
                    if va != vb:
                        diff_at = j
                        break
                if diff_at < 0:
                    return False, f"gif frame differ at index {i} (index payload length mismatch)"
                x = diff_at % a["width"]
                y = diff_at // a["width"]
                return (
                    False,
                    f"gif frame differ at frame={i}, x={x}, y={y}, py_idx={a['index'][diff_at]}, cpp_idx={b['index'][diff_at]}, expr=n/a",
                )
        return True, "gif frames equal"
    # fallback: non-image outputs
    return (py_img.read_bytes() == cpp_img.read_bytes(), "binary equal")


def verify_case(stem: str, *, work: Path, compile_flags: list[str], ignore_stdout: bool = False) -> CaseResult:
    import time
    py = Path("sample/py") / f"{stem}.py"
    cpp = Path("sample/cpp") / f"{stem}.cpp"
    exe = work / f"{stem}.out"

    t0 = time.time()
    vlog(f"[{stem}] python run start")
    rc, py_stdout = run_cmd(["python3", str(py)], env={**os.environ, "PYTHONPATH": "src"})
    vlog(f"[{stem}] python run done ({time.time()-t0:.2f}s)")
    if rc != 0:
        return CaseResult(stem, False, False, False, "python run failed")
    py_out = parse_output_path(py_stdout)

    t1 = time.time()
    vlog(f"[{stem}] cpp compile start")
    rc, _ = run_cmd(
        [
            "g++",
            "-std=c++20",
            *compile_flags,
            "-I",
            "src",
            str(cpp),
            "src/runtime/cpp/pylib/png.cpp",
            "src/runtime/cpp/pylib/gif.cpp",
            "src/runtime/cpp/core/math.cpp",
            "-o",
            str(exe),
        ]
    )
    vlog(f"[{stem}] cpp compile done ({time.time()-t1:.2f}s)")
    if rc != 0:
        return CaseResult(stem, False, False, False, "cpp compile failed")
    t2 = time.time()
    vlog(f"[{stem}] cpp run start")
    rc, cpp_stdout = run_cmd([str(exe)])
    vlog(f"[{stem}] cpp run done ({time.time()-t2:.2f}s)")
    if rc != 0:
        return CaseResult(stem, False, False, False, "cpp run failed")

    cpp_out = parse_output_path(cpp_stdout)

    stdout_ok = True if ignore_stdout else (py_stdout == cpp_stdout)
    image_ok = True
    msg = "no image output"
    if py_out is None and cpp_out is None:
        image_ok = True
    elif py_out is None or cpp_out is None:
        image_ok = False
        msg = "output path presence mismatch"
    else:
        t3 = time.time()
        vlog(f"[{stem}] image compare start")
        py_img = work / f"{stem}.py{Path(py_out).suffix.lower()}"
        cpp_img = work / f"{stem}.cpp{Path(cpp_out).suffix.lower()}"
        shutil.copyfile(py_out, py_img)
        shutil.copyfile(cpp_out, cpp_img)
        image_ok, msg = compare_images(py_img, cpp_img)
        vlog(f"[{stem}] image compare done ({time.time()-t3:.2f}s)")
    ok = stdout_ok and image_ok
    detail = [f"stdout={'skip' if ignore_stdout else ('ok' if stdout_ok else 'diff')}", f"image={'ok' if image_ok else 'diff'}", msg]
    return CaseResult(stem, ok, stdout_ok, image_ok, ", ".join(detail))


def main() -> int:
    ap = argparse.ArgumentParser(description="Verify sample/py vs transpiled C++ outputs")
    ap.add_argument("--samples", nargs="*", default=None, help="sample stems (e.g. 01_mandelbrot)")
    ap.add_argument("--compile-flags", default="-O2", help="extra g++ compile flags (space-separated)")
    ap.add_argument("--verbose", action="store_true", help="print phase timings")
    ap.add_argument("--ignore-stdout", action="store_true", help="judge only image parity and ignore stdout differences")
    args = ap.parse_args()
    global VERBOSE
    VERBOSE = args.verbose

    if args.samples is None:
        stems = [p.stem for p in sorted(Path("sample/py").glob("*.py"))]
    else:
        stems = args.samples

    compile_flags = [x for x in args.compile_flags.split(" ") if x]

    work = Path(tempfile.mkdtemp(prefix="pytra_verify_sample_"))
    print(f"work={work}")

    ok = 0
    ng = 0
    for stem in stems:
        r = verify_case(stem, work=work, compile_flags=compile_flags, ignore_stdout=args.ignore_stdout)
        if r.ok:
            ok += 1
            status = "OK"
        else:
            ng += 1
            status = "NG"
        print(f"{status} {stem}: {r.message}")

    print(f"SUMMARY OK={ok} NG={ng}")
    return 0 if ng == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
