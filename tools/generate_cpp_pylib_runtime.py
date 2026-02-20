#!/usr/bin/env python3
"""Generate C++ runtime files from src/pytra/runtime/**/*.py."""

from __future__ import annotations

import argparse
import os
import subprocess
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

PNG_SOURCE = "src/pytra/runtime/png.py"
GIF_SOURCE = "src/pytra/runtime/gif.py"
ASSERTIONS_SOURCE = "src/pytra/runtime/assertions.py"
EAST_SOURCE = "src/pytra/runtime/east.py"
STD_TIME_SOURCE = "src/pytra/runtime/std/time.py"
STD_PATHLIB_SOURCE = "src/pytra/runtime/std/pathlib.py"
STD_DATACLASSES_SOURCE = "src/pytra/runtime/std/dataclasses.py"
STD_SYS_SOURCE = "src/pytra/runtime/std/sys.py"
STD_JSON_SOURCE = "src/pytra/runtime/std/json.py"
STD_TYPING_SOURCE = "src/pytra/runtime/std/typing.py"


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
    """`src/pytra/runtime/gif.py` -> `pytra::runtime::gif` を返す。"""
    parts = _namespace_parts_from_source(source_rel)
    return "::".join(parts)


def _cpp_alias_target_from_source(source_rel: str) -> str:
    """`namespace pytra { namespace x = ...; }` 用の右辺を返す。"""
    parts = _namespace_parts_from_source(source_rel)
    if len(parts) >= 2 and parts[0] == "pytra":
        return "::".join(parts[1:])
    return "::".join(parts)


def _png_header_text(namespace_cpp: str, alias_target: str) -> str:
    return f"""// AUTO-GENERATED FILE. DO NOT EDIT.
// command: python3 tools/generate_cpp_pylib_runtime.py

#ifndef PYTRA_CPP_MODULE_PNG_H
#define PYTRA_CPP_MODULE_PNG_H

#include <cstdint>
#include <string>
#include <vector>

class str;
template <class T>
class list;

namespace {namespace_cpp} {{

void write_rgb_png(const std::string& path, int width, int height, const std::vector<std::uint8_t>& pixels);
void write_rgb_png_py(
    const str& path,
    std::int64_t width,
    std::int64_t height,
    const list<std::uint8_t>& pixels
);

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

class str;
template <class T>
class list;

namespace {namespace_cpp} {{

std::vector<std::uint8_t> grayscale_palette();
list<std::uint8_t> grayscale_palette_py();

void save_gif(
    const std::string& path,
    int width,
    int height,
    const std::vector<std::vector<std::uint8_t>>& frames,
    const std::vector<std::uint8_t>& palette,
    int delay_cs = 4,
    int loop = 0
);
void save_gif_py(
    const str& path,
    std::int64_t width,
    std::int64_t height,
    const list<list<std::uint8_t>>& frames,
    const list<std::uint8_t>& palette,
    std::int64_t delay_cs = 4,
    std::int64_t loop = 0
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

void write_rgb_png_py(
    const str& path,
    std::int64_t width,
    std::int64_t height,
    const list<std::uint8_t>& pixels
) {{
    generated::write_rgb_png(path, int64(width), int64(height), pixels);
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

list<std::uint8_t> grayscale_palette_py() {{
    return generated::grayscale_palette();
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

void save_gif_py(
    const str& path,
    std::int64_t width,
    std::int64_t height,
    const list<list<std::uint8_t>>& frames,
    const list<std::uint8_t>& palette,
    std::int64_t delay_cs,
    std::int64_t loop
) {{
    generated::save_gif(path, int64(width), int64(height), frames, palette, int64(delay_cs), int64(loop));
}}

}}  // namespace {namespace_cpp}
"""


def _runtime_assertions_header_text() -> str:
    return f"""// AUTO-GENERATED FILE. DO NOT EDIT.
// source: {ASSERTIONS_SOURCE}
// command: python3 tools/generate_cpp_pylib_runtime.py

#ifndef PYTRA_RUNTIME_CPP_PYTRA_RUNTIME_ASSERTIONS_H
#define PYTRA_RUNTIME_CPP_PYTRA_RUNTIME_ASSERTIONS_H

// assertion helpers are provided by runtime/cpp/py_runtime.h

#endif
"""


def _runtime_east_header_text() -> str:
    return f"""// AUTO-GENERATED FILE. DO NOT EDIT.
// source: {EAST_SOURCE}
// command: python3 tools/generate_cpp_pylib_runtime.py

#ifndef PYTRA_RUNTIME_CPP_PYTRA_RUNTIME_EAST_H
#define PYTRA_RUNTIME_CPP_PYTRA_RUNTIME_EAST_H

// EAST parser/runtime bridge is not linked in current selfhost stage.

#endif
"""


def _std_json_header_text() -> str:
    return f"""// AUTO-GENERATED FILE. DO NOT EDIT.
// source: {STD_JSON_SOURCE}
// command: python3 tools/generate_cpp_pylib_runtime.py

#ifndef PYTRA_RUNTIME_CPP_PYTRA_STD_JSON_H
#define PYTRA_RUNTIME_CPP_PYTRA_STD_JSON_H

// json runtime functions are provided via py_runtime helpers in current backend.

#endif
"""


def _std_typing_header_text() -> str:
    return f"""// AUTO-GENERATED FILE. DO NOT EDIT.
// source: {STD_TYPING_SOURCE}
// command: python3 tools/generate_cpp_pylib_runtime.py

#ifndef PYTRA_RUNTIME_CPP_PYTRA_STD_TYPING_H
#define PYTRA_RUNTIME_CPP_PYTRA_STD_TYPING_H

// typing symbols are compile-time only in py2cpp output.

#endif
"""


def _extract_numeric_functions_from_transpiled(cpp_text: str) -> list[tuple[str, list[str]]]:
    funcs: list[tuple[str, list[str]]] = []
    for raw in cpp_text.splitlines():
        ln = raw.strip()
        if not ln.startswith("float64 "):
            continue
        if not ln.endswith("{"):
            continue
        head = ln[: len(ln) - 1].strip()
        p0 = head.find("(")
        p1 = head.rfind(")")
        if p0 < 0 or p1 < p0:
            continue
        sig = head[:p0].strip()
        args_txt = head[p0 + 1 : p1].strip()
        sig_parts = sig.split(" ")
        if len(sig_parts) < 2:
            continue
        fn_name = sig_parts[-1].strip()
        params: list[str] = []
        if args_txt != "":
            for tok in args_txt.split(","):
                part = tok.strip()
                if part == "":
                    continue
                items = part.split(" ")
                params.append(items[-1].strip())
        funcs.append((fn_name, params))
    return funcs


def _extract_numeric_constants_from_transpiled(cpp_text: str) -> list[tuple[str, str]]:
    out: list[tuple[str, str]] = []
    for raw in cpp_text.splitlines():
        ln = raw.strip()
        if not ln.startswith("std::any "):
            continue
        eq = ln.find("= make_object(")
        if eq < 0:
            continue
        tail = ln[eq + len("= make_object(") :]
        if not tail.endswith(");"):
            continue
        name = ln[len("std::any ") : eq].strip()
        expr = tail[: len(tail) - 2].strip()
        if name == "" or expr == "":
            continue
        out.append((name, expr))
    return out


def _header_guard_from_target(target_h_rel: str) -> str:
    txt = target_h_rel.upper().replace("/", "_").replace(".", "_")
    return txt


def _std_numeric_header_text(
    source_rel: str,
    target_h_rel: str,
    module_name: str,
    funcs: list[tuple[str, list[str]]],
    consts: list[tuple[str, str]],
) -> str:
    guard = _header_guard_from_target(target_h_rel)
    lines: list[str] = []
    lines.append("// AUTO-GENERATED FILE. DO NOT EDIT.")
    lines.append(f"// source: {source_rel}")
    lines.append("// generated-by: src/py2cpp.py")
    lines.append("// command: python3 tools/generate_cpp_pylib_runtime.py")
    lines.append("")
    lines.append(f"#ifndef {guard}")
    lines.append(f"#define {guard}")
    lines.append("")
    lines.append("#include <any>")
    lines.append("")
    lines.append(f"namespace pytra::core::{module_name} {{")
    lines.append("")
    for fn_name, params in funcs:
        ds = ", ".join([f"double {p}" for p in params])
        lines.append(f"double {fn_name}({ds});")
    for fn_name, params in funcs:
        if len(params) == 1:
            lines.append(f"double {fn_name}(const std::any& x);")
        elif len(params) == 2:
            lines.append(f"double {fn_name}(const std::any& x, const std::any& y);")
    for name, _expr in consts:
        lines.append(f"extern const double {name};")
    lines.append("")
    lines.append(f"}}  // namespace pytra::core::{module_name}")
    lines.append("")
    lines.append("namespace pytra {")
    lines.append(f"namespace {module_name} = core::{module_name};")
    lines.append("}")
    lines.append("")
    lines.append(f"#endif  // {guard}")
    lines.append("")
    return "\n".join(lines)


def _std_numeric_cpp_text(
    source_rel: str,
    target_h_rel: str,
    module_name: str,
    funcs: list[tuple[str, list[str]]],
    consts: list[tuple[str, str]],
) -> str:
    lines: list[str] = []
    lines.append("// AUTO-GENERATED FILE. DO NOT EDIT.")
    lines.append(f"// source: {source_rel}")
    lines.append("// generated-by: src/py2cpp.py")
    lines.append("// command: python3 tools/generate_cpp_pylib_runtime.py")
    lines.append("")
    lines.append("#include <cmath>")
    lines.append("")
    lines.append(f'#include "{target_h_rel.replace("src/", "")}"')
    lines.append("")
    lines.append(f"namespace pytra::core::{module_name} {{")
    lines.append("")
    lines.append("static double any_to_double(const std::any& v) {")
    lines.append("    if (const auto* p = std::any_cast<double>(&v)) return *p;")
    lines.append("    if (const auto* p = std::any_cast<float>(&v)) return static_cast<double>(*p);")
    lines.append("    if (const auto* p = std::any_cast<long long>(&v)) return static_cast<double>(*p);")
    lines.append("    if (const auto* p = std::any_cast<unsigned long long>(&v)) return static_cast<double>(*p);")
    lines.append("    if (const auto* p = std::any_cast<long>(&v)) return static_cast<double>(*p);")
    lines.append("    if (const auto* p = std::any_cast<unsigned long>(&v)) return static_cast<double>(*p);")
    lines.append("    if (const auto* p = std::any_cast<int>(&v)) return static_cast<double>(*p);")
    lines.append("    if (const auto* p = std::any_cast<unsigned>(&v)) return static_cast<double>(*p);")
    lines.append("    if (const auto* p = std::any_cast<bool>(&v)) return *p ? 1.0 : 0.0;")
    lines.append("    return 0.0;")
    lines.append("}")
    lines.append("")
    for name, expr in consts:
        lines.append(f"const double {name} = {expr};")
    lines.append("")
    for fn_name, params in funcs:
        ds = ", ".join([f"double {p}" for p in params])
        call_args = ", ".join(params)
        lines.append(f"double {fn_name}({ds}) {{ return std::{fn_name}({call_args}); }}")
    lines.append("")
    for fn_name, params in funcs:
        if len(params) == 1:
            lines.append(f"double {fn_name}(const std::any& x) {{ return {fn_name}(any_to_double(x)); }}")
        elif len(params) == 2:
            lines.append(f"double {fn_name}(const std::any& x, const std::any& y) {{ return {fn_name}(any_to_double(x), any_to_double(y)); }}")
    lines.append("")
    lines.append(f"}}  // namespace pytra::core::{module_name}")
    lines.append("")
    return "\n".join(lines)


def _discover_std_auto_numeric_modules() -> list[tuple[str, str, str, str]]:
    out: list[tuple[str, str, str, str]] = []
    std_dir = ROOT / "src" / "pytra" / "runtime" / "std"
    skip = {"__init__", "time", "pathlib", "dataclasses", "sys", "json", "typing"}
    for p in sorted(std_dir.glob("*.py")):
        stem = p.stem
        if stem in skip:
            continue
        src_rel = p.relative_to(ROOT).as_posix()
        h_rel = f"src/runtime/cpp/pytra/std/{stem}.h"
        cpp_rel = f"src/runtime/cpp/pytra/std/{stem}.cpp"
        out.append((src_rel, h_rel, cpp_rel, stem))
    return out

def _std_time_header_text() -> str:
    return """// AUTO-GENERATED FILE. DO NOT EDIT.
// source: src/pytra/runtime/std/time.py
// command: python3 tools/generate_cpp_pylib_runtime.py

#ifndef PYTRA_RUNTIME_CPP_PYTRA_STD_TIME_H
#define PYTRA_RUNTIME_CPP_PYTRA_STD_TIME_H

namespace pytra::cpp_module {

double perf_counter();

}  // namespace pytra::cpp_module

#endif  // PYTRA_RUNTIME_CPP_PYTRA_STD_TIME_H
"""


def _std_time_cpp_text() -> str:
    return """// AUTO-GENERATED FILE. DO NOT EDIT.
// source: src/pytra/runtime/std/time.py
// command: python3 tools/generate_cpp_pylib_runtime.py

#include <chrono>

#include "runtime/cpp/pytra/std/time.h"

namespace pytra::cpp_module {

double perf_counter() {
    using Clock = std::chrono::steady_clock;
    using Seconds = std::chrono::duration<double>;
    return Seconds(Clock::now().time_since_epoch()).count();
}

}  // namespace pytra::cpp_module
"""


def _std_dataclasses_header_text() -> str:
    return """// AUTO-GENERATED FILE. DO NOT EDIT.
// source: src/pytra/runtime/std/dataclasses.py
// command: python3 tools/generate_cpp_pylib_runtime.py

#ifndef PYTRA_RUNTIME_CPP_PYTRA_STD_DATACLASSES_H
#define PYTRA_RUNTIME_CPP_PYTRA_STD_DATACLASSES_H

#include <type_traits>

namespace pytra::cpp_module::dataclasses {

struct DataclassTag {};

template <typename T>
constexpr T dataclass(T value) {
    return value;
}

template <typename T>
constexpr bool is_dataclass_v = std::is_base_of_v<DataclassTag, T>;

}  // namespace pytra::cpp_module::dataclasses

#endif  // PYTRA_RUNTIME_CPP_PYTRA_STD_DATACLASSES_H
"""


def _std_dataclasses_cpp_text() -> str:
    return """// AUTO-GENERATED FILE. DO NOT EDIT.
// source: src/pytra/runtime/std/dataclasses.py
// command: python3 tools/generate_cpp_pylib_runtime.py

#include "runtime/cpp/pytra/std/dataclasses.h"
"""


def _std_sys_header_text() -> str:
    return """// AUTO-GENERATED FILE. DO NOT EDIT.
// source: src/pytra/runtime/std/sys.py
// command: python3 tools/generate_cpp_pylib_runtime.py

#ifndef PYTRA_RUNTIME_CPP_PYTRA_STD_SYS_H
#define PYTRA_RUNTIME_CPP_PYTRA_STD_SYS_H

#include <cstddef>
#include <string>
#include <vector>

namespace pytra::cpp_module {

class SysPath {
public:
    void insert(int index, const std::string& value);

private:
    std::vector<std::string> entries_;
};

class SysModule {
public:
    SysModule();
    ~SysModule();

    SysPath* path;
};

extern SysModule* sys;

}  // namespace pytra::cpp_module

using pytra::cpp_module::sys;

#endif  // PYTRA_RUNTIME_CPP_PYTRA_STD_SYS_H
"""


def _std_sys_cpp_text() -> str:
    return """// AUTO-GENERATED FILE. DO NOT EDIT.
// source: src/pytra/runtime/std/sys.py
// command: python3 tools/generate_cpp_pylib_runtime.py

#include "runtime/cpp/pytra/std/sys.h"

namespace pytra::cpp_module {

void SysPath::insert(int index, const std::string& value) {
    if (index < 0 || static_cast<std::size_t>(index) >= entries_.size()) {
        entries_.push_back(value);
        return;
    }
    entries_.insert(entries_.begin() + index, value);
}

SysModule::SysModule() : path(new SysPath()) {}

SysModule::~SysModule() {
    delete path;
}

SysModule* sys = new SysModule();

}  // namespace pytra::cpp_module
"""


def _std_pathlib_header_text() -> str:
    return """// AUTO-GENERATED FILE. DO NOT EDIT.
// source: src/pytra/runtime/std/pathlib.py
// command: python3 tools/generate_cpp_pylib_runtime.py

#ifndef PYTRA_RUNTIME_CPP_PYTRA_STD_PATHLIB_H
#define PYTRA_RUNTIME_CPP_PYTRA_STD_PATHLIB_H

#include <filesystem>
#include <fstream>
#include <sstream>
#include <stdexcept>
#include <string>

namespace pytra::cpp_module {

class Path;

class PathParentProxy {
public:
    explicit PathParentProxy(const Path* owner) : owner_(owner) {}
    Path* operator->() const;
    Path operator()() const;

private:
    const Path* owner_;
};

class PathParentsProxy {
public:
    explicit PathParentsProxy(const Path* owner) : owner_(owner) {}
    Path operator[](std::size_t index) const;

private:
    const Path* owner_;
};

class Path {
public:
    Path() : parent(this), parents(this) {}
    explicit Path(const std::string& value) : path_(value), parent(this), parents(this) {}
    explicit Path(const char* value) : path_(value), parent(this), parents(this) {}
    explicit Path(std::filesystem::path value)
        : path_(std::move(value)), parent(this), parents(this) {}
    Path(const Path& other) : path_(other.path_), parent(this), parents(this) {}
    Path(Path&& other) noexcept : path_(std::move(other.path_)), parent(this), parents(this) {}

    Path& operator=(const Path& other) {
        if (this != &other) {
            path_ = other.path_;
        }
        return *this;
    }

    Path& operator=(Path&& other) noexcept {
        if (this != &other) {
            path_ = std::move(other.path_);
        }
        return *this;
    }

    Path resolve() const {
        return Path(std::filesystem::absolute(path_));
    }

    bool exists() const {
        return std::filesystem::exists(path_);
    }

    Path operator/(const std::string& rhs) const {
        return Path(path_ / rhs);
    }

    Path operator/(const char* rhs) const {
        return Path(path_ / rhs);
    }

    std::string string() const {
        return path_.string();
    }

    std::string read_text(const std::string& /*encoding*/ = "utf-8") const {
        std::ifstream ifs(path_);
        if (!ifs) {
            throw std::runtime_error("read_text failed: " + path_.string());
        }
        std::ostringstream oss;
        oss << ifs.rdbuf();
        return oss.str();
    }

    void write_text(const std::string& content, const std::string& /*encoding*/ = "utf-8") const {
        std::ofstream ofs(path_);
        if (!ofs) {
            throw std::runtime_error("write_text failed: " + path_.string());
        }
        ofs << content;
    }

    void mkdir(bool parents_flag = false, bool exist_ok = false) const {
        std::error_code ec;
        if (parents_flag) {
            std::filesystem::create_directories(path_, ec);
        } else {
            std::filesystem::create_directory(path_, ec);
        }
        if (!exist_ok && ec) {
            throw std::runtime_error("mkdir failed: " + ec.message());
        }
    }

    Path* operator->() { return this; }
    const Path* operator->() const { return this; }

    std::string name() const {
        return path_.filename().string();
    }

    std::string stem() const {
        return path_.stem().string();
    }

    const std::filesystem::path& raw_path() const { return path_; }

    PathParentProxy parent;
    PathParentsProxy parents;

private:
    std::filesystem::path path_;
};

inline Path* PathParentProxy::operator->() const {
    static thread_local Path cached;
    cached = Path(owner_->raw_path().parent_path());
    return &cached;
}

inline Path PathParentProxy::operator()() const {
    return Path(owner_->raw_path().parent_path());
}

inline Path PathParentsProxy::operator[](std::size_t index) const {
    std::filesystem::path cur = owner_->raw_path();
    for (std::size_t i = 0; i <= index; ++i) {
        cur = cur.parent_path();
    }
    return Path(cur);
}

inline std::string str(const Path& p) {
    return p.string();
}

}  // namespace pytra::cpp_module

#endif  // PYTRA_RUNTIME_CPP_PYTRA_STD_PATHLIB_H
"""


def _std_pathlib_cpp_text() -> str:
    return """// AUTO-GENERATED FILE. DO NOT EDIT.
// source: src/pytra/runtime/std/pathlib.py
// command: python3 tools/generate_cpp_pylib_runtime.py

#include "runtime/cpp/pytra/std/pathlib.h"
"""


def transpile_to_cpp(source_rel: str) -> str:
    source = ROOT / source_rel
    with tempfile.TemporaryDirectory() as tmp:
        out_cpp = Path(tmp) / "out.cpp"
        cmd = ["python3", "src/py2cpp.py", str(source), "--no-main", "-o", str(out_cpp)]
        env = dict(os.environ)
        env["PYTRA_SKIP_RUNTIME_AUTOGEN"] = "1"
        p = subprocess.run(cmd, cwd=str(ROOT), capture_output=True, text=True, env=env)
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
    auto_numeric_outputs: list[tuple[str, str]] = []
    auto_numeric_mods = _discover_std_auto_numeric_modules()
    for src_rel, h_rel, cpp_rel, mod_name in auto_numeric_mods:
        raw_mod = transpile_to_cpp(src_rel)
        funcs = _extract_numeric_functions_from_transpiled(raw_mod)
        consts = _extract_numeric_constants_from_transpiled(raw_mod)
        h_txt = _std_numeric_header_text(src_rel, h_rel, mod_name, funcs, consts)
        cpp_txt = _std_numeric_cpp_text(src_rel, h_rel, mod_name, funcs, consts)
        auto_numeric_outputs.append((h_rel, h_txt))
        auto_numeric_outputs.append((cpp_rel, cpp_txt))
    outputs: list[tuple[str, str]] = [
        ("src/runtime/cpp/pytra/runtime/assertions.h", _runtime_assertions_header_text()),
        ("src/runtime/cpp/pytra/runtime/east.h", _runtime_east_header_text()),
        ("src/runtime/cpp/pytra/runtime/png.h", _png_header_text(png_ns, png_alias)),
        ("src/runtime/cpp/pytra/runtime/gif.h", _gif_header_text(gif_ns, gif_alias)),
        ("src/runtime/cpp/pytra/runtime/png.cpp", png_cpp),
        ("src/runtime/cpp/pytra/runtime/gif.cpp", gif_cpp),
        ("src/runtime/cpp/pytra/std/json.h", _std_json_header_text()),
        ("src/runtime/cpp/pytra/std/typing.h", _std_typing_header_text()),
        ("src/runtime/cpp/pytra/std/time.h", _std_time_header_text()),
        ("src/runtime/cpp/pytra/std/time.cpp", _std_time_cpp_text()),
        ("src/runtime/cpp/pytra/std/dataclasses.h", _std_dataclasses_header_text()),
        ("src/runtime/cpp/pytra/std/dataclasses.cpp", _std_dataclasses_cpp_text()),
        ("src/runtime/cpp/pytra/std/sys.h", _std_sys_header_text()),
        ("src/runtime/cpp/pytra/std/sys.cpp", _std_sys_cpp_text()),
        ("src/runtime/cpp/pytra/std/pathlib.h", _std_pathlib_header_text()),
        ("src/runtime/cpp/pytra/std/pathlib.cpp", _std_pathlib_cpp_text()),
    ]
    outputs.extend(auto_numeric_outputs)
    for target_rel, text in outputs:
        if write_or_check(target_rel, text.rstrip() + "\n", args.check):
            changed = True

    if args.check and changed:
        print("[FAIL] generated cpp pylib files are stale")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
