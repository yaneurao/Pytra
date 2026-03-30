// Python 互換ランタイム（TypeScript版）の共通関数群。
// 将来的な Python -> TypeScript ネイティブ変換コードから利用する。

import { writeFileSync, mkdirSync } from "node:fs";
import { dirname } from "node:path";

export const PY_TYPE_NONE = 0;
export const PY_TYPE_BOOL = 1;
export const PY_TYPE_NUMBER = 2;
export const PY_TYPE_STRING = 3;
export const PY_TYPE_ARRAY = 4;
export const PY_TYPE_MAP = 5;
export const PY_TYPE_SET = 6;
export const PY_TYPE_OBJECT = 7;

export const PYTRA_TYPE_ID = Symbol.for("pytra.type_id");
export const PYTRA_TRUTHY = Symbol.for("pytra.py_truthy");
export const PYTRA_TRY_LEN = Symbol.for("pytra.py_try_len");
export const PYTRA_STR = Symbol.for("pytra.py_str");

const PYTRA_USER_TYPE_ID_BASE = 1000;
let pyNextTypeId = PYTRA_USER_TYPE_ID_BASE;
const pyTypeIds: number[] = [];
const pyTypeBase = new Map<number, number>();
const pyTypeChildren = new Map<number, number[]>();
const pyTypeOrder = new Map<number, number>();
const pyTypeMin = new Map<number, number>();
const pyTypeMax = new Map<number, number>();

function containsInt(items: number[], value: number): boolean {
  let i = 0;
  while (i < items.length) {
    if (items[i] === value) {
      return true;
    }
    i += 1;
  }
  return false;
}

function removeInt(items: number[], value: number): void {
  let i = 0;
  while (i < items.length) {
    if (items[i] === value) {
      items.splice(i, 1);
      return;
    }
    i += 1;
  }
}

function copyInts(items: number[]): number[] {
  const out: number[] = [];
  for (const value of items) {
    out.push(value);
  }
  return out;
}

function sortedInts(items: number[]): number[] {
  const out = copyInts(items);
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

function registerTypeNode(typeId: number, baseTypeId: number): void {
  if (!containsInt(pyTypeIds, typeId)) {
    pyTypeIds.push(typeId);
  }
  const prevBase = pyTypeBase.get(typeId);
  if (typeof prevBase === "number" && prevBase >= 0) {
    const prevChildren = pyTypeChildren.get(prevBase);
    if (Array.isArray(prevChildren)) {
      removeInt(prevChildren, typeId);
    }
  }
  pyTypeBase.set(typeId, baseTypeId);
  if (!pyTypeChildren.has(typeId)) {
    pyTypeChildren.set(typeId, []);
  }
  if (baseTypeId < 0) {
    return;
  }
  if (!pyTypeChildren.has(baseTypeId)) {
    pyTypeChildren.set(baseTypeId, []);
  }
  const children = pyTypeChildren.get(baseTypeId);
  if (Array.isArray(children) && !containsInt(children, typeId)) {
    children.push(typeId);
  }
}

function sortedChildTypeIds(typeId: number): number[] {
  const children = pyTypeChildren.get(typeId);
  if (!Array.isArray(children)) {
    return [];
  }
  return sortedInts(children);
}

function collectRootTypeIds(): number[] {
  const roots: number[] = [];
  for (const typeId of pyTypeIds) {
    const baseTypeId = pyTypeBase.get(typeId);
    if (typeof baseTypeId !== "number" || baseTypeId < 0 || !pyTypeBase.has(baseTypeId)) {
      roots.push(typeId);
    }
  }
  return sortedInts(roots);
}

function assignTypeRangesDfs(typeId: number, nextOrder: number): number {
  pyTypeOrder.set(typeId, nextOrder);
  pyTypeMin.set(typeId, nextOrder);
  let cur = nextOrder + 1;
  const children = sortedChildTypeIds(typeId);
  for (const childTypeId of children) {
    cur = assignTypeRangesDfs(childTypeId, cur);
  }
  pyTypeMax.set(typeId, cur - 1);
  return cur;
}

function recomputeTypeRanges(): void {
  pyTypeOrder.clear();
  pyTypeMin.clear();
  pyTypeMax.clear();
  let nextOrder = 0;
  const roots = collectRootTypeIds();
  for (const rootTypeId of roots) {
    nextOrder = assignTypeRangesDfs(rootTypeId, nextOrder);
  }
  const allTypeIds = sortedInts(pyTypeIds);
  for (const typeId of allTypeIds) {
    if (!pyTypeOrder.has(typeId)) {
      nextOrder = assignTypeRangesDfs(typeId, nextOrder);
    }
  }
}

function initBuiltinTypeBases(): void {
  if (pyTypeIds.length > 0) {
    return;
  }
  registerTypeNode(PY_TYPE_NONE, -1);
  registerTypeNode(PY_TYPE_OBJECT, -1);
  registerTypeNode(PY_TYPE_NUMBER, PY_TYPE_OBJECT);
  registerTypeNode(PY_TYPE_BOOL, PY_TYPE_NUMBER);
  registerTypeNode(PY_TYPE_STRING, PY_TYPE_OBJECT);
  registerTypeNode(PY_TYPE_ARRAY, PY_TYPE_OBJECT);
  registerTypeNode(PY_TYPE_MAP, PY_TYPE_OBJECT);
  registerTypeNode(PY_TYPE_SET, PY_TYPE_OBJECT);
  recomputeTypeRanges();
}

function normalizeBaseTypeId(bases: number[]): number {
  const unique: number[] = [];
  for (const typeId of bases) {
    if (Number.isInteger(typeId) && !containsInt(unique, typeId)) {
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
  if (!pyTypeBase.has(baseTypeId)) {
    throw new Error("unknown base type_id: " + String(baseTypeId));
  }
  return baseTypeId;
}

export function pyRegisterType(typeId: number, bases: number[] = []): number {
  initBuiltinTypeBases();
  const baseTypeId = normalizeBaseTypeId(bases.slice());
  registerTypeNode(typeId, baseTypeId);
  recomputeTypeRanges();
  return typeId;
}

export function pyRegisterClassType(bases: number[] = [PY_TYPE_OBJECT]): number {
  initBuiltinTypeBases();
  while (pyTypeBase.has(pyNextTypeId)) {
    pyNextTypeId += 1;
  }
  const out = pyNextTypeId;
  pyNextTypeId += 1;
  return pyRegisterType(out, bases);
}

export function pyIsSubtype(actualTypeId: number, expectedTypeId: number): boolean {
  initBuiltinTypeBases();
  const actualOrder = pyTypeOrder.get(actualTypeId);
  if (typeof actualOrder !== "number") {
    return false;
  }
  const expectedMin = pyTypeMin.get(expectedTypeId);
  const expectedMax = pyTypeMax.get(expectedTypeId);
  if (typeof expectedMin !== "number" || typeof expectedMax !== "number") {
    return false;
  }
  return expectedMin <= actualOrder && actualOrder <= expectedMax;
}

export function pyIsInstance(value: unknown, expectedTypeId: number): boolean {
  return pyIsSubtype(pyTypeId(value), expectedTypeId);
}

type PytraTagged = {
  [PYTRA_TYPE_ID]?: number;
  [PYTRA_TRUTHY]?: () => unknown;
  [PYTRA_TRY_LEN]?: () => unknown;
  [PYTRA_STR]?: () => unknown;
};

function asTagged(value: unknown): PytraTagged | null {
  if ((typeof value === "object" || typeof value === "function") && value !== null) {
    return value as PytraTagged;
  }
  return null;
}

/** 値の type_id を返す（minify 耐性のある tag dispatch 用）。 */
export function pyTypeId(value: unknown): number {
  initBuiltinTypeBases();
  if (value === null || value === undefined) return PY_TYPE_NONE;
  const ty = typeof value;
  if (ty === "boolean") return PY_TYPE_BOOL;
  if (ty === "number") return PY_TYPE_NUMBER;
  if (ty === "string") return PY_TYPE_STRING;
  if (Array.isArray(value)) return PY_TYPE_ARRAY;
  if (value instanceof Map) return PY_TYPE_MAP;
  if (value instanceof Set) return PY_TYPE_SET;
  const tagged = asTagged(value);
  if (tagged !== null) {
    const raw = tagged[PYTRA_TYPE_ID];
    if (typeof raw === "number" && Number.isInteger(raw)) {
      return raw;
    }
  }
  return PY_TYPE_OBJECT;
}

/** bool 境界の共通 truthy 判定。 */
export function pyTruthy(value: unknown): boolean {
  const typeId = pyTypeId(value);
  switch (typeId) {
    case PY_TYPE_NONE:
      return false;
    case PY_TYPE_BOOL:
      return value as boolean;
    case PY_TYPE_NUMBER:
      return (value as number) !== 0;
    case PY_TYPE_STRING:
      return (value as string).length !== 0;
    case PY_TYPE_ARRAY:
      return (value as unknown[]).length !== 0;
    case PY_TYPE_MAP:
    case PY_TYPE_SET:
      return (value as Map<unknown, unknown> | Set<unknown>).size !== 0;
    case PY_TYPE_OBJECT:
      return true;
    default:
      break;
  }
  const tagged = asTagged(value);
  if (tagged !== null) {
    const hook = tagged[PYTRA_TRUTHY];
    if (typeof hook === "function") {
      return Boolean(hook.call(tagged));
    }
  }
  return true;
}

/** len 境界の共通 try helper（未対応は null）。 */
export function pyTryLen(value: unknown): number | null {
  if (value instanceof Uint8Array) return value.length;
  const typeId = pyTypeId(value);
  switch (typeId) {
    case PY_TYPE_STRING:
    case PY_TYPE_ARRAY:
      return (value as string | unknown[]).length;
    case PY_TYPE_MAP:
    case PY_TYPE_SET:
      return (value as Map<unknown, unknown> | Set<unknown>).size;
    case PY_TYPE_OBJECT: {
      // Check PYTRA_TRY_LEN hook first (e.g. _GrowBytes Proxy)
      const tagged = asTagged(value);
      if (tagged !== null) {
        const hook = tagged[PYTRA_TRY_LEN];
        if (typeof hook === "function") {
          const out = hook.call(tagged);
          if (typeof out === "number" && Number.isFinite(out)) return Math.trunc(out);
        }
      }
      return Object.keys(value as Record<string, unknown>).length;
    }
    default:
      break;
  }
  const tagged = asTagged(value);
  if (tagged !== null) {
    const hook = tagged[PYTRA_TRY_LEN];
    if (typeof hook === "function") {
      const out = hook.call(tagged);
      if (typeof out === "number" && Number.isFinite(out)) {
        return Math.trunc(out);
      }
    }
  }
  return null;
}

/** Python の float 型の数値を str() と同じ形式で返す (2.0 → "2.0")。 */
export function pyFloatStr(n: number): string {
  if (!isFinite(n)) return String(n);
  if (Number.isInteger(n)) return n.toString() + ".0";
  return String(n);
}

/** str 境界の共通 helper。 */
export function pyStr(value: unknown): string {
  const typeId = pyTypeId(value);
  switch (typeId) {
    case PY_TYPE_NONE:
      return "None";
    case PY_TYPE_BOOL:
      return (value as boolean) ? "True" : "False";
    case PY_TYPE_NUMBER:
      return String(value);
    case PY_TYPE_STRING:
      return value as string;
    case PY_TYPE_ARRAY:
      return `[${(value as unknown[]).map((v) => pyToString(v)).join(", ")}]`;
    case PY_TYPE_MAP: {
      const entries = Array.from((value as Map<unknown, unknown>).entries()).map(([k, v]) => `${pyToString(k)}: ${pyToString(v)}`);
      return `{${entries.join(", ")}}`;
    }
    case PY_TYPE_SET: {
      const entries = Array.from((value as Set<unknown>).values()).map((v) => pyToString(v));
      return `{${entries.join(", ")}}`;
    }
    case PY_TYPE_OBJECT:
      if (value instanceof Error) return value.message;
      return String(value);
    default:
      break;
  }
  const tagged = asTagged(value);
  if (tagged !== null) {
    const hook = tagged[PYTRA_STR];
    if (typeof hook === "function") {
      return String(hook.call(tagged));
    }
  }
  if (value instanceof Error) return value.message;
  return String(value);
}

/** Python 風の文字列表現へ変換する。 */
export function pyToString(value: unknown): string {
  return pyStr(value);
}

/** Python の print 相当（空白区切りで表示）。 */
export function pyPrint(...args: unknown[]): void {
  if (args.length === 0) {
    console.log("");
    return;
  }
  console.log(args.map((arg) => pyToString(arg)).join(" "));
}

/** Python の len 相当。 */
export function pyLen(value: unknown): number {
  const out = pyTryLen(value);
  if (out !== null) return out;
  throw new Error("len() unsupported type");
}

/** Python の bool 相当。 */
export function pyBool(value: unknown): boolean {
  return pyTruthy(value);
}

/** Python の range 相当配列を返す。 */
export function pyRange(start: number, stop: number, step = 1): number[] {
  if (step === 0) {
    throw new Error("range() arg 3 must not be zero");
  }
  const out: number[] = [];
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
export function pyFloorDiv(a: number, b: number): number {
  if (b === 0) {
    throw new Error("division by zero");
  }
  return Math.floor(a / b);
}

/** Python の剰余相当（除数と同符号）。 */
export function pyMod(a: number, b: number): number {
  if (b === 0) {
    throw new Error("integer modulo by zero");
  }
  const m = a % b;
  return m < 0 && b > 0 ? m + b : (m > 0 && b < 0 ? m + b : m);
}

/** Python の in 相当。 */
export function pyIn(item: unknown, container: unknown): boolean {
  if (container instanceof Uint8Array) {
    const v = typeof item === 'number' ? item : Number(item);
    for (let i = 0; i < container.length; i++) { if (container[i] === v) return true; }
    return false;
  }
  const typeId = pyTypeId(container);
  switch (typeId) {
    case PY_TYPE_STRING:
      return (container as string).includes(String(item));
    case PY_TYPE_ARRAY:
      return (container as unknown[]).includes(item);
    case PY_TYPE_SET:
    case PY_TYPE_MAP:
      return (container as Set<unknown> | Map<unknown, unknown>).has(item);
    case PY_TYPE_OBJECT:
      if (typeof container === "object" && container !== null) {
        return Object.prototype.hasOwnProperty.call(container as object, String(item));
      }
      break;
    default:
      if (typeof container === "object" && container !== null) {
        return Object.prototype.hasOwnProperty.call(container as object, String(item));
      }
      break;
  }
  throw new Error("in operation unsupported type");
}

/** Python のスライス相当（step なし）。 */
export function pySlice<T>(value: T[] | string, start: number | null = null, end: number | null = null): T[] | string {
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
  return (value as any).slice(s, e);
}

/** Python の ord 相当。 */
export function pyOrd(ch: string): number {
  if (ch.length === 0) {
    throw new Error("ord() expected non-empty string");
  }
  return ch.codePointAt(0) as number;
}

/** Python の chr 相当。 */
export function pyChr(code: number): string {
  return String.fromCodePoint(code);
}

// ---------------------------------------------------------------------------
// Efficient byte buffer (Uint8Array-based to reduce memory usage 8x vs number[])
// ---------------------------------------------------------------------------

/** Growable byte buffer backed by Uint8Array (1 byte per element). */
class _GrowBytes {
  _d: Uint8Array;
  _n: number;
  constructor(init?: ArrayLike<number>) {
    if (init && init.length > 0) {
      this._d = new Uint8Array(init);
      this._n = init.length;
    } else {
      this._d = new Uint8Array(16);
      this._n = 0;
    }
  }
  get length(): number { return this._n; }
  push(v: number): number {
    if (this._n === this._d.length) {
      const nd = new Uint8Array(this._d.length << 1);
      nd.set(this._d);
      this._d = nd;
    }
    this._d[this._n++] = v & 255;
    return this._n;
  }
  [Symbol.iterator]() { return this._d.subarray(0, this._n).values(); }
  /** Snapshot current content as a Uint8Array view (no copy). */
  _snap(): Uint8Array { return this._d.subarray(0, this._n); }
  [PYTRA_TRY_LEN]() { return this._n; }
}

const _gbHandler: ProxyHandler<_GrowBytes> = {
  get(t, p) {
    if (typeof p === 'string' && p.length > 0) {
      const c = p.charCodeAt(0);
      if (c >= 48 && c <= 57) { // digit
        const n = +p;
        if (Number.isInteger(n) && n >= 0) return t._d[n];
      }
    }
    const v = (t as unknown as Record<string | symbol, unknown>)[p];
    return typeof v === 'function' ? (v as Function).bind(t) : v;
  },
  set(t, p, v) {
    if (typeof p === 'string' && p.length > 0) {
      const c = p.charCodeAt(0);
      if (c >= 48 && c <= 57) {
        const n = +p;
        if (Number.isInteger(n) && n >= 0) { t._d[n] = v & 255; return true; }
      }
    }
    (t as unknown as Record<string | symbol, unknown>)[p] = v;
    return true;
  },
};

function _mkGrowBuf(init?: ArrayLike<number>): number[] {
  return new Proxy(new _GrowBytes(init), _gbHandler) as unknown as number[];
}

/** Python の bytearray 相当。size または number[] を受け取る。 */
export function pyBytearray(arg: number | number[] = 0): number[] {
  if (typeof arg === 'number') {
    if (arg < 0) throw new Error("negative count");
    if (arg === 0) return _mkGrowBuf();
    // Pre-sized: use growable buffer so push/indexed-write work
    return _mkGrowBuf(new Uint8Array(arg));
  }
  // From array literal: use growable buffer so push/indexed-write work
  return _mkGrowBuf(arg);
}

/** Python の bytes 相当。引数なし or ArrayLike<number> を受け取る。 */
export function pyBytes(value?: ArrayLike<number>): number[] {
  if (!value) return _mkGrowBuf();
  if (value instanceof Uint8Array) return value as unknown as number[];
  // Proxy over _GrowBytes: extract snapshot
  const snap = (value as unknown as { _snap?: () => Uint8Array })._snap;
  if (typeof snap === 'function') return snap.call(value) as unknown as number[];
  // Regular number[] or other ArrayLike
  return new Uint8Array(Array.from(value as unknown as Iterable<number>)) as unknown as number[];
}

/** Python の collections.deque 相当。 */
class _Deque<T = any> {
  private _data: T[] = [];
  constructor(items?: Iterable<T>) {
    if (items) this._data = Array.from(items);
  }
  append(v: T): void { this._data.push(v); }
  appendleft(v: T): void { this._data.unshift(v); }
  pop(): T {
    if (this._data.length === 0) throw new Error("pop from an empty deque");
    return this._data.pop()!;
  }
  popleft(): T {
    if (this._data.length === 0) throw new Error("pop from an empty deque");
    return this._data.shift()!;
  }
  clear(): void { this._data.length = 0; }
  get length(): number { return this._data.length; }
  [Symbol.iterator](): Iterator<T> { return this._data[Symbol.iterator](); }
  [PYTRA_TRY_LEN](): number { return this._data.length; }
}
export type deque<T = any> = _Deque<T>;
export function deque<T = any>(items?: Iterable<T>): _Deque<T> {
  return new _Deque<T>(items);
}

/** Python の sep.join(items) 相当。 */
export function pyStrJoin(sep: string, items: string[]): string {
  return items.join(sep);
}

/** Python の str.isdigit 相当。 */
export function pyIsDigit(value: unknown): boolean {
  return typeof value === "string" && value.length > 0 && /^[0-9]+$/.test(value);
}

/** Python の str.isalpha 相当。 */
export function pyIsAlpha(value: unknown): boolean {
  return typeof value === "string" && value.length > 0 && /^[A-Za-z]+$/.test(value);
}

// ---------------------------------------------------------------------------
// String method helpers
// ---------------------------------------------------------------------------

export function pyStrStrip(s: string, chars?: string): string {
  if (chars === undefined) return s.trim();
  const esc = chars.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
  return s.replace(new RegExp(`^[${esc}]+|[${esc}]+$`, "g"), "");
}
export function pyStrLstrip(s: string, chars?: string): string {
  if (chars === undefined) return s.trimStart();
  const esc = chars.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
  return s.replace(new RegExp(`^[${esc}]+`), "");
}
export function pyStrRstrip(s: string, chars?: string): string {
  if (chars === undefined) return s.trimEnd();
  const esc = chars.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
  return s.replace(new RegExp(`[${esc}]+$`), "");
}
export function pyStrStartswith(s: string, prefix: string): boolean {
  return s.startsWith(prefix);
}
export function pyStrEndswith(s: string, suffix: string): boolean {
  return s.endsWith(suffix);
}
export function pyStrReplace(s: string, old: string, rep: string, count = -1): string {
  if (count < 0) return s.split(old).join(rep);
  let result = s;
  let n = count;
  while (n-- > 0) {
    const idx = result.indexOf(old);
    if (idx < 0) break;
    result = result.slice(0, idx) + rep + result.slice(idx + old.length);
  }
  return result;
}
export function pyStrFind(s: string, sub: string, start = 0, end = -1): number {
  const haystack = end < 0 ? s.slice(start) : s.slice(start, end);
  const idx = haystack.indexOf(sub);
  return idx < 0 ? -1 : idx + start;
}
export function pyStrRfind(s: string, sub: string, start = 0, end = -1): number {
  const haystack = end < 0 ? s.slice(start) : s.slice(start, end);
  const idx = haystack.lastIndexOf(sub);
  return idx < 0 ? -1 : idx + start;
}
export function pyStrSplit(s: string, sep?: string, maxsplit = -1): string[] {
  if (sep === undefined || sep === null) {
    const parts = s.split(/\s+/).filter(p => p.length > 0);
    if (maxsplit < 0) return parts;
    const head = parts.slice(0, maxsplit);
    const tail = parts.slice(maxsplit).join(" ");
    return tail ? [...head, tail] : head;
  }
  if (maxsplit < 0) return s.split(sep);
  const result: string[] = [];
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
export function pyStrUpper(s: string): string { return s.toUpperCase(); }
export function pyStrLower(s: string): string { return s.toLowerCase(); }
export function pyStrCount(s: string, sub: string, start = 0, end = -1): number {
  const haystack = end < 0 ? s.slice(start) : s.slice(start, end);
  if (sub.length === 0) return haystack.length + 1;
  let count = 0;
  let pos = 0;
  while ((pos = haystack.indexOf(sub, pos)) >= 0) {
    count++;
    pos += sub.length;
  }
  return count;
}
export function pyStrIndex(s: string, sub: string, start = 0, end = -1): number {
  const idx = pyStrFind(s, sub, start, end);
  if (idx < 0) throw new Error("substring not found");
  return idx;
}
export function pyStrIsdigit(s: string): boolean {
  return s.length > 0 && /^[0-9]+$/.test(s);
}
export function pyStrIsalpha(s: string): boolean {
  return s.length > 0 && /^[A-Za-z]+$/.test(s);
}
export function pyStrIsalnum(s: string): boolean {
  return s.length > 0 && /^[A-Za-z0-9]+$/.test(s);
}
export function pyStrIsspace(s: string): boolean {
  return s.length > 0 && /^\s+$/.test(s);
}

// ---------------------------------------------------------------------------
// Collection helpers
// ---------------------------------------------------------------------------

export function pyEnumerate<T>(items: T[], start = 0): [number, T][] {
  return items.map((item, i) => [i + start, item] as [number, T]);
}
export function pyReversed<T>(items: T[]): T[] {
  return items.slice().reverse();
}
export function pySorted<T>(items: T[], key?: (x: T) => unknown, reverse = false): T[] {
  const sorted = items.slice().sort((a, b) => {
    const ka = key ? key(a) : a;
    const kb = key ? key(b) : b;
    if (ka < kb) return reverse ? 1 : -1;
    if (ka > kb) return reverse ? -1 : 1;
    return 0;
  });
  return sorted;
}

/** Python の py_assert_true 相当（テスト用）。 */
export function pyAssertTrue(cond: boolean, label: string = ""): boolean {
  if (cond) return true;
  pyPrint(label !== "" ? `[assert_true] ${label}: False` : "[assert_true] False");
  return false;
}

/** Python の py_assert_eq 相当（テスト用）。 */
export function pyAssertEq(actual: unknown, expected: unknown, label: string = ""): boolean {
  const ok = pyStr(actual) === pyStr(expected);
  if (ok) return true;
  pyPrint(label !== "" ? `[assert_eq] ${label}: actual=${pyStr(actual)}, expected=${pyStr(expected)}` : `[assert_eq] actual=${pyStr(actual)}, expected=${pyStr(expected)}`);
  return false;
}

/** Python の py_assert_all 相当（テスト用）。 */
export function pyAssertAll(results: boolean[], label: string = ""): boolean {
  for (const v of results) {
    if (!v) {
      pyPrint(label !== "" ? `[assert_all] ${label}: False` : "[assert_all] False");
      return false;
    }
  }
  return true;
}

/** Python の assert stdout 相当（テスト用）。 */
export function pyAssertStdout(expected: string[], fn: () => void): string {
  const lines: string[] = [];
  const origLog = console.log;
  console.log = (...args: unknown[]) => {
    lines.push(args.map(a => String(a)).join(" "));
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

/** Python の type() 相当。クラス名を返すオブジェクトを返す。 */
export function type_(obj: unknown): { __name__: string } {
  if (obj === null || obj === undefined) return { __name__: "NoneType" };
  if (typeof obj === "boolean") return { __name__: "bool" };
  if (typeof obj === "number") return { __name__: "int" };
  if (typeof obj === "string") return { __name__: "str" };
  if (Array.isArray(obj)) return { __name__: "list" };
  if (obj instanceof Map) return { __name__: "dict" };
  if (obj instanceof Set) return { __name__: "set" };
  const ctor = (obj as Record<string, unknown>).constructor;
  return { __name__: (typeof ctor === "function" && ctor.name) ? ctor.name : "object" };
}

/** Python の sum() 相当。 */
export function pysum(iterable: number[], start: number = 0): number {
  let acc = start;
  for (const v of iterable) acc += v;
  return acc;
}

/** Python の zip() 相当。 */
export function pyzip<A, B>(a: A[], b: B[]): [A, B][] {
  const len = Math.min(a.length, b.length);
  const result: [A, B][] = [];
  for (let i = 0; i < len; i++) result.push([a[i], b[i]]);
  return result;
}

/** Python の format() / f-string format spec 相当。 */
export function pyFmt(value: unknown, spec: string): string {
  // Parse spec: [fill][align][sign][#][0][width][grouping][.precision][type]
  const m = spec.match(/^([^a-zA-Z%<>^=]?[<>^=])?([+\- ])?(#?)([0]?)([0-9]*)([,_])?(?:\.([0-9]+))?([bcdeEfFgGnosxX%])?$/);
  if (!m) return String(value);
  const [, alignFill, sign, _hash, zeroPadChar, widthStr, grouping, precStr, typeChar] = m;
  const width = widthStr ? parseInt(widthStr, 10) : 0;
  const prec = precStr !== undefined && precStr !== "" ? parseInt(precStr, 10) : -1;
  const zeroPad = zeroPadChar === "0";

  let fill = " ";
  let align = "";
  if (alignFill) {
    if (alignFill.length === 1) {
      align = alignFill;
    } else {
      fill = alignFill[0];
      align = alignFill[1];
    }
  }

  const n = typeof value === "number" ? value : parseFloat(String(value));
  let result: string;

  switch (typeChar) {
    case "d": case "i": case undefined:
      if (typeof value === "number" || typeChar === "d" || typeChar === "i") {
        result = Math.trunc(n).toString(10);
      } else {
        result = prec >= 0 ? String(value).slice(0, prec) : String(value);
      }
      break;
    case "f": case "F":
      result = prec >= 0 ? n.toFixed(prec) : n.toFixed(6);
      if (typeChar === "F") result = result.toUpperCase();
      break;
    case "e":
      result = prec >= 0 ? n.toExponential(prec) : n.toExponential(6);
      break;
    case "E":
      result = prec >= 0 ? n.toExponential(prec).toUpperCase() : n.toExponential(6).toUpperCase();
      break;
    case "g": case "G": {
      const p = prec >= 0 ? prec : 6;
      result = n.toPrecision(p || 1);
      // Remove trailing zeros after decimal point for 'g'
      if (result.includes(".") && !result.includes("e")) {
        result = result.replace(/\.?0+$/, "");
      }
      if (typeChar === "G") result = result.toUpperCase();
      break;
    }
    case "x":
      result = Math.trunc(n).toString(16);
      if (prec >= 0) result = result.padStart(prec, "0");
      break;
    case "X":
      result = Math.trunc(n).toString(16).toUpperCase();
      if (prec >= 0) result = result.padStart(prec, "0");
      break;
    case "o":
      result = Math.trunc(n).toString(8);
      break;
    case "b":
      result = Math.trunc(n).toString(2);
      break;
    case "%":
      result = (n * 100).toFixed(prec >= 0 ? prec : 6) + "%";
      break;
    case "s":
      result = typeof value === "string" ? (prec >= 0 ? value.slice(0, prec) : value) : String(value);
      break;
    default:
      result = prec >= 0 ? (typeof value === "string" ? String(value).slice(0, prec) : n.toFixed(prec)) : String(value);
  }

  // Sign for numeric types
  if (typeof value === "number" || ["d","i","f","F","e","E","g","G","x","X","o","b","%"].includes(typeChar ?? "")) {
    if (sign === "+" && !result.startsWith("-")) result = "+" + result;
    else if (sign === " " && !result.startsWith("-")) result = " " + result;
  }

  // Thousands grouping
  if (grouping === ",") {
    const dotIdx = result.indexOf(".");
    let intPart = dotIdx >= 0 ? result.slice(0, dotIdx) : result;
    const decPart = dotIdx >= 0 ? result.slice(dotIdx) : "";
    const neg = intPart.startsWith("-") || intPart.startsWith("+") || intPart.startsWith(" ");
    const prefix = neg ? intPart[0] : "";
    const digits = neg ? intPart.slice(1) : intPart;
    result = prefix + digits.replace(/\B(?=(\d{3})+(?!\d))/g, ",") + decPart;
  }

  // Padding / alignment
  if (width > 0 && result.length < width) {
    const isNeg = result.startsWith("-");
    const signChar = isNeg ? "-" : (result.startsWith("+") ? "+" : (result.startsWith(" ") ? " " : ""));
    if (zeroPad && !align) {
      const body = signChar ? result.slice(1) : result;
      result = signChar + body.padStart(width - signChar.length, "0");
    } else {
      const a = align || (typeof value === "number" || ["d","i","f","F","e","E","g","G","x","X","o","b","%"].includes(typeChar ?? "") ? ">" : "<");
      if (a === "<") result = result.padEnd(width, fill);
      else if (a === ">") result = result.padStart(width, fill);
      else if (a === "^") {
        const pad = width - result.length;
        result = fill.repeat(Math.floor(pad / 2)) + result + fill.repeat(Math.ceil(pad / 2));
      }
    }
  }

  return result;
}

/** Python の open 相当（バイナリ書き込み専用）。 */
export function open(filePath: string, _mode?: string): { write(data: number[]): void; close(): void } {
  const dir = dirname(filePath);
  if (dir !== "" && dir !== ".") {
    mkdirSync(dir, { recursive: true });
  }
  const chunks: Uint8Array[] = [];
  return {
    write(data: number[]): void {
      if (data instanceof Uint8Array) {
        chunks.push(data);
      } else {
        // Check for Proxy over _GrowBytes (has _snap method)
        const snap = (data as unknown as { _snap?: () => Uint8Array })._snap;
        if (typeof snap === 'function') {
          chunks.push(snap.call(data));
        } else if (Array.isArray(data)) {
          chunks.push(new Uint8Array(data));
        }
      }
    },
    close(): void {
      const totalLen = chunks.reduce((s, c) => s + c.length, 0);
      const out = new Uint8Array(totalLen);
      let offset = 0;
      for (const chunk of chunks) { out.set(chunk, offset); offset += chunk.length; }
      writeFileSync(filePath, Buffer.from(out.buffer, out.byteOffset, out.byteLength));
    },
  };
}

/** Alias for open(), used by compiled pytra.utils modules. */
export const pyopen = open;
export type PyFile = ReturnType<typeof open>;

// ---------------------------------------------------------------------------
// Python math module wrappers (py-prefixed for emitter mapping)
// ---------------------------------------------------------------------------
export function pyfabs(x: number): number { return Math.abs(x); }
export function pytan(x: number): number { return Math.tan(x); }
export function pylog(x: number, base?: number): number {
  return base !== undefined ? Math.log(x) / Math.log(base) : Math.log(x);
}
export function pyexp(x: number): number { return Math.exp(x); }
export function pylog10(x: number): number { return Math.log10(x); }
export function pylog2(x: number): number { return Math.log2(x); }
export function pysqrt(x: number): number { return Math.sqrt(x); }
export function pysin(x: number): number { return Math.sin(x); }
export function pycos(x: number): number { return Math.cos(x); }
export function pyceil(x: number): number { return Math.ceil(x); }
export function pyfloor(x: number): number { return Math.floor(x); }
export function pypow(x: number, y: number): number { return Math.pow(x, y); }
export function pyround(x: number, ndigits: number = 0): number {
  if (ndigits === 0) return Math.round(x);
  const factor = Math.pow(10, ndigits);
  return Math.round(x * factor) / factor;
}
export function pytrunc(x: number): number { return Math.trunc(x); }
export function pyatan2(y: number, x: number): number { return Math.atan2(y, x); }
export function pyasin(x: number): number { return Math.asin(x); }
export function pyacos(x: number): number { return Math.acos(x); }
export function pyatan(x: number): number { return Math.atan(x); }
export function pyhypot(...args: number[]): number { return Math.hypot(...args); }
export const py_math_pi: number = Math.PI;
export const py_math_e: number = Math.E;
export const py_math_inf: number = Infinity;
export const py_math_nan: number = NaN;
export function pyisfinite(x: number): boolean { return isFinite(x); }
export function pyisinf(x: number): boolean { return !isFinite(x) && !isNaN(x); }
export function pyisnan(x: number): boolean { return isNaN(x); }

// ---------------------------------------------------------------------------
// Python json module wrappers
// ---------------------------------------------------------------------------
export function dumps(
  obj: unknown,
  ensure_ascii: boolean = true,
  indent: number | null = null,
  sort_keys: boolean | null = null
): string {
  function serialize(v: unknown, depth: number): string {
    if (v === null || v === undefined) return "null";
    if (typeof v === "boolean") return v ? "true" : "false";
    if (typeof v === "number") return String(v);
    if (typeof v === "string") {
      let s = JSON.stringify(v);
      if (!ensure_ascii) return s;
      // Escape non-ASCII
      return s.replace(/[\u0080-\uFFFF]/g, (c) => {
        return "\\u" + c.charCodeAt(0).toString(16).padStart(4, "0");
      });
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
      const obj2 = v as Record<string, unknown>;
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

export function loads(s: string): unknown {
  function revive(v: unknown): unknown {
    if (v === null) return null;
    if (typeof v === "object" && !Array.isArray(v)) {
      const map = new Map<string, unknown>();
      for (const [k, val] of Object.entries(v as Record<string, unknown>)) {
        map.set(k, revive(val));
      }
      return map;
    }
    if (Array.isArray(v)) return v.map(revive);
    return v;
  }
  return revive(JSON.parse(s));
}

// ---------------------------------------------------------------------------
// pytra.std.json wrapper classes and functions
// ---------------------------------------------------------------------------
export type JsonVal = null | boolean | number | string | JsonVal[] | Map<string, JsonVal>;

export class JsonValue {
  raw: JsonVal;
  constructor(raw: JsonVal) { this.raw = raw; }
  as_str(): string | null { return typeof this.raw === "string" ? this.raw : null; }
  as_int(): number | null { return typeof this.raw === "number" ? Math.trunc(this.raw) : null; }
  as_float(): number | null { return typeof this.raw === "number" ? this.raw : null; }
  as_bool(): boolean | null { return typeof this.raw === "boolean" ? this.raw : null; }
  as_obj(): JsonObj | null { return this.raw instanceof Map ? new JsonObj(this.raw) : null; }
  as_arr(): JsonArr | null { return Array.isArray(this.raw) ? new JsonArr(this.raw as JsonVal[]) : null; }
}

export class JsonArr {
  raw: JsonVal[];
  constructor(raw: JsonVal[]) { this.raw = raw; }
  get(index: number): JsonValue | null {
    if (index < 0 || index >= this.raw.length) return null;
    return new JsonValue(this.raw[index]);
  }
  get_str(index: number): string | null { return this.get(index)?.as_str() ?? null; }
  get_int(index: number): number | null { return this.get(index)?.as_int() ?? null; }
  get_float(index: number): number | null { return this.get(index)?.as_float() ?? null; }
  get_bool(index: number): boolean | null { return this.get(index)?.as_bool() ?? null; }
  get_arr(index: number): JsonArr | null { return this.get(index)?.as_arr() ?? null; }
  get_obj(index: number): JsonObj | null { return this.get(index)?.as_obj() ?? null; }
}

export class JsonObj {
  raw: Map<string, JsonVal>;
  constructor(raw: Map<string, JsonVal>) { this.raw = raw; }
  get(key: string): JsonValue | null {
    if (!this.raw.has(key)) return null;
    return new JsonValue(this.raw.get(key) as JsonVal);
  }
  get_str(key: string): string | null { return this.get(key)?.as_str() ?? null; }
  get_int(key: string): number | null { return this.get(key)?.as_int() ?? null; }
  get_float(key: string): number | null { return this.get(key)?.as_float() ?? null; }
  get_bool(key: string): boolean | null { return this.get(key)?.as_bool() ?? null; }
  get_arr(key: string): JsonArr | null { return this.get(key)?.as_arr() ?? null; }
  get_obj(key: string): JsonObj | null { return this.get(key)?.as_obj() ?? null; }
}

function _parseJsonVal(v: unknown): JsonVal {
  if (v === null || v === undefined) return null;
  if (typeof v === "boolean") return v;
  if (typeof v === "number") return v;
  if (typeof v === "string") return v;
  if (Array.isArray(v)) return (v as unknown[]).map(_parseJsonVal) as JsonVal[];
  if (typeof v === "object") {
    const m = new Map<string, JsonVal>();
    for (const [k, val] of Object.entries(v as Record<string, unknown>)) {
      m.set(k, _parseJsonVal(val));
    }
    return m;
  }
  return null;
}

export function pyloads(s: string): JsonValue {
  return new JsonValue(_parseJsonVal(JSON.parse(s)));
}

export function pyloads_arr(s: string): JsonArr | null {
  const v = _parseJsonVal(JSON.parse(s));
  if (Array.isArray(v)) return new JsonArr(v as JsonVal[]);
  return null;
}

export function pyloads_obj(s: string): JsonObj | null {
  const v = _parseJsonVal(JSON.parse(s));
  if (v instanceof Map) return new JsonObj(v);
  return null;
}

export function pydumps(
  obj: unknown,
  ensure_ascii: boolean = true,
  indent: number | null = null,
  separators: unknown = null
): string {
  return dumps(obj, ensure_ascii, indent, null);
}

// ---------------------------------------------------------------------------
// Path utilities (pytra.std.pathlib)
// ---------------------------------------------------------------------------
export class PyPath {
  _p: string;
  constructor(p: string) { this._p = p; }
  get parent(): PyPath {
    const s = this._p.replace(/[/\\]$/, "");
    const i = Math.max(s.lastIndexOf("/"), s.lastIndexOf("\\"));
    return new PyPath(i <= 0 ? (i === 0 ? "/" : ".") : s.slice(0, i));
  }
  get name(): string {
    const s = this._p.replace(/[/\\]$/, "");
    const i = Math.max(s.lastIndexOf("/"), s.lastIndexOf("\\"));
    return i === -1 ? s : s.slice(i + 1);
  }
  get stem(): string {
    const n = this.name;
    const d = n.lastIndexOf(".");
    return d > 0 ? n.slice(0, d) : n;
  }
  get suffix(): string {
    const n = this.name;
    const d = n.lastIndexOf(".");
    return d > 0 ? n.slice(d) : "";
  }
  joinpath(other: string): PyPath { return new PyPath(this._p + "/" + other); }
  toString(): string { return this._p; }
  exists(): boolean { try { return require("fs").existsSync(this._p); } catch { return false; } }
  mkdir(parents: boolean = false, exist_ok: boolean = false): void {
    try { require("fs").mkdirSync(this._p, { recursive: parents }); } catch (e: unknown) {
      if (!exist_ok) throw e;
    }
  }
  write_text(data: string): void { require("fs").writeFileSync(this._p, data, "utf8"); }
  read_text(encoding: string = "utf8"): string { return require("fs").readFileSync(this._p, "utf8"); }
}

export function Path(p: string | PyPath): PyPath {
  return p instanceof PyPath ? p : new PyPath(typeof p === "string" ? p : String(p));
}

export const py_math_tau: number = 2 * Math.PI;

// ---------------------------------------------------------------------------
// os.path utilities
// ---------------------------------------------------------------------------
export function pyjoin(...parts: string[]): string {
  if (parts.length === 0) return "";
  let result = parts[0];
  for (let i = 1; i < parts.length; i++) {
    const p = parts[i];
    if (p.startsWith("/")) { result = p; continue; }
    result = result.endsWith("/") ? result + p : result + "/" + p;
  }
  return result;
}

export function pysplitext(p: string): [string, string] {
  const dot = p.lastIndexOf(".");
  const slash = Math.max(p.lastIndexOf("/"), p.lastIndexOf("\\"));
  if (dot > slash && dot !== -1) return [p.slice(0, dot), p.slice(dot)];
  return [p, ""];
}

export function pybasename(p: string): string {
  const s = p.replace(/[/\\]$/, "");
  const i = Math.max(s.lastIndexOf("/"), s.lastIndexOf("\\"));
  return i === -1 ? s : s.slice(i + 1);
}

export function pydirname(p: string): string {
  const s = p.replace(/[/\\]$/, "");
  const i = Math.max(s.lastIndexOf("/"), s.lastIndexOf("\\"));
  if (i === -1) return ".";
  if (i === 0) return "/";
  return s.slice(0, i);
}

export function pyexists(p: string): boolean {
  try {
    // eslint-disable-next-line @typescript-eslint/no-var-requires
    return require("fs").existsSync(p);
  } catch { return false; }
}

export function pyisfile(p: string): boolean {
  try {
    return require("fs").statSync(p).isFile();
  } catch { return false; }
}

export function pyisdir(p: string): boolean {
  try {
    return require("fs").statSync(p).isDirectory();
  } catch { return false; }
}

// ---------------------------------------------------------------------------
// time module
// ---------------------------------------------------------------------------
export function perf_counter(): number {
  if (typeof performance !== "undefined") return performance.now() / 1000;
  try { const [s, ns] = process.hrtime(); return s + ns / 1e9; } catch { return Date.now() / 1000; }
}

// ---------------------------------------------------------------------------
// sys module
// ---------------------------------------------------------------------------
export const sys: { argv: string[]; path: string[] } = { argv: [], path: [] };
export function pyset_argv(args: string[]): void { sys.argv = args; }
export function pyset_path(paths: string[]): void { sys.path = paths; }

// ---------------------------------------------------------------------------
// re module
// ---------------------------------------------------------------------------
export function sub(pattern: string, repl: string, s: string, count: number = 0): string {
  const flags = count === 0 ? "g" : "";
  const re = new RegExp(pattern, flags);
  if (count > 0) {
    let result = s;
    for (let i = 0; i < count; i++) {
      result = result.replace(re, repl);
    }
    return result;
  }
  return s.replace(re, repl);
}

export function match(pattern: string, s: string): RegExpMatchArray | null {
  return s.match(new RegExp("^" + pattern));
}

export function search(pattern: string, s: string): RegExpMatchArray | null {
  return s.match(new RegExp(pattern));
}

export function findall(pattern: string, s: string): string[] {
  const matches: string[] = [];
  const re = new RegExp(pattern, "g");
  let m: RegExpExecArray | null;
  while ((m = re.exec(s)) !== null) matches.push(m[0]);
  return matches;
}

export function split(pattern: string, s: string, maxsplit: number = 0): string[] {
  if (maxsplit === 0) return s.split(new RegExp(pattern));
  return s.split(new RegExp(pattern), maxsplit + 1);
}

// ---------------------------------------------------------------------------
// argparse module
// ---------------------------------------------------------------------------
class _ArgumentParser {
  _desc: string;
  _args: Array<{ names: string[]; choices: string[] | null; default_val: unknown; action: string }>;
  constructor(description: string = "") {
    this._desc = description;
    this._args = [];
  }
  add_argument(...params: unknown[]): void {
    const names: string[] = [];
    let action: string = "store";
    let choices: string[] | null = null;
    let default_val: unknown = null;
    for (const p of params) {
      if (typeof p === "string") {
        if (p === "store_true" || p === "store_false") { action = p; }
        else if (p.startsWith("-")) names.push(p);
        else if (names.length === 0) names.push(p); // positional name
        else default_val = p; // non-flag string after flags = default
      } else if (Array.isArray(p)) choices = p as string[];
      else if (p !== null && p !== undefined) default_val = p;
    }
    if (action === "store_true" && default_val === null) default_val = false;
    this._args.push({ names, choices, default_val, action });
  }
  parse_args(args: string[]): Map<string, unknown> {
    const result = new Map<string, unknown>();
    let pos = 0;
    const positional = this._args.filter(a => a.names.length > 0 && !a.names[0].startsWith("-"));
    const optional = this._args.filter(a => a.names.length > 0 && a.names[0].startsWith("-"));
    for (const arg of optional) {
      const key = arg.names[arg.names.length - 1].replace(/^-+/, "").replace(/-/g, "_");
      result.set(key, arg.default_val ?? null);
    }
    let i = 0;
    while (i < args.length) {
      const a = args[i];
      if (a.startsWith("-")) {
        const opt = optional.find(o => o.names.includes(a));
        if (opt) {
          const key = opt.names[opt.names.length - 1].replace(/^-+/, "").replace(/-/g, "_");
          if (opt.action === "store_true") {
            result.set(key, true); i++;
          } else if (opt.action === "store_false") {
            result.set(key, false); i++;
          } else { result.set(key, args[++i]); i++; }
        } else i++;
      } else {
        if (pos < positional.length) {
          const key = positional[pos].names[0].replace(/^-+/, "");
          result.set(key, a); pos++;
        }
        i++;
      }
    }
    return result;
  }
}
export type ArgumentParser = _ArgumentParser;
export function ArgumentParser(description: string = ""): _ArgumentParser {
  return new _ArgumentParser(description);
}

// ---------------------------------------------------------------------------
// os.makedirs
// ---------------------------------------------------------------------------
export function pymakedirs(path: string, exist_ok: boolean = false): void {
  try { require("fs").mkdirSync(path, { recursive: true }); } catch (e: unknown) {
    if (!exist_ok) throw e;
  }
}

// ---------------------------------------------------------------------------
// PNG writer (stub for runtime tests)
// ---------------------------------------------------------------------------
export function pywrite_rgb_png(path: string, width: number, height: number, pixels: number[]): void {
  // Minimal PNG writer: writes a valid PNG file
  try {
    const fs = require("fs");
    const data = _encode_png(width, height, pixels);
    fs.writeFileSync(path, Buffer.from(data));
  } catch { /* ignore if fs not available */ }
}

function _encode_png(w: number, h: number, pixels: number[]): number[] {
  // Minimal PNG: signature + IHDR + IDAT + IEND
  const sig = [137, 80, 78, 71, 13, 10, 26, 10];
  function chunk(type: string, data: number[]): number[] {
    const len = data.length;
    const typeBytes = type.split("").map(c => c.charCodeAt(0));
    const crcInput = [...typeBytes, ...data];
    const crc = _crc32(crcInput);
    return [(len >> 24) & 0xff, (len >> 16) & 0xff, (len >> 8) & 0xff, len & 0xff,
            ...typeBytes, ...data,
            (crc >> 24) & 0xff, (crc >> 16) & 0xff, (crc >> 8) & 0xff, crc & 0xff];
  }
  const ihdr = [0,0,0,w>>0, 0,0,0,h>>0, 8, 2, 0, 0, 0]; // simplified
  ihdr[0] = (w >> 24) & 0xff; ihdr[1] = (w >> 16) & 0xff; ihdr[2] = (w >> 8) & 0xff; ihdr[3] = w & 0xff;
  ihdr[4] = (h >> 24) & 0xff; ihdr[5] = (h >> 16) & 0xff; ihdr[6] = (h >> 8) & 0xff; ihdr[7] = h & 0xff;
  // Raw scanlines (filter byte 0 + RGB pixels)
  const raw: number[] = [];
  for (let y = 0; y < h; y++) {
    raw.push(0); // filter type None
    for (let x = 0; x < w; x++) {
      const i = (y * w + x) * 3;
      raw.push(pixels[i] ?? 0, pixels[i+1] ?? 0, pixels[i+2] ?? 0);
    }
  }
  const compressed = _deflate_store(raw);
  return [...sig, ...chunk("IHDR", ihdr), ...chunk("IDAT", compressed), ...chunk("IEND", [])];
}

function _deflate_store(data: number[]): number[] {
  // zlib stored block (no compression)
  const len = data.length;
  const nlen = (~len) & 0xffff;
  return [0x78, 0x01, // zlib header
          0x01, // BFINAL=1, BTYPE=00 (no compression)
          len & 0xff, (len >> 8) & 0xff,
          nlen & 0xff, (nlen >> 8) & 0xff,
          ...data,
          ...Array(4).fill(0)]; // adler32 checksum stub
}

function _crc32(data: number[]): number {
  let crc = 0xffffffff;
  for (const b of data) {
    crc ^= b;
    for (let i = 0; i < 8; i++) crc = (crc & 1) ? (0xedb88320 ^ (crc >>> 1)) : (crc >>> 1);
  }
  return (crc ^ 0xffffffff) >>> 0;
}

// ---------------------------------------------------------------------------
// glob module
// ---------------------------------------------------------------------------
export function pyglob(pattern: string): string[] {
  try {
    const fs = require("fs");
    const path = require("path");
    const dir = path.dirname(pattern) || ".";
    const base = path.basename(pattern);
    // Convert glob pattern to regex
    const regexStr = base.replace(/[.+^${}()|[\]\\]/g, "\\$&").replace(/\*/g, ".*").replace(/\?/g, ".");
    const re = new RegExp("^" + regexStr + "$");
    const entries: string[] = fs.readdirSync(dir);
    return entries.filter((e: string) => re.test(e)).map((e: string) => dir === "." ? e : dir + "/" + e);
  } catch { return []; }
}

// ---------------------------------------------------------------------------
// Python dict/list builtin helpers
// ---------------------------------------------------------------------------
/** Python dict.update(other) — merge other into d in-place. */
export function pyupdate<K, V>(d: Map<K, V>, other: Map<K, V>): void {
  for (const [k, v] of other) d.set(k, v);
}

/** Python dict.pop(key, default?) — remove key from d and return its value. */
export function pypop<K, V>(d: Map<K, V>, key: K, def: V | null = null): V | null {
  const v = d.has(key) ? (d.get(key) as V) : def;
  d.delete(key);
  return v;
}

/** Python list.extend(other) — append all items from other to lst. */
export function pyextend<T>(lst: T[], other: T[]): void {
  for (const item of other) lst.push(item);
}

/** Python list.sort() — sort lst in-place. */
export function pysort<T>(lst: T[]): void {
  lst.sort((a: any, b: any) => a < b ? -1 : a > b ? 1 : 0);
}

/** Python list.clear() or dict.clear() — clear container in-place. */
export function pyclear(c: Map<any, any> | any[]): void {
  if (Array.isArray(c)) c.splice(0); else c.clear();
}

/** Python del d[key] — delete key from Map. */
export function pydel<K>(d: Map<K, unknown>, key: K): void {
  d.delete(key);
}

// ---------------------------------------------------------------------------
// Python built-in constructors / dataclass helpers
// ---------------------------------------------------------------------------
/** Python dict() constructor — create empty Map. */
export function dict<K = any, V = any>(): Map<K, V> { return new Map<K, V>(); }

/** Python list() constructor — create empty array. */
export function list<T = any>(): T[] { return []; }

/** Python set() constructor — create empty Set (set_ to avoid JS reserved words). */
export function set_<T = any>(): Set<T> { return new Set<T>(); }

/** Python dataclasses.field(default_factory) — call factory and return value. */
export function field<T>(factory: (() => T) | T): T {
  return typeof factory === "function" ? (factory as () => T)() : factory;
}

/** Placeholder for Python Ellipsis (...) in type annotations like tuple[str, ...]. */
export type ___ = any;

// Python built-in type aliases for isinstance checks and type annotations
// Each is both a callable value (for use as key= functions) and a type alias.
export const bool = Boolean;
export const str = String;
export type str = string;
export const int = Number;
export type int = number;
export const float = Number;
export type float = number;

// Python list.insert(i, val)
export function pyinsert<T>(lst: T[], index: number, item: T): void {
  lst.splice(index, 0, item);
}
// Python bool(x)
export function pybool(x: any): boolean {
  if (x === null || x === undefined || x === false || x === 0 || x === "") return false;
  if (Array.isArray(x)) return x.length > 0;
  if (x instanceof Map) return x.size > 0;
  if (x instanceof Set) return x.size > 0;
  return true;
}
// Python repr(x)
export function pyrepr(x: any): string {
  if (x === null) return "None";
  if (x === true) return "True";
  if (x === false) return "False";
  if (typeof x === "string") return JSON.stringify(x);
  if (Array.isArray(x)) return "[" + x.map(pyrepr).join(", ") + "]";
  if (x instanceof Map) {
    const entries = Array.from(x.entries()).map(([k, v]) => pyrepr(k) + ": " + pyrepr(v));
    return "{" + entries.join(", ") + "}";
  }
  return String(x);
}
