"""Helpers for writing JS runtime shim modules next to transpiled outputs."""

from __future__ import annotations

from pytra.std.pathlib import Path


def write_js_runtime_shims(output_dir: Path) -> None:
    """Write CommonJS shims expected by JS/TS transpiled imports.

    Generated JS/TS currently imports runtime modules under `./pytra/...`.
    These shims forward to runtime implementations in `src/runtime/js/pytra`.
    """
    files: dict[str, str] = {
        "pytra/std/time.js": (
            "const rt = require(process.cwd() + '/src/runtime/js/pytra/time.js');\n"
            "const perf_counter = typeof rt.perf_counter === 'function' ? rt.perf_counter : rt.perfCounter;\n"
            "exports.perf_counter = perf_counter;\n"
            "exports.perfCounter = perf_counter;\n"
        ),
        "pytra/std/math.js": (
            "const rt = require(process.cwd() + '/src/runtime/js/pytra/math.js');\n"
            "exports.pi = rt.pi;\n"
            "exports.e = rt.e;\n"
            "exports.sin = rt.sin;\n"
            "exports.cos = rt.cos;\n"
            "exports.tan = rt.tan;\n"
            "exports.sqrt = rt.sqrt;\n"
            "exports.exp = rt.exp;\n"
            "exports.log = rt.log;\n"
            "exports.log10 = rt.log10;\n"
            "exports.fabs = rt.fabs;\n"
            "exports.floor = rt.floor;\n"
            "exports.ceil = rt.ceil;\n"
            "exports.pow = rt.pow;\n"
        ),
        "pytra/std/pathlib.js": (
            "const rt = require(process.cwd() + '/src/runtime/js/pytra/pathlib.js');\n"
            "exports.Path = rt.Path;\n"
            "exports.pathJoin = rt.pathJoin;\n"
        ),
        "pytra/runtime.js": (
            "const png = require(process.cwd() + '/src/runtime/js/pytra/png_helper.js');\n"
            "const gif = require(process.cwd() + '/src/runtime/js/pytra/gif_helper.js');\n"
            "exports.png = png;\n"
            "exports.gif = gif;\n"
        ),
        "pytra/runtime/png.js": (
            "const rt = require(process.cwd() + '/src/runtime/js/pytra/png_helper.js');\n"
            "exports.write_rgb_png = rt.write_rgb_png;\n"
        ),
        "pytra/runtime/gif.js": (
            "const rt = require(process.cwd() + '/src/runtime/js/pytra/gif_helper.js');\n"
            "exports.grayscale_palette = rt.grayscale_palette;\n"
            "exports.save_gif = rt.save_gif;\n"
        ),
        "pytra/py_runtime.js": (
            "const rt = require(process.cwd() + '/src/runtime/js/pytra/py_runtime.js');\n"
            "exports.PY_TYPE_NONE = rt.PY_TYPE_NONE;\n"
            "exports.PY_TYPE_BOOL = rt.PY_TYPE_BOOL;\n"
            "exports.PY_TYPE_NUMBER = rt.PY_TYPE_NUMBER;\n"
            "exports.PY_TYPE_STRING = rt.PY_TYPE_STRING;\n"
            "exports.PY_TYPE_ARRAY = rt.PY_TYPE_ARRAY;\n"
            "exports.PY_TYPE_MAP = rt.PY_TYPE_MAP;\n"
            "exports.PY_TYPE_SET = rt.PY_TYPE_SET;\n"
            "exports.PY_TYPE_OBJECT = rt.PY_TYPE_OBJECT;\n"
            "exports.PYTRA_TYPE_ID = rt.PYTRA_TYPE_ID;\n"
            "exports.PYTRA_TRUTHY = rt.PYTRA_TRUTHY;\n"
            "exports.PYTRA_TRY_LEN = rt.PYTRA_TRY_LEN;\n"
            "exports.PYTRA_STR = rt.PYTRA_STR;\n"
            "exports.pyRegisterType = rt.pyRegisterType;\n"
            "exports.pyRegisterClassType = rt.pyRegisterClassType;\n"
            "exports.pyIsSubtype = rt.pyIsSubtype;\n"
            "exports.pyIsInstance = rt.pyIsInstance;\n"
            "exports.pyTypeId = rt.pyTypeId;\n"
            "exports.pyTruthy = rt.pyTruthy;\n"
            "exports.pyTryLen = rt.pyTryLen;\n"
            "exports.pyStr = rt.pyStr;\n"
            "exports.pyToString = rt.pyToString;\n"
            "exports.pyPrint = rt.pyPrint;\n"
            "exports.pyLen = rt.pyLen;\n"
            "exports.pyBool = rt.pyBool;\n"
            "exports.pyRange = rt.pyRange;\n"
            "exports.pyFloorDiv = rt.pyFloorDiv;\n"
            "exports.pyMod = rt.pyMod;\n"
            "exports.pyIn = rt.pyIn;\n"
            "exports.pySlice = rt.pySlice;\n"
            "exports.pyOrd = rt.pyOrd;\n"
            "exports.pyChr = rt.pyChr;\n"
            "exports.pyBytearray = rt.pyBytearray;\n"
            "exports.pyBytes = rt.pyBytes;\n"
            "exports.pyIsDigit = rt.pyIsDigit;\n"
            "exports.pyIsAlpha = rt.pyIsAlpha;\n"
        ),
        "pytra/utils.js": (
            "const png = require(process.cwd() + '/src/runtime/js/pytra/png_helper.js');\n"
            "const gif = require(process.cwd() + '/src/runtime/js/pytra/gif_helper.js');\n"
            "exports.png = png;\n"
            "exports.gif = gif;\n"
        ),
        "pytra/utils/png.js": (
            "const rt = require(process.cwd() + '/src/runtime/js/pytra/png_helper.js');\n"
            "exports.write_rgb_png = rt.write_rgb_png;\n"
        ),
        "pytra/utils/gif.js": (
            "const rt = require(process.cwd() + '/src/runtime/js/pytra/gif_helper.js');\n"
            "exports.grayscale_palette = rt.grayscale_palette;\n"
            "exports.save_gif = rt.save_gif;\n"
        ),
        "pytra/utils/assertions.js": (
            "exports.py_assert_true = function(cond, _label) { return !!cond; };\n"
            "exports.py_assert_eq = function(actual, expected, _label) { return actual === expected; };\n"
            "exports.py_assert_all = function(results, _label) {\n"
            "  if (!Array.isArray(results)) return false;\n"
            "  for (const v of results) { if (!v) return false; }\n"
            "  return true;\n"
            "};\n"
            "exports.py_assert_stdout = function(_expected_lines, fn) {\n"
            "  if (typeof fn === 'function') { fn(); }\n"
            "  return true;\n"
            "};\n"
        ),
    }
    for rel, text in files.items():
        out = output_dir / rel
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(text, encoding="utf-8")
