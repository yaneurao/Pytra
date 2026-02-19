#!/usr/bin/env python3
"""Generate C++ pylib runtime files from src/pylib/tra/*.py."""

from __future__ import annotations

import argparse
import subprocess
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

PNG_SOURCE = "src/pylib/tra/png.py"
GIF_SOURCE = "src/pylib/tra/gif.py"


def _namespace_parts_from_source(source_rel: str) -> list[str]:
    """`src/.../*.py` から C++ namespace 用パーツを抽出する。"""
    p = Path(source_rel)
    parts = list(p.parts)
    if len(parts) < 3:
        raise ValueError(f"invalid source path: {source_rel}")
    if parts[0] != "src":
        raise ValueError(f"source path must start with src/: {source_rel}")
    if p.suffix != ".py":
        raise ValueError(f"source path must be .py: {source_rel}")
    out = parts[1:-1] + [p.stem]
    if len(out) == 0:
        raise ValueError(f"empty namespace parts from source: {source_rel}")
    return out


def _cpp_namespace_from_source(source_rel: str) -> str:
    """`src/pylib/tra/gif.py` -> `pytra::pylib::tra::gif` を返す。"""
    return "pytra::" + "::".join(_namespace_parts_from_source(source_rel))


def _cpp_alias_target_from_source(source_rel: str) -> str:
    """`namespace pytra { namespace x = ...; }` 用の右辺を返す。"""
    return "::".join(_namespace_parts_from_source(source_rel))


def _png_header_text(namespace_cpp: str, alias_target: str) -> str:
    return f"""// AUTO-GENERATED FILE. DO NOT EDIT.
// command: python3 tools/generate_cpp_pylib_runtime.py

#ifndef PYTRA_CPP_MODULE_PNG_H
#define PYTRA_CPP_MODULE_PNG_H

#include <cstdint>
#include <string>
#include <vector>

namespace {namespace_cpp} {{

void write_rgb_png(const std::string& path, int width, int height, const std::vector<std::uint8_t>& pixels);

}}  // namespace {namespace_cpp}

namespace pytra {{
namespace png = {alias_target};
}}

#endif  // PYTRA_CPP_MODULE_PNG_H
"""


def _gif_header_text(namespace_cpp: str, alias_target: str) -> str:
    return f"""// AUTO-GENERATED FILE. DO NOT EDIT.
// command: python3 tools/generate_cpp_pylib_runtime.py

#ifndef PYTRA_CPP_MODULE_GIF_H
#define PYTRA_CPP_MODULE_GIF_H

#include <cstdint>
#include <string>
#include <vector>

namespace {namespace_cpp} {{

std::vector<std::uint8_t> grayscale_palette();

void save_gif(
    const std::string& path,
    int width,
    int height,
    const std::vector<std::vector<std::uint8_t>>& frames,
    const std::vector<std::uint8_t>& palette,
    int delay_cs = 4,
    int loop = 0
);

}}  // namespace {namespace_cpp}

namespace pytra {{
namespace gif = {alias_target};
}}

#endif  // PYTRA_CPP_MODULE_GIF_H
"""


def _png_wrapper_text(namespace_cpp: str) -> str:
    return f"""// AUTO-GENERATED FILE. DO NOT EDIT.
// command: python3 tools/generate_cpp_pylib_runtime.py

#include \"runtime/cpp/pytra/runtime/png.h\"

#include \"runtime/cpp/py_runtime.h\"

namespace {namespace_cpp} {{
namespace generated {{
__PYTRA_PNG_IMPL__
}}  // namespace generated

void write_rgb_png(const std::string& path, int width, int height, const std::vector<std::uint8_t>& pixels) {{
    const bytes raw(pixels.begin(), pixels.end());
    generated::write_rgb_png(str(path), int64(width), int64(height), raw);
}}

}}  // namespace {namespace_cpp}
"""


def _gif_wrapper_text(namespace_cpp: str) -> str:
    return f"""// AUTO-GENERATED FILE. DO NOT EDIT.
// command: python3 tools/generate_cpp_pylib_runtime.py

#include \"runtime/cpp/pytra/runtime/gif.h\"

#include \"runtime/cpp/py_runtime.h\"

namespace {namespace_cpp} {{
namespace generated {{
__PYTRA_GIF_IMPL__
}}  // namespace generated

std::vector<std::uint8_t> grayscale_palette() {{
    const bytes raw = generated::grayscale_palette();
    return std::vector<std::uint8_t>(raw.begin(), raw.end());
}}

void save_gif(
    const std::string& path,
    int width,
    int height,
    const std::vector<std::vector<std::uint8_t>>& frames,
    const std::vector<std::uint8_t>& palette,
    int delay_cs,
    int loop
) {{
    list<bytes> frame_list{{}};
    frame_list.reserve(frames.size());
    for (const auto& fr : frames) {{
        frame_list.append(bytes(fr.begin(), fr.end()));
    }}
    const bytes pal_bytes(palette.begin(), palette.end());
    generated::save_gif(
        str(path),
        int64(width),
        int64(height),
        frame_list,
        pal_bytes,
        int64(delay_cs),
        int64(loop)
    );
}}

}}  // namespace {namespace_cpp}
"""


def transpile_to_cpp(source_rel: str) -> str:
    source = ROOT / source_rel
    with tempfile.TemporaryDirectory() as tmp:
        out_cpp = Path(tmp) / "out.cpp"
        cmd = ["python3", "src/py2cpp.py", str(source), "--no-main", "-o", str(out_cpp)]
        p = subprocess.run(cmd, cwd=str(ROOT), capture_output=True, text=True)
        if p.returncode != 0:
            raise RuntimeError(f"failed: {' '.join(cmd)}\\n{p.stderr}")
        return out_cpp.read_text(encoding="utf-8")


def normalize_generated_impl_text(text: str, source_rel: str) -> str:
    banner = (
        "// AUTO-GENERATED FILE. DO NOT EDIT.\n"
        f"// source: {source_rel}\n"
        "// command: python3 tools/generate_cpp_pylib_runtime.py\n\n"
    )
    return banner + text.rstrip() + "\n"


def _strip_runtime_include(text: str) -> str:
    lines = text.splitlines()
    out: list[str] = []
    for ln in lines:
        if ln.strip() == '#include "runtime/cpp/py_runtime.h"':
            continue
        out.append(ln)
    return "\n".join(out).strip() + "\n"


def write_or_check(target_rel: str, text: str, check: bool) -> bool:
    target = ROOT / target_rel
    target.parent.mkdir(parents=True, exist_ok=True)
    current = target.read_text(encoding="utf-8") if target.exists() else ""
    if current == text:
        return False
    if check:
        print(f"[DIFF] {target_rel}")
        return True
    target.write_text(text, encoding="utf-8")
    print(f"[WRITE] {target_rel}")
    return True


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true", help="only check generated files are up-to-date")
    args = ap.parse_args()

    changed = False

    png_ns = _cpp_namespace_from_source(PNG_SOURCE)
    gif_ns = _cpp_namespace_from_source(GIF_SOURCE)
    png_alias = _cpp_alias_target_from_source(PNG_SOURCE)
    gif_alias = _cpp_alias_target_from_source(GIF_SOURCE)

    raw_png = transpile_to_cpp(PNG_SOURCE)
    raw_gif = transpile_to_cpp(GIF_SOURCE)
    png_impl = normalize_generated_impl_text(raw_png, PNG_SOURCE)
    gif_impl = normalize_generated_impl_text(raw_gif, GIF_SOURCE)
    png_cpp = _png_wrapper_text(png_ns).replace("__PYTRA_PNG_IMPL__", _strip_runtime_include(png_impl).rstrip())
    gif_cpp = _gif_wrapper_text(gif_ns).replace("__PYTRA_GIF_IMPL__", _strip_runtime_include(gif_impl).rstrip())
    outputs: list[tuple[str, str]] = [
        ("src/runtime/cpp/pytra/runtime/png.h", _png_header_text(png_ns, png_alias)),
        ("src/runtime/cpp/pytra/runtime/gif.h", _gif_header_text(gif_ns, gif_alias)),
        ("src/runtime/cpp/pytra/runtime/png.cpp", png_cpp),
        ("src/runtime/cpp/pytra/runtime/gif.cpp", gif_cpp),
    ]
    for target_rel, text in outputs:
        if write_or_check(target_rel, text.rstrip() + "\n", args.check):
            changed = True

    if args.check and changed:
        print("[FAIL] generated cpp pylib files are stale")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
