// Python 互換ランタイム（TypeScript版）の共通関数群。
// 将来的な Python -> TypeScript ネイティブ変換コードから利用する。

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
const pyTypeBases = new Map<number, number[]>();

function initBuiltinTypeBases(): void {
  if (pyTypeBases.size > 0) {
    return;
  }
  pyTypeBases.set(PY_TYPE_NONE, []);
  pyTypeBases.set(PY_TYPE_BOOL, [PY_TYPE_NUMBER, PY_TYPE_OBJECT]);
  pyTypeBases.set(PY_TYPE_NUMBER, [PY_TYPE_OBJECT]);
  pyTypeBases.set(PY_TYPE_STRING, [PY_TYPE_OBJECT]);
  pyTypeBases.set(PY_TYPE_ARRAY, [PY_TYPE_OBJECT]);
  pyTypeBases.set(PY_TYPE_MAP, [PY_TYPE_OBJECT]);
  pyTypeBases.set(PY_TYPE_SET, [PY_TYPE_OBJECT]);
  pyTypeBases.set(PY_TYPE_OBJECT, []);
}

export function pyRegisterType(typeId: number, bases: number[] = []): number {
  initBuiltinTypeBases();
  pyTypeBases.set(typeId, bases.slice());
  return typeId;
}

export function pyRegisterClassType(bases: number[] = [PY_TYPE_OBJECT]): number {
  initBuiltinTypeBases();
  while (pyTypeBases.has(pyNextTypeId)) {
    pyNextTypeId += 1;
  }
  const out = pyNextTypeId;
  pyNextTypeId += 1;
  return pyRegisterType(out, bases);
}

export function pyIsSubtype(actualTypeId: number, expectedTypeId: number): boolean {
  initBuiltinTypeBases();
  if (actualTypeId === expectedTypeId) {
    return true;
  }
  if (!pyTypeBases.has(expectedTypeId)) {
    return false;
  }
  const visited = new Set<number>();
  const stack: number[] = [actualTypeId];
  while (stack.length > 0) {
    const cur = stack.pop();
    if (cur === undefined) {
      continue;
    }
    if (cur === expectedTypeId) {
      return true;
    }
    if (visited.has(cur)) {
      continue;
    }
    visited.add(cur);
    const bases = pyTypeBases.get(cur);
    if (!Array.isArray(bases)) {
      continue;
    }
    for (const b of bases) {
      if (b === expectedTypeId) {
        return true;
      }
      stack.push(b);
    }
  }
  return false;
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
  const typeId = pyTypeId(value);
  switch (typeId) {
    case PY_TYPE_STRING:
    case PY_TYPE_ARRAY:
      return (value as string | unknown[]).length;
    case PY_TYPE_MAP:
    case PY_TYPE_SET:
      return (value as Map<unknown, unknown> | Set<unknown>).size;
    case PY_TYPE_OBJECT:
      return Object.keys(value as Record<string, unknown>).length;
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

/** Python の bytearray 相当。 */
export function pyBytearray(size = 0): number[] {
  if (size < 0) {
    throw new Error("negative count");
  }
  return new Array<number>(size).fill(0);
}

/** Python の bytes 相当。 */
export function pyBytes(value: ArrayLike<number>): number[] {
  return Array.from(value);
}

/** Python の str.isdigit 相当。 */
export function pyIsDigit(value: unknown): boolean {
  return typeof value === "string" && value.length > 0 && /^[0-9]+$/.test(value);
}

/** Python の str.isalpha 相当。 */
export function pyIsAlpha(value: unknown): boolean {
  return typeof value === "string" && value.length > 0 && /^[A-Za-z]+$/.test(value);
}
