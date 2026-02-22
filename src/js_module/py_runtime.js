// Python 互換ランタイム（JavaScript版）の共通関数群。
// 将来的な Python -> JavaScript ネイティブ変換コードから利用する。

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

/** 値の type_id を返す（minify 耐性のある tag dispatch 用）。 */
function pyTypeId(value) {
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
  if ((typeof value === "object" || typeof value === "function") && value !== null) {
    const hook = value[PYTRA_TRY_LEN];
    if (typeof hook === "function") {
      const out = hook.call(value);
      if (typeof out === "number" && Number.isFinite(out)) {
        return Math.trunc(out);
      }
    }
  }
  return null;
}

/** str 境界の共通 helper。 */
function pyStr(value) {
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
  if (size < 0) {
    throw new Error("negative count");
  }
  return new Array(size).fill(0);
}

/** Python の bytes 相当（配列コピー）。 */
function pyBytes(value) {
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

module.exports = {
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
};
