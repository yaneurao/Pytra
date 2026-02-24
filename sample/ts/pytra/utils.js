import * as py_runtime from "../../../src/runtime/js/pytra/py_runtime.js";
import { write_rgb_png } from "../../../src/runtime/js/pytra/png_helper.js";

export const png = {
  write_rgb_png,
};

export const bytearray = py_runtime.pyBytearray;
export const bytes = py_runtime.pyBytes;
export const max = Math.max;
export const min = Math.min;

if (typeof globalThis !== "undefined") {
  globalThis.bytearray = globalThis.bytearray ?? py_runtime.pyBytearray;
  globalThis.bytes = globalThis.bytes ?? py_runtime.pyBytes;
  globalThis.max = globalThis.max ?? Math.max;
  globalThis.min = globalThis.min ?? Math.min;
}
