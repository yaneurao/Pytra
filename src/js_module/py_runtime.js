// Python 互換ランタイム（JavaScript版）の共通関数群。
// 将来的な Python -> JavaScript ネイティブ変換コードから利用する。

/** Python 風の文字列表現へ変換する。 */
function pyToString(value) {
  if (value === null || value === undefined) {
    return "None";
  }
  if (typeof value === "boolean") {
    return value ? "True" : "False";
  }
  if (Array.isArray(value)) {
    return `[${value.map((v) => pyToString(v)).join(", ")}]`;
  }
  if (value instanceof Map) {
    const entries = Array.from(value.entries()).map(([k, v]) => `${pyToString(k)}: ${pyToString(v)}`);
    return `{${entries.join(", ")}}`;
  }
  if (value instanceof Set) {
    const entries = Array.from(value.values()).map((v) => pyToString(v));
    return `{${entries.join(", ")}}`;
  }
  return String(value);
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
  if (typeof value === "string" || Array.isArray(value)) {
    return value.length;
  }
  if (value instanceof Map || value instanceof Set) {
    return value.size;
  }
  if (typeof value === "object") {
    return Object.keys(value).length;
  }
  throw new Error("len() unsupported type");
}

/** Python の bool 相当。 */
function pyBool(value) {
  if (value === null || value === undefined) {
    return false;
  }
  if (typeof value === "boolean") {
    return value;
  }
  if (typeof value === "number") {
    return value !== 0;
  }
  if (typeof value === "string") {
    return value.length !== 0;
  }
  if (Array.isArray(value)) {
    return value.length !== 0;
  }
  if (value instanceof Map || value instanceof Set) {
    return value.size !== 0;
  }
  return true;
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
  if (typeof container === "string") {
    return container.includes(String(item));
  }
  if (Array.isArray(container)) {
    return container.includes(item);
  }
  if (container instanceof Set) {
    return container.has(item);
  }
  if (container instanceof Map) {
    return container.has(item);
  }
  if (typeof container === "object" && container !== null) {
    return Object.prototype.hasOwnProperty.call(container, String(item));
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
