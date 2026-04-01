// Python 互換ランタイム（JavaScript版）の共通関数群。
// 将来的な Python -> JavaScript ネイティブ変換コードから利用する。

import { writeFileSync, mkdirSync, readFileSync, statSync, readdirSync } from "node:fs";
import { dirname } from "node:path";

const PY_TYPE_NONE = 0;
const PY_TYPE_BOOL = 1;
const PY_TYPE_NUMBER = 2;
const PY_TYPE_STRING = 3;
const PY_TYPE_ARRAY = 4;
const PY_TYPE_MAP = 5;
const PY_TYPE_SET = 6;
const PY_TYPE_OBJECT = 7;

const PYTRA_TYPE_ID = Symbol.for("pytra.type_id");
const PYTRA_TRUTHY = Symbol.for("pytra.py_truthy");
const PYTRA_TRY_LEN = Symbol.for("pytra.py_try_len");
const PYTRA_STR = Symbol.for("pytra.py_str");

const PYTRA_USER_TYPE_ID_BASE = 1000;
let _pyNextTypeId = PYTRA_USER_TYPE_ID_BASE;
const _pyTypeIds = [];
const _pyTypeBase = new Map();
const _pyTypeChildren = new Map();
const _pyTypeOrder = new Map();
const _pyTypeMin = new Map();
const _pyTypeMax = new Map();

function _pyDeepEq(a, b) {
  if (Array.isArray(a) && Array.isArray(b)) {
    if (a.length !== b.length) return false;
    for (let i = 0; i < a.length; i++) {
      if (!_pyDeepEq(a[i], b[i])) return false;
    }
    return true;
  }
  return Object.is(a, b);
}

const _NativeSet = globalThis.Set;
class PySet extends _NativeSet {
  constructor(items) {
    super();
    if (items) {
      for (const item of items) this.add(item);
    }
  }
  add(value) {
    if (!this.has(value)) super.add(value);
    return this;
  }
  has(value) {
    if (super.has(value)) return true;
    for (const item of super.values()) {
      if (_pyDeepEq(item, value)) return true;
    }
    return false;
  }
  delete(value) {
    if (super.delete(value)) return true;
    for (const item of super.values()) {
      if (_pyDeepEq(item, value)) return super.delete(item);
    }
    return false;
  }
}
globalThis.Set = PySet;

function _containsInt(items, value) {
  let i = 0;
  while (i < items.length) {
    if (items[i] === value) {
      return true;
    }
    i += 1;
  }
  return false;
}

function _removeInt(items, value) {
  let i = 0;
  while (i < items.length) {
    if (items[i] === value) {
      items.splice(i, 1);
      return;
    }
    i += 1;
  }
}

function _copyInts(items) {
  const out = [];
  for (const value of items) {
    out.push(value);
  }
  return out;
}

function _sortedInts(items) {
  const out = _copyInts(items);
  let i = 0;
  while (i < out.length) {
    let j = i + 1;
    while (j < out.length) {
      if (out[j] < out[i]) {
        const tmp = out[i];
        out[i] = out[j];
        out[j] = tmp;
      }
      j += 1;
    }
    i += 1;
  }
  return out;
}

function _registerTypeNode(typeId, baseTypeId) {
  if (!_containsInt(_pyTypeIds, typeId)) {
    _pyTypeIds.push(typeId);
  }
  const prevBase = _pyTypeBase.get(typeId);
  if (typeof prevBase === "number" && prevBase >= 0) {
    const prevChildren = _pyTypeChildren.get(prevBase);
    if (Array.isArray(prevChildren)) {
      _removeInt(prevChildren, typeId);
    }
  }
  _pyTypeBase.set(typeId, baseTypeId);
  if (!_pyTypeChildren.has(typeId)) {
    _pyTypeChildren.set(typeId, []);
  }
  if (baseTypeId < 0) {
    return;
  }
  if (!_pyTypeChildren.has(baseTypeId)) {
    _pyTypeChildren.set(baseTypeId, []);
  }
  const children = _pyTypeChildren.get(baseTypeId);
  if (Array.isArray(children) && !_containsInt(children, typeId)) {
    children.push(typeId);
  }
}

function _sortedChildTypeIds(typeId) {
  const children = _pyTypeChildren.get(typeId);
  if (!Array.isArray(children)) {
    return [];
  }
  return _sortedInts(children);
}

function _collectRootTypeIds() {
  const roots = [];
  for (const typeId of _pyTypeIds) {
    const baseTypeId = _pyTypeBase.get(typeId);
    if (typeof baseTypeId !== "number" || baseTypeId < 0 || !_pyTypeBase.has(baseTypeId)) {
      roots.push(typeId);
    }
  }
  return _sortedInts(roots);
}

function _assignTypeRangesDfs(typeId, nextOrder) {
  _pyTypeOrder.set(typeId, nextOrder);
  _pyTypeMin.set(typeId, nextOrder);
  let cur = nextOrder + 1;
  const children = _sortedChildTypeIds(typeId);
  for (const childTypeId of children) {
    cur = _assignTypeRangesDfs(childTypeId, cur);
  }
  _pyTypeMax.set(typeId, cur - 1);
  return cur;
}

function _recomputeTypeRanges() {
  _pyTypeOrder.clear();
  _pyTypeMin.clear();
  _pyTypeMax.clear();
  let nextOrder = 0;
  const roots = _collectRootTypeIds();
  for (const rootTypeId of roots) {
    nextOrder = _assignTypeRangesDfs(rootTypeId, nextOrder);
  }
  const allTypeIds = _sortedInts(_pyTypeIds);
  for (const typeId of allTypeIds) {
    if (!_pyTypeOrder.has(typeId)) {
      nextOrder = _assignTypeRangesDfs(typeId, nextOrder);
    }
  }
}

function _initBuiltinTypeBases() {
  if (_pyTypeIds.length > 0) {
    return;
  }
  _registerTypeNode(PY_TYPE_NONE, -1);
  _registerTypeNode(PY_TYPE_OBJECT, -1);
  _registerTypeNode(PY_TYPE_NUMBER, PY_TYPE_OBJECT);
  _registerTypeNode(PY_TYPE_BOOL, PY_TYPE_NUMBER);
  _registerTypeNode(PY_TYPE_STRING, PY_TYPE_OBJECT);
  _registerTypeNode(PY_TYPE_ARRAY, PY_TYPE_OBJECT);
  _registerTypeNode(PY_TYPE_MAP, PY_TYPE_OBJECT);
  _registerTypeNode(PY_TYPE_SET, PY_TYPE_OBJECT);
  _recomputeTypeRanges();
}

function _normalizeBaseTypeId(bases) {
  const normalized = Array.isArray(bases) ? bases.slice() : [];
  const unique = [];
  for (const typeId of normalized) {
    if (Number.isInteger(typeId) && !_containsInt(unique, typeId)) {
      unique.push(typeId);
    }
  }
  if (unique.length === 0) {
    return PY_TYPE_OBJECT;
  }
  if (unique.length > 1) {
    throw new Error("multiple inheritance is not supported");
  }
  const baseTypeId = unique[0];
  if (!_pyTypeBase.has(baseTypeId)) {
    throw new Error("unknown base type_id: " + String(baseTypeId));
  }
  return baseTypeId;
}

function pyRegisterType(typeId, bases = []) {
  _initBuiltinTypeBases();
  const baseTypeId = _normalizeBaseTypeId(bases);
  _registerTypeNode(typeId, baseTypeId);
  _recomputeTypeRanges();
  return typeId;
}

function pyRegisterClassType(bases = [PY_TYPE_OBJECT]) {
  _initBuiltinTypeBases();
  while (_pyTypeBase.has(_pyNextTypeId)) {
    _pyNextTypeId += 1;
  }
  const out = _pyNextTypeId;
  _pyNextTypeId += 1;
  return pyRegisterType(out, bases);
}

function pyIsSubtype(actualTypeId, expectedTypeId) {
  _initBuiltinTypeBases();
  const actualOrder = _pyTypeOrder.get(actualTypeId);
  if (typeof actualOrder !== "number") {
    return false;
  }
  const expectedMin = _pyTypeMin.get(expectedTypeId);
  const expectedMax = _pyTypeMax.get(expectedTypeId);
  if (typeof expectedMin !== "number" || typeof expectedMax !== "number") {
    return false;
  }
  return expectedMin <= actualOrder && actualOrder <= expectedMax;
}

function pyIsInstance(value, expectedTypeId) {
  return pyIsSubtype(pyTypeId(value), expectedTypeId);
}

/** 値の type_id を返す（minify 耐性のある tag dispatch 用）。 */
function pyTypeId(value) {
  _initBuiltinTypeBases();
  if (value === null || value === undefined) {
    return PY_TYPE_NONE;
  }
  const ty = typeof value;
  if (ty === "boolean") return PY_TYPE_BOOL;
  if (ty === "number") return PY_TYPE_NUMBER;
  if (ty === "string") return PY_TYPE_STRING;
  if (Array.isArray(value)) return PY_TYPE_ARRAY;
  if (value instanceof Map) return PY_TYPE_MAP;
  if (value instanceof Set) return PY_TYPE_SET;
  if ((ty === "object" || ty === "function") && value !== null) {
    const tagged = value[PYTRA_TYPE_ID];
    if (typeof tagged === "number" && Number.isInteger(tagged)) {
      return tagged;
    }
  }
  return PY_TYPE_OBJECT;
}

/** bool 境界の共通 truthy 判定。 */
function pyTruthy(value) {
  const typeId = pyTypeId(value);
  switch (typeId) {
    case PY_TYPE_NONE:
      return false;
    case PY_TYPE_BOOL:
      return value;
    case PY_TYPE_NUMBER:
      return value !== 0;
    case PY_TYPE_STRING:
      return value.length !== 0;
    case PY_TYPE_ARRAY:
      return value.length !== 0;
    case PY_TYPE_MAP:
    case PY_TYPE_SET:
      return value.size !== 0;
    case PY_TYPE_OBJECT:
      return true;
    default:
      break;
  }
  if ((typeof value === "object" || typeof value === "function") && value !== null) {
    const hook = value[PYTRA_TRUTHY];
    if (typeof hook === "function") {
      return Boolean(hook.call(value));
    }
  }
  return true;
}

/** len 境界の共通 try helper（未対応は null）。 */
function pyTryLen(value) {
  if ((typeof value === "object" || typeof value === "function") && value !== null) {
    const hook = value[PYTRA_TRY_LEN];
    if (typeof hook === "function") {
      const out = hook.call(value);
      if (typeof out === "number" && Number.isFinite(out)) {
        return Math.trunc(out);
      }
    }
  }
  const typeId = pyTypeId(value);
  switch (typeId) {
    case PY_TYPE_STRING:
    case PY_TYPE_ARRAY:
      return value.length;
    case PY_TYPE_MAP:
    case PY_TYPE_SET:
      return value.size;
    case PY_TYPE_OBJECT:
      return Object.keys(value).length;
    default:
      break;
  }
  return null;
}

/** str 境界の共通 helper。 */
function pyStr(value) {
  if (value instanceof Error) {
    return value.message || String(value);
  }
  const typeId = pyTypeId(value);
  switch (typeId) {
    case PY_TYPE_NONE:
      return "None";
    case PY_TYPE_BOOL:
      return value ? "True" : "False";
    case PY_TYPE_NUMBER:
      return String(value);
    case PY_TYPE_STRING:
      return value;
    case PY_TYPE_ARRAY:
      return `[${value.map((v) => pyToString(v)).join(", ")}]`;
    case PY_TYPE_MAP: {
      const entries = Array.from(value.entries()).map(([k, v]) => `${pyToString(k)}: ${pyToString(v)}`);
      return `{${entries.join(", ")}}`;
    }
    case PY_TYPE_SET: {
      const entries = Array.from(value.values()).map((v) => pyToString(v));
      return `{${entries.join(", ")}}`;
    }
    case PY_TYPE_OBJECT:
      return String(value);
    default:
      break;
  }
  if ((typeof value === "object" || typeof value === "function") && value !== null) {
    const hook = value[PYTRA_STR];
    if (typeof hook === "function") {
      return String(hook.call(value));
    }
  }
  return String(value);
}

/** Python 風の文字列表現へ変換する。 */
function pyToString(value) {
  return pyStr(value);
}

/** Python の print 相当（空白区切りで表示）。 */
function pyPrint(...args) {
  if (args.length === 0) {
    console.log("");
    return;
  }
  console.log(args.map((arg) => pyToString(arg)).join(" "));
}

/** Python の len 相当。 */
function pyLen(value) {
  const out = pyTryLen(value);
  if (out !== null) return out;
  throw new Error("len() unsupported type");
}

/** Python の bool 相当。 */
function pyBool(value) {
  return pyTruthy(value);
}

/** Python の range 相当配列を返す。 */
function pyRange(start, stop, step = 1) {
  if (stop === undefined) {
    stop = start;
    start = 0;
  }
  if (step === 0) {
    throw new Error("range() arg 3 must not be zero");
  }
  const out = [];
  if (step > 0) {
    for (let i = start; i < stop; i += step) {
      out.push(i);
    }
  } else {
    for (let i = start; i > stop; i += step) {
      out.push(i);
    }
  }
  return out;
}

/** Python の floor 除算相当。 */
function pyFloorDiv(a, b) {
  if (b === 0) {
    throw new Error("division by zero");
  }
  return Math.floor(a / b);
}

/** Python の剰余相当（除数と同符号）。 */
function pyMod(a, b) {
  if (b === 0) {
    throw new Error("integer modulo by zero");
  }
  const m = a % b;
  return m < 0 && b > 0 ? m + b : (m > 0 && b < 0 ? m + b : m);
}

/** Python の in 相当。 */
function pyIn(item, container) {
  const typeId = pyTypeId(container);
  switch (typeId) {
    case PY_TYPE_STRING:
      return container.includes(String(item));
    case PY_TYPE_ARRAY:
      return container.includes(item);
    case PY_TYPE_SET:
    case PY_TYPE_MAP:
      return container.has(item);
    case PY_TYPE_OBJECT:
      if (typeof container === "object" && container !== null) {
        return Object.prototype.hasOwnProperty.call(container, String(item));
      }
      break;
    default:
      if (typeof container === "object" && container !== null) {
        return Object.prototype.hasOwnProperty.call(container, String(item));
      }
      break;
  }
  throw new Error("in operation unsupported type");
}

/** Python のスライス相当（step なし）。 */
function pySlice(value, start = null, end = null) {
  const len = value.length;
  let s = start === null ? 0 : start;
  let e = end === null ? len : end;
  if (s < 0) s += len;
  if (e < 0) e += len;
  if (s < 0) s = 0;
  if (e < 0) e = 0;
  if (s > len) s = len;
  if (e > len) e = len;
  if (e < s) e = s;
  return value.slice(s, e);
}

/** Python の ord 相当。 */
function pyOrd(ch) {
  if (typeof ch !== "string" || ch.length === 0) {
    throw new Error("ord() expected non-empty string");
  }
  return ch.codePointAt(0);
}

/** Python の chr 相当。 */
function pyChr(code) {
  return String.fromCodePoint(code);
}

/** Python の bytearray 相当。 */
function pyBytearray(size = 0) {
  if (Array.isArray(size)) {
    return size.map((value) => value & 0xff);
  }
  if (size && typeof size !== "number" && typeof size.length === "number") {
    return Array.from(size, (value) => value & 0xff);
  }
  if (size < 0) {
    throw new Error("negative count");
  }
  return new Array(size).fill(0);
}

/** Python の bytes 相当（配列コピー）。 */
function pyBytes(value) {
  if (value === undefined || value === null) {
    return [];
  }
  if (Array.isArray(value)) {
    return value.slice();
  }
  return Array.from(value);
}

/** Python の str.isdigit 相当。 */
function pyIsDigit(value) {
  return typeof value === "string" && value.length > 0 && /^[0-9]+$/.test(value);
}

/** Python の str.isalpha 相当。 */
function pyIsAlpha(value) {
  return typeof value === "string" && value.length > 0 && /^[A-Za-z]+$/.test(value);
}

/** Python の open 相当（バイナリ書き込み専用）。 */
function open(filePath, _mode) {
  const dir = dirname(filePath);
  if (dir !== "" && dir !== ".") {
    mkdirSync(dir, { recursive: true });
  }
  const buf = [];
  return {
    write(data) {
      if (Array.isArray(data)) {
        for (let i = 0; i < data.length; i++) {
          buf.push(data[i] & 0xFF);
        }
      }
    },
    close() {
      writeFileSync(filePath, Buffer.from(buf));
    },
  };
}

const pyopen = open;

// ---------------------------------------------------------------------------
// math module
// ---------------------------------------------------------------------------
const py_math_pi = Math.PI;
const py_math_e = Math.E;
const py_math_inf = Infinity;
const py_math_nan = NaN;
function pyexp(x) { return Math.exp(x); }
function pysqrt(x) { return Math.sqrt(x); }
function pysin(x) { return Math.sin(x); }
function pycos(x) { return Math.cos(x); }
function pyfloor(x) { return Math.floor(x); }
function pylog2(x) { return Math.log2(x); }
function pyround(x, ndigits = 0) {
  if (ndigits === 0) return Math.round(x);
  const factor = Math.pow(10, ndigits);
  return Math.round(x * factor) / factor;
}
function pytrunc(x) { return Math.trunc(x); }
function pyatan2(y, x) { return Math.atan2(y, x); }
function pyasin(x) { return Math.asin(x); }
function pyacos(x) { return Math.acos(x); }
function pyatan(x) { return Math.atan(x); }
function pyhypot(...args) { return Math.hypot(...args); }
function pyisfinite(x) { return isFinite(x); }
function pyisinf(x) { return !isFinite(x) && !isNaN(x); }
function pyisnan(x) { return isNaN(x); }

// ---------------------------------------------------------------------------
// float / int helpers
// ---------------------------------------------------------------------------
function pyFloatStr(n) {
  if (!isFinite(n)) return String(n);
  if (Number.isInteger(n)) return n.toString() + ".0";
  return String(n);
}
const bool = Boolean;
const int = Number;
const float = Number;
const str = String;

// ---------------------------------------------------------------------------
// time module
// ---------------------------------------------------------------------------
function perf_counter() {
  if (typeof performance !== "undefined") return performance.now() / 1000;
  return Date.now() / 1000;
}

// ---------------------------------------------------------------------------
// re module
// ---------------------------------------------------------------------------
function match(pattern, s) {
  return s.match(new RegExp("^" + pattern));
}

// ---------------------------------------------------------------------------
// pathlib module
// ---------------------------------------------------------------------------
class PyPath {
  constructor(p) {
    this._p = typeof p === "string" ? p : p._p;
  }
  toString() { return this._p; }
  get name() { const parts = this._p.split("/"); return parts[parts.length - 1] || ""; }
  get stem() { const n = this.name; const i = n.lastIndexOf("."); return i > 0 ? n.slice(0, i) : n; }
  get suffix() { const n = this.name; const i = n.lastIndexOf("."); return i > 0 ? n.slice(i) : ""; }
  get parent() { const i = this._p.lastIndexOf("/"); return new PyPath(i >= 0 ? this._p.slice(0, i) : "."); }
  joinpath(...parts) { return new PyPath(this._p + "/" + parts.map(p => typeof p === "string" ? p : p._p).join("/")); }
  exists() { try { statSync(this._p); return true; } catch { return false; } }
  read_text() { return readFileSync(this._p, "utf-8"); }
  write_text(t) { mkdirSync(dirname(this._p), { recursive: true }); writeFileSync(this._p, t, "utf-8"); }
  mkdir(parents = false, exist_ok = false) {
    let recursive = !!parents;
    let ignoreExists = !!exist_ok;
    if (parents && typeof parents === "object") {
      recursive = !!parents.parents;
      ignoreExists = !!parents.exist_ok;
    }
    try {
      mkdirSync(this._p, { recursive });
    } catch (err) {
      if (!ignoreExists) throw err;
    }
  }
}
function Path(p) { return new PyPath(p); }

// ---------------------------------------------------------------------------
// string helpers
// ---------------------------------------------------------------------------
function pyStrJoin(sep, items) { return items.join(sep); }
function pyStrIsdigit(s) { return s.length > 0 && /^\d+$/.test(s); }
function pyStrIsalpha(s) { return s.length > 0 && /^[a-zA-Z]+$/.test(s); }
function pyStrStartswith(s, prefix) { return s.startsWith(prefix); }
function pyStrEndswith(s, suffix) { return s.endsWith(suffix); }
function pyStrReplace(s, old, rep, count) {
  if (count === undefined || count < 0) return s.split(old).join(rep);
  let result = s;
  for (let i = 0; i < count; i++) {
    const idx = result.indexOf(old);
    if (idx === -1) break;
    result = result.slice(0, idx) + rep + result.slice(idx + old.length);
  }
  return result;
}
function pyStrStrip(s, chars) {
  if (!chars) return s.trim();
  const re = new RegExp("^[" + chars.replace(/[-[\]{}()*+?.,\\^$|#\s]/g, "\\$&") + "]+|[" + chars.replace(/[-[\]{}()*+?.,\\^$|#\s]/g, "\\$&") + "]+$", "g");
  return s.replace(re, "");
}
function pyStrLstrip(s, chars) {
  if (!chars) return s.trimStart();
  const esc = chars.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
  return s.replace(new RegExp("^[" + esc + "]+"), "");
}
function pyStrRstrip(s, chars) {
  if (!chars) return s.trimEnd();
  const esc = chars.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
  return s.replace(new RegExp("[" + esc + "]+$"), "");
}
function pyStrUpper(s) { return s.toUpperCase(); }
function pyStrLower(s) { return s.toLowerCase(); }
function pyStrFind(s, sub, start = 0, end = -1) {
  const haystack = end < 0 ? s.slice(start) : s.slice(start, end);
  const idx = haystack.indexOf(sub);
  return idx < 0 ? -1 : idx + start;
}
function pyStrRfind(s, sub, start = 0, end = -1) {
  const haystack = end < 0 ? s.slice(start) : s.slice(start, end);
  const idx = haystack.lastIndexOf(sub);
  return idx < 0 ? -1 : idx + start;
}
function pyStrSplit(s, sep, maxsplit = -1) {
  if (sep === undefined || sep === null) {
    const parts = s.split(/\s+/).filter((p) => p.length > 0);
    if (maxsplit < 0) return parts;
    const head = parts.slice(0, maxsplit);
    const tail = parts.slice(maxsplit).join(" ");
    return tail ? [...head, tail] : head;
  }
  if (maxsplit < 0) return s.split(sep);
  const result = [];
  let remaining = s;
  let n = maxsplit;
  while (n-- > 0) {
    const idx = remaining.indexOf(sep);
    if (idx < 0) break;
    result.push(remaining.slice(0, idx));
    remaining = remaining.slice(idx + sep.length);
  }
  result.push(remaining);
  return result;
}
function pyStrCount(s, sub, start = 0, end = -1) {
  const haystack = end < 0 ? s.slice(start) : s.slice(start, end);
  if (sub.length === 0) return haystack.length + 1;
  let count = 0;
  let pos = 0;
  while ((pos = haystack.indexOf(sub, pos)) >= 0) {
    count += 1;
    pos += sub.length;
  }
  return count;
}
function pyStrIndex(s, sub, start = 0, end = -1) {
  const idx = pyStrFind(s, sub, start, end);
  if (idx < 0) throw new Error("substring not found");
  return idx;
}
function pyStrIsalnum(s) { return s.length > 0 && /^[A-Za-z0-9]+$/.test(s); }
function pyStrIsspace(s) { return s.length > 0 && /^\s+$/.test(s); }
function pyEnumerate(items, start = 0) { return items.map((item, i) => [i + start, item]); }
function pyReversed(items) { return items.slice().reverse(); }
function pySorted(items, key, reverse = false) {
  const sorted = items.slice().sort((a, b) => {
    const ka = key ? key(a) : a;
    const kb = key ? key(b) : b;
    if (ka < kb) return reverse ? 1 : -1;
    if (ka > kb) return reverse ? -1 : 1;
    return 0;
  });
  return sorted;
}

function pyAssertTrue(cond, label = "") {
  if (cond) return true;
  pyPrint(label !== "" ? `[assert_true] ${label}: False` : "[assert_true] False");
  return false;
}
function pyAssertEq(actual, expected, label = "") {
  const ok = pyStr(actual) === pyStr(expected);
  if (ok) return true;
  pyPrint(label !== "" ? `[assert_eq] ${label}: actual=${pyStr(actual)}, expected=${pyStr(expected)}` : `[assert_eq] actual=${pyStr(actual)}, expected=${pyStr(expected)}`);
  return false;
}
function pyAssertAll(results, label = "") {
  for (const v of results) {
    if (!v) {
      pyPrint(label !== "" ? `[assert_all] ${label}: False` : "[assert_all] False");
      return false;
    }
  }
  return true;
}
function pyAssertStdout(expected, fn) {
  const lines = [];
  const origLog = console.log;
  console.log = (...args) => {
    lines.push(args.map((arg) => String(arg)).join(" "));
  };
  try {
    fn();
  } finally {
    console.log = origLog;
  }
  if (lines.join("\n") !== expected.join("\n")) {
    return `[assert_stdout] FAIL\n  expected: ${JSON.stringify(expected)}\n  actual:   ${JSON.stringify(lines)}`;
  }
  return "True";
}

function type_(obj) {
  if (obj === null || obj === undefined) return { __name__: "NoneType" };
  if (typeof obj === "boolean") return { __name__: "bool" };
  if (typeof obj === "number") return { __name__: "int" };
  if (typeof obj === "string") return { __name__: "str" };
  if (Array.isArray(obj)) return { __name__: "list" };
  if (obj instanceof Map) return { __name__: "dict" };
  if (obj instanceof Set) return { __name__: "set" };
  const ctor = obj.constructor;
  return { __name__: (typeof ctor === "function" && ctor.name) ? ctor.name : "object" };
}

function pysum(iterable, start = 0) {
  let acc = start;
  for (const value of iterable) acc += value;
  return acc;
}

function pyzip(a, b) {
  const len = Math.min(a.length, b.length);
  const result = [];
  for (let i = 0; i < len; i++) result.push([a[i], b[i]]);
  return result;
}

class _Deque {
  constructor(items) {
    this._data = items ? Array.from(items) : [];
  }
  append(v) { this._data.push(v); }
  appendleft(v) { this._data.unshift(v); }
  pop() {
    if (this._data.length === 0) throw new Error("pop from an empty deque");
    return this._data.pop();
  }
  popleft() {
    if (this._data.length === 0) throw new Error("pop from an empty deque");
    return this._data.shift();
  }
  clear() { this._data.length = 0; }
  get length() { return this._data.length; }
  [Symbol.iterator]() { return this._data[Symbol.iterator](); }
  [PYTRA_TRY_LEN]() { return this._data.length; }
}
function deque(items) { return new _Deque(items); }

function pyfabs(x) { return Math.abs(x); }
function pytan(x) { return Math.tan(x); }
function pylog(x, base) { return base !== undefined ? Math.log(x) / Math.log(base) : Math.log(x); }
function pylog10(x) { return Math.log10(x); }
function pyceil(x) { return Math.ceil(x); }
function pypow(x, y) { return Math.pow(x, y); }
const py_math_tau = 2 * Math.PI;

function dumps(obj, ensure_ascii = true, indent = null, sort_keys = null) {
  function serialize(v, depth) {
    if (v === null || v === undefined) return "null";
    if (typeof v === "boolean") return v ? "true" : "false";
    if (typeof v === "number") return String(v);
    if (typeof v === "string") {
      const s = JSON.stringify(v);
      if (!ensure_ascii) return s;
      return s.replace(/[\u0080-\uFFFF]/g, (c) => "\\u" + c.charCodeAt(0).toString(16).padStart(4, "0"));
    }
    if (Array.isArray(v)) {
      const items = v.map((item) => serialize(item, depth + 1));
      if (indent !== null && indent > 0) {
        const pad = " ".repeat(indent * (depth + 1));
        const closePad = " ".repeat(indent * depth);
        return "[\n" + items.map((i) => pad + i).join(",\n") + "\n" + closePad + "]";
      }
      return "[" + items.join(", ") + "]";
    }
    if (v instanceof Map) {
      const keys = sort_keys ? [...v.keys()].sort() : [...v.keys()];
      const pairs = keys.map((k) => serialize(String(k), depth + 1) + ": " + serialize(v.get(k), depth + 1));
      if (indent !== null && indent > 0) {
        const pad = " ".repeat(indent * (depth + 1));
        const closePad = " ".repeat(indent * depth);
        return "{\n" + pairs.map((p) => pad + p).join(",\n") + "\n" + closePad + "}";
      }
      return "{" + pairs.join(", ") + "}";
    }
    if (typeof v === "object") {
      const obj2 = v;
      let keys = Object.keys(obj2);
      if (sort_keys) keys = keys.sort();
      const pairs = keys.map((k) => JSON.stringify(k) + ": " + serialize(obj2[k], depth + 1));
      if (indent !== null && indent > 0) {
        const pad = " ".repeat(indent * (depth + 1));
        const closePad = " ".repeat(indent * depth);
        return "{\n" + pairs.map((p) => pad + p).join(",\n") + "\n" + closePad + "}";
      }
      return "{" + pairs.join(", ") + "}";
    }
    return JSON.stringify(v);
  }
  return serialize(obj, 0);
}
function loads(s) {
  function revive(v) {
    if (v === null) return null;
    if (typeof v === "object" && !Array.isArray(v)) {
      const map = new Map();
      for (const [k, val] of Object.entries(v)) {
        map.set(k, revive(val));
      }
      return map;
    }
    if (Array.isArray(v)) return v.map(revive);
    return v;
  }
  return revive(JSON.parse(s));
}
class JsonValue {
  constructor(raw) { this.raw = raw; }
  as_str() { return typeof this.raw === "string" ? this.raw : null; }
  as_int() { return typeof this.raw === "number" ? Math.trunc(this.raw) : null; }
  as_float() { return typeof this.raw === "number" ? this.raw : null; }
  as_bool() { return typeof this.raw === "boolean" ? this.raw : null; }
  as_obj() { return this.raw instanceof Map ? new JsonObj(this.raw) : null; }
  as_arr() { return Array.isArray(this.raw) ? new JsonArr(this.raw) : null; }
}
class JsonArr {
  constructor(raw) { this.raw = raw; }
  get(index) { return index < 0 || index >= this.raw.length ? null : new JsonValue(this.raw[index]); }
  get_str(index) { const v = this.get(index); return v ? v.as_str() : null; }
  get_int(index) { const v = this.get(index); return v ? v.as_int() : null; }
  get_float(index) { const v = this.get(index); return v ? v.as_float() : null; }
  get_bool(index) { const v = this.get(index); return v ? v.as_bool() : null; }
  get_arr(index) { const v = this.get(index); return v ? v.as_arr() : null; }
  get_obj(index) { const v = this.get(index); return v ? v.as_obj() : null; }
}
class JsonObj {
  constructor(raw) { this.raw = raw; }
  get(key) { return this.raw.has(key) ? new JsonValue(this.raw.get(key)) : null; }
  get_str(key) { const v = this.get(key); return v ? v.as_str() : null; }
  get_int(key) { const v = this.get(key); return v ? v.as_int() : null; }
  get_float(key) { const v = this.get(key); return v ? v.as_float() : null; }
  get_bool(key) { const v = this.get(key); return v ? v.as_bool() : null; }
  get_arr(key) { const v = this.get(key); return v ? v.as_arr() : null; }
  get_obj(key) { const v = this.get(key); return v ? v.as_obj() : null; }
}
function _parseJsonVal(v) {
  if (v === null || v === undefined) return null;
  if (typeof v === "boolean" || typeof v === "number" || typeof v === "string") return v;
  if (Array.isArray(v)) return v.map(_parseJsonVal);
  if (typeof v === "object") {
    const m = new Map();
    for (const [k, val] of Object.entries(v)) m.set(k, _parseJsonVal(val));
    return m;
  }
  return null;
}
function pyloads(s) { return new JsonValue(_parseJsonVal(JSON.parse(s))); }
function pyloads_arr(s) { const v = _parseJsonVal(JSON.parse(s)); return Array.isArray(v) ? new JsonArr(v) : null; }
function pyloads_obj(s) { const v = _parseJsonVal(JSON.parse(s)); return v instanceof Map ? new JsonObj(v) : null; }
function pydumps(obj, ensure_ascii = true, indent = null, _separators = null) { return dumps(obj, ensure_ascii, indent, null); }

function pyjoin(...parts) {
  if (parts.length === 0) return "";
  let result = parts[0];
  for (let i = 1; i < parts.length; i++) {
    const p = parts[i];
    if (p.startsWith("/")) { result = p; continue; }
    result = result.endsWith("/") ? result + p : result + "/" + p;
  }
  return result;
}
function pysplitext(p) {
  const dot = p.lastIndexOf(".");
  const slash = Math.max(p.lastIndexOf("/"), p.lastIndexOf("\\"));
  if (dot > slash && dot !== -1) return [p.slice(0, dot), p.slice(dot)];
  return [p, ""];
}
function pybasename(p) {
  const s = p.replace(/[/\\]$/, "");
  const i = Math.max(s.lastIndexOf("/"), s.lastIndexOf("\\"));
  return i === -1 ? s : s.slice(i + 1);
}
function pydirname(p) {
  const s = p.replace(/[/\\]$/, "");
  const i = Math.max(s.lastIndexOf("/"), s.lastIndexOf("\\"));
  if (i === -1) return ".";
  if (i === 0) return "/";
  return s.slice(0, i);
}
function pyjoinpath(...parts) { return pyjoin(...parts); }
function pyexists(p) { try { return statSync(p) !== undefined; } catch { return false; } }
function pyisfile(p) { try { return statSync(p).isFile(); } catch { return false; } }
function pyisdir(p) { try { return statSync(p).isDirectory(); } catch { return false; } }

const sys = { argv: [], path: [] };
function pyset_argv(args) { sys.argv = args; }
function pyset_path(paths) { sys.path = paths; }

function sub(pattern, repl, s, count = 0) {
  const flags = count === 0 ? "g" : "";
  const re = new RegExp(pattern, flags);
  if (count > 0) {
    let result = s;
    for (let i = 0; i < count; i++) result = result.replace(re, repl);
    return result;
  }
  return s.replace(re, repl);
}
function search(pattern, s) { return s.match(new RegExp(pattern)); }
function findall(pattern, s) {
  const matches = [];
  const re = new RegExp(pattern, "g");
  let m;
  while ((m = re.exec(s)) !== null) matches.push(m[0]);
  return matches;
}
function split(pattern, s, maxsplit = 0) {
  if (maxsplit === 0) return s.split(new RegExp(pattern));
  return s.split(new RegExp(pattern), maxsplit + 1);
}

class _ArgumentParser {
  constructor(description = "") { this._desc = description; this._args = []; }
  add_argument(...params) {
    const names = [];
    let action = "store";
    let choices = null;
    let default_val = null;
    for (const p of params) {
      if (typeof p === "string") {
        if (p === "store_true" || p === "store_false") action = p;
        else if (p.startsWith("-")) names.push(p);
        else if (names.length === 0) names.push(p);
        else default_val = p;
      } else if (Array.isArray(p)) choices = p;
      else if (p !== null && p !== undefined) default_val = p;
    }
    if (action === "store_true" && default_val === null) default_val = false;
    this._args.push({ names, choices, default_val, action });
  }
  parse_args(args) {
    const result = new Map();
    let pos = 0;
    const positional = this._args.filter((a) => a.names.length > 0 && !a.names[0].startsWith("-"));
    const optional = this._args.filter((a) => a.names.length > 0 && a.names[0].startsWith("-"));
    for (const arg of optional) {
      const key = arg.names[arg.names.length - 1].replace(/^-+/, "").replace(/-/g, "_");
      result.set(key, arg.default_val ?? null);
    }
    let i = 0;
    while (i < args.length) {
      const a = args[i];
      if (a.startsWith("-")) {
        const opt = optional.find((o) => o.names.includes(a));
        if (opt) {
          const key = opt.names[opt.names.length - 1].replace(/^-+/, "").replace(/-/g, "_");
          if (opt.action === "store_true") { result.set(key, true); i += 1; }
          else if (opt.action === "store_false") { result.set(key, false); i += 1; }
          else { result.set(key, args[i + 1]); i += 2; }
          continue;
        }
      } else if (pos < positional.length) {
        const key = positional[pos].names[0].replace(/^-+/, "");
        result.set(key, a);
        pos += 1;
      }
      i += 1;
    }
    return result;
  }
}
function ArgumentParser(description = "") { return new _ArgumentParser(description); }

function pymakedirs(path, exist_ok = false) {
  try { mkdirSync(path, { recursive: true }); } catch (e) { if (!exist_ok) throw e; }
}

function _crc32(data) {
  let crc = 0xffffffff;
  for (const b of data) {
    crc ^= b;
    for (let i = 0; i < 8; i++) crc = (crc & 1) ? (0xedb88320 ^ (crc >>> 1)) : (crc >>> 1);
  }
  return (crc ^ 0xffffffff) >>> 0;
}
function _encode_png(w, h, pixels) {
  const sig = [137, 80, 78, 71, 13, 10, 26, 10];
  function chunk(type, data) {
    const len = data.length;
    const typeBytes = type.split("").map((c) => c.charCodeAt(0));
    const crcInput = [...typeBytes, ...data];
    const crc = _crc32(crcInput);
    return [(len >> 24) & 0xff, (len >> 16) & 0xff, (len >> 8) & 0xff, len & 0xff, ...typeBytes, ...data, (crc >> 24) & 0xff, (crc >> 16) & 0xff, (crc >> 8) & 0xff, crc & 0xff];
  }
  const ihdr = [(w >> 24) & 0xff, (w >> 16) & 0xff, (w >> 8) & 0xff, w & 0xff, (h >> 24) & 0xff, (h >> 16) & 0xff, (h >> 8) & 0xff, h & 0xff, 8, 2, 0, 0, 0];
  const raw = [];
  for (let y = 0; y < h; y++) {
    raw.push(0);
    for (let x = 0; x < w; x++) {
      const i = (y * w + x) * 3;
      raw.push(pixels[i] ?? 0, pixels[i + 1] ?? 0, pixels[i + 2] ?? 0);
    }
  }
  const zlib = [0x78, 0x01, 1, raw.length & 0xff, (raw.length >> 8) & 0xff, (~raw.length) & 0xff, ((~raw.length) >> 8) & 0xff, ...raw, ...Array(4).fill(0)];
  return [...sig, ...chunk("IHDR", ihdr), ...chunk("IDAT", zlib), ...chunk("IEND", [])];
}
function pywrite_rgb_png(path, width, height, pixels) {
  try { writeFileSync(path, new Uint8Array(_encode_png(width, height, pixels))); } catch {}
}

function pyglob(pattern) {
  try {
    const dir = dirname(pattern) || ".";
    const base = pattern.slice(dir === "." ? 0 : dir.length + 1);
    const regexStr = base.replace(/[.+^${}()|[\]\\]/g, "\\$&").replace(/\*/g, ".*").replace(/\?/g, ".");
    const re = new RegExp("^" + regexStr + "$");
    const entries = readdirSync(dir);
    return entries.filter((e) => re.test(e)).map((e) => dir === "." ? e : dir + "/" + e);
  } catch { return []; }
}
function pyextend(lst, other) { for (const item of other) lst.push(item); }
function dict() { return new Map(); }
function list() { return []; }
function set_() { return new Set(); }
function field(factory) { return typeof factory === "function" ? factory() : factory; }
const ___ = undefined;
function pyFmt(value, spec) {
  if (spec === "" || spec === undefined || spec === null) return String(value);
  if ((spec.endsWith("s") || spec.includes("<")) && typeof value === "string") {
    const mStr = spec.match(/^([<>=^])?(\d+)?s?$/);
    if (mStr) {
      const [, align = "", widthStr = "0"] = mStr;
      const width = parseInt(widthStr, 10);
      if (align === "<" && width > value.length) return value.padEnd(width, " ");
      if ((align === "" || align === ">") && width > value.length) return value.padStart(width, " ");
      if (align === "^" && width > value.length) {
        const pad = width - value.length;
        const left = Math.floor(pad / 2);
        const right = pad - left;
        return " ".repeat(left) + value + " ".repeat(right);
      }
    }
    return value;
  }
  const n = typeof value === "number" ? value : Number(value);
  if (!Number.isFinite(n)) return String(value);
  const m = spec.match(/^([<>=^])?([+\- ])?(#?)(0?)(\d*)([,_])?(?:\.(\d+))?([bcdeEfFgGnosxX%])?$/);
  if (!m) return String(value);
  const [, align = "", sign = "", _hash, zeroPadChar, widthStr, grouping, precStr, typeChar = ""] = m;
  const width = widthStr ? parseInt(widthStr, 10) : 0;
  const prec = precStr ? parseInt(precStr, 10) : -1;
  let out = "";
  if (typeChar === "f" || typeChar === "F") out = (prec >= 0 ? n.toFixed(prec) : n.toFixed(6));
  else if (typeChar === "e" || typeChar === "E") out = (prec >= 0 ? n.toExponential(prec) : n.toExponential());
  else if (typeChar === "g" || typeChar === "G") out = (prec >= 0 ? n.toPrecision(prec) : String(n));
  else if (typeChar === "x") out = Math.trunc(n).toString(16);
  else if (typeChar === "X") out = Math.trunc(n).toString(16).toUpperCase();
  else if (typeChar === "b") out = Math.trunc(n).toString(2);
  else if (typeChar === "%") out = ((prec >= 0 ? (n * 100).toFixed(prec) : String(n * 100)) + "%");
  else out = String(value);
  if (grouping === ",") {
    const parts = out.split(".");
    parts[0] = parts[0].replace(/\B(?=(\d{3})+(?!\d))/g, ",");
    out = parts.join(".");
  }
  if (sign === "+" && !out.startsWith("-")) out = "+" + out;
  else if (sign === " " && !out.startsWith("-")) out = " " + out;
  if (width > out.length) {
    const fill = zeroPadChar === "0" ? "0" : " ";
    if (align === "<") out = out.padEnd(width, fill);
    else if (align === "^") {
      const pad = width - out.length;
      const left = Math.floor(pad / 2);
      const right = pad - left;
      out = fill.repeat(left) + out + fill.repeat(right);
    } else out = out.padStart(width, fill);
  }
  return out;
}

export {
  PY_TYPE_NONE,
  PY_TYPE_BOOL,
  PY_TYPE_NUMBER,
  PY_TYPE_STRING,
  PY_TYPE_ARRAY,
  PY_TYPE_MAP,
  PY_TYPE_SET,
  PY_TYPE_OBJECT,
  PYTRA_TYPE_ID,
  PYTRA_TRUTHY,
  PYTRA_TRY_LEN,
  PYTRA_STR,
  pyRegisterType,
  pyRegisterClassType,
  pyIsSubtype,
  pyIsInstance,
  pyTypeId,
  pyTruthy,
  pyTryLen,
  pyStr,
  pyToString,
  pyPrint,
  pyLen,
  pyBool,
  pyRange,
  pyFloorDiv,
  pyMod,
  pyIn,
  pySlice,
  pyOrd,
  pyChr,
  pyBytearray,
  pyBytes,
  pyIsDigit,
  pyIsAlpha,
  deque,
  open,
  py_math_pi,
  py_math_e,
  py_math_inf,
  py_math_nan,
  pyexp,
  pylog2,
  pysqrt,
  pysin,
  pycos,
  pyfloor,
  pyround,
  pytrunc,
  pyatan2,
  pyasin,
  pyacos,
  pyatan,
  pyhypot,
  pyisfinite,
  pyisinf,
  pyisnan,
  pyFloatStr,
  pyAssertStdout,
  pyAssertTrue,
  pyAssertEq,
  pyAssertAll,
  type_,
  pysum,
  pyzip,
  pyfabs,
  pytan,
  pylog,
  pylog10,
  pyceil,
  pypow,
  dumps,
  loads,
  pydumps,
  pyloads,
  pyloads_arr,
  pyloads_obj,
  JsonValue,
  JsonArr,
  JsonObj,
  py_math_tau,
  pyjoin,
  pysplitext,
  pybasename,
  pydirname,
  pyexists,
  pyisfile,
  pyisdir,
  pyjoinpath,
  int,
  float,
  str,
  sys,
  pyset_argv,
  pyset_path,
  perf_counter,
  sub,
  match,
  search,
  findall,
  split,
  ArgumentParser,
  pymakedirs,
  pywrite_rgb_png,
  pyglob,
  pyextend,
  dict,
  list,
  set_,
  field,
  ___,
  Path,
  PyPath,
  pyStrJoin,
  pyStrIsdigit,
  pyStrIsalpha,
  pyStrIsalnum,
  pyStrIsspace,
  pyStrUpper,
  pyStrLower,
  pyStrStartswith,
  pyStrEndswith,
  pyStrReplace,
  pyStrStrip,
  pyStrLstrip,
  pyStrRstrip,
  pyStrFind,
  pyStrRfind,
  pyStrSplit,
  pyStrCount,
  pyStrIndex,
  pyEnumerate,
  pyReversed,
  pySorted,
  pyFmt,
  bool,
  pyopen,
};
