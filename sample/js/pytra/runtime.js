import * as py_runtime from "../../../src/runtime/js/pytra/py_runtime.js";
import { write_rgb_png } from "../../../src/runtime/js/pytra/png_helper.js";
import { grayscale_palette, save_gif } from "../../../src/runtime/js/pytra/gif_helper.js";

export const { PY_TYPE_NONE, PY_TYPE_BOOL, PY_TYPE_NUMBER, PY_TYPE_STRING, PY_TYPE_ARRAY, PY_TYPE_MAP, PY_TYPE_SET, PY_TYPE_OBJECT, PYTRA_TYPE_ID, PYTRA_TRUTHY, PYTRA_TRY_LEN, PYTRA_STR, pyRegisterType, pyRegisterClassType, pyIsSubtype, pyIsInstance, pyTypeId, pyTruthy, pyTryLen, pyStr, pyToString, pyPrint, pyLen, pyBool, pyRange, pyFloorDiv, pyMod, pyIn, pySlice, pyOrd, pyChr, pyBytearray, pyBytes, pyIsDigit, pyIsAlpha, } = py_runtime;

export const bytearray = pyBytearray;
export const bytes = pyBytes;
export const range = pyRange;
export const len = pyLen;
export const str = pyStr;
export const bool = pyBool;
export const max = Math.max;
export const min = Math.min;

if (typeof globalThis !== "undefined") {
  globalThis.bytearray = globalThis.bytearray ?? pyBytearray;
  globalThis.bytes = globalThis.bytes ?? pyBytes;
  globalThis.range = globalThis.range ?? pyRange;
  globalThis.len = globalThis.len ?? pyLen;
  globalThis.str = globalThis.str ?? pyStr;
  globalThis.bool = globalThis.bool ?? pyBool;
  globalThis.max = globalThis.max ?? Math.max;
  globalThis.min = globalThis.min ?? Math.min;
}

export const png = { write_rgb_png };
export const gif = { grayscale_palette, save_gif };
