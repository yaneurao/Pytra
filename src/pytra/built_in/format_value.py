"""Pure-Python format spec interpreter for f-string formatting.

Implements a subset of Python's Format Specification Mini-Language:
  [[fill]align][sign][z][#][0][width][grouping_option][.precision][type]

Supported types: d, f, e, E, g, G, x, X, o, b, s, n, %
Supported align: <, >, ^, =
Supported sign: +, -, space
Supported grouping: , (comma) and _ (underscore)

This module is the source-of-truth for all transpilation targets.
Backends with native format support can override with emitter-level optimization.
"""


def py_format_value(value: object, spec: str) -> str:
    """Format *value* according to Python format spec *spec*.

    Equivalent to ``format(value, spec)`` in Python.
    """
    if spec == "":
        return _to_str(value)
    parsed = _parse_format_spec(spec)
    raw = _format_core(value, parsed)
    return _apply_align(raw, parsed)


def py_format_conversion(value: object, conversion: str) -> str:
    """Apply f-string conversion flag (!s, !r, !a)."""
    if conversion == "s":
        return _to_str(value)
    if conversion == "r":
        return _repr_value(value)
    if conversion == "a":
        return _repr_value(value)
    return _to_str(value)


def _to_str(value: object) -> str:
    v: str = ""
    if isinstance(value, str):
        v = value
    elif isinstance(value, bool):
        if value:
            v = "True"
        else:
            v = "False"
    elif isinstance(value, int):
        v = _int_to_str(value)
    elif isinstance(value, float):
        v = _float_to_str(value)
    else:
        v = str(value)
    return v


def _repr_value(value: object) -> str:
    if isinstance(value, str):
        return "'" + value + "'"
    return _to_str(value)


def _int_to_str(value: int) -> str:
    if value < 0:
        return "-" + _int_to_str(-value)
    if value == 0:
        return "0"
    digits: list[str] = []
    n: int = value
    while n > 0:
        d: int = n % 10
        if d == 0:
            digits.append("0")
        elif d == 1:
            digits.append("1")
        elif d == 2:
            digits.append("2")
        elif d == 3:
            digits.append("3")
        elif d == 4:
            digits.append("4")
        elif d == 5:
            digits.append("5")
        elif d == 6:
            digits.append("6")
        elif d == 7:
            digits.append("7")
        elif d == 8:
            digits.append("8")
        else:
            digits.append("9")
        n = n // 10
    result: str = ""
    i: int = len(digits) - 1
    while i >= 0:
        result = result + digits[i]
        i = i - 1
    return result


def _float_to_str(value: float) -> str:
    # Delegate to runtime str() for basic float rendering.
    return str(value)


# -- Format spec parser --

def _parse_format_spec(spec: str) -> list[str]:
    """Parse format spec into [fill, align, sign, width, grouping, precision, type_char].

    Returns a list of 7 strings for selfhost compatibility (no dataclass).
    """
    fill: str = ""
    align: str = ""
    sign: str = ""
    width: str = ""
    grouping: str = ""
    precision: str = ""
    type_char: str = ""

    pos: int = 0
    n: int = len(spec)

    # Detect fill + align.
    if n >= 2 and (spec[1] == "<" or spec[1] == ">" or spec[1] == "^" or spec[1] == "="):
        fill = spec[0]
        align = spec[1]
        pos = 2
    elif n >= 1 and (spec[0] == "<" or spec[0] == ">" or spec[0] == "^" or spec[0] == "="):
        align = spec[0]
        pos = 1

    # Sign.
    if pos < n and (spec[pos] == "+" or spec[pos] == "-" or spec[pos] == " "):
        sign = spec[pos]
        pos = pos + 1

    # Skip 'z' flag (Python 3.11+).
    if pos < n and spec[pos] == "z":
        pos = pos + 1

    # Skip '#' (alternate form).
    if pos < n and spec[pos] == "#":
        pos = pos + 1

    # Skip '0' (zero-fill shorthand: equivalent to fill='0' align='=').
    if pos < n and spec[pos] == "0":
        if fill == "" and align == "":
            fill = "0"
            align = "="
        pos = pos + 1

    # Width.
    width_start: int = pos
    while pos < n and spec[pos] >= "0" and spec[pos] <= "9":
        pos = pos + 1
    if pos > width_start:
        width = spec[width_start:pos]

    # Grouping option.
    if pos < n and (spec[pos] == "," or spec[pos] == "_"):
        grouping = spec[pos]
        pos = pos + 1

    # Precision.
    if pos < n and spec[pos] == ".":
        pos = pos + 1
        prec_start: int = pos
        while pos < n and spec[pos] >= "0" and spec[pos] <= "9":
            pos = pos + 1
        precision = spec[prec_start:pos]

    # Type character.
    if pos < n:
        type_char = spec[pos]

    return [fill, align, sign, width, grouping, precision, type_char]


# Accessors for the parsed spec list.
def _spec_fill(p: list[str]) -> str:
    return p[0]

def _spec_align(p: list[str]) -> str:
    return p[1]

def _spec_sign(p: list[str]) -> str:
    return p[2]

def _spec_width(p: list[str]) -> str:
    return p[3]

def _spec_grouping(p: list[str]) -> str:
    return p[4]

def _spec_precision(p: list[str]) -> str:
    return p[5]

def _spec_type(p: list[str]) -> str:
    return p[6]


# -- Core formatting --

def _format_core(value: object, parsed: list[str]) -> str:
    tc: str = _spec_type(parsed)
    sign: str = _spec_sign(parsed)
    precision: str = _spec_precision(parsed)
    grouping: str = _spec_grouping(parsed)

    if tc == "s" or (tc == "" and isinstance(value, str)):
        s: str = _to_str(value)
        if precision != "":
            max_len: int = _str_to_int(precision)
            if len(s) > max_len:
                s = s[:max_len]
        return s

    if isinstance(value, int) and not isinstance(value, bool):
        return _format_int(value, tc, sign, grouping)

    if isinstance(value, float):
        return _format_float(value, tc, sign, precision, grouping)

    # Fallback: treat as string.
    return _to_str(value)


def _format_int(value: int, tc: str, sign: str, grouping: str) -> str:
    negative: bool = value < 0
    abs_val: int = -value if negative else value

    raw: str = ""
    if tc == "d" or tc == "" or tc == "n":
        raw = _int_to_str(abs_val)
    elif tc == "x":
        raw = _int_to_hex(abs_val, False)
    elif tc == "X":
        raw = _int_to_hex(abs_val, True)
    elif tc == "o":
        raw = _int_to_oct(abs_val)
    elif tc == "b":
        raw = _int_to_bin(abs_val)
    elif tc == "f" or tc == "e" or tc == "E" or tc == "g" or tc == "G":
        # int with float format spec: convert to float.
        return _format_float(float(value), tc, sign, "", grouping)
    else:
        raw = _int_to_str(abs_val)

    if grouping == ",":
        raw = _insert_grouping(raw, ",", 3)
    elif grouping == "_":
        if tc == "x" or tc == "X":
            raw = _insert_grouping(raw, "_", 4)
        elif tc == "b":
            raw = _insert_grouping(raw, "_", 4)
        elif tc == "o":
            raw = _insert_grouping(raw, "_", 4)
        else:
            raw = _insert_grouping(raw, "_", 3)

    return _apply_sign(raw, negative, sign)


def _format_float(value: float, tc: str, sign: str, precision: str, grouping: str) -> str:
    prec: int = 6
    if precision != "":
        prec = _str_to_int(precision)

    negative: bool = value < 0.0
    abs_val: float = -value if negative else value

    raw: str = ""
    if tc == "f" or tc == "F" or tc == "":
        raw = _float_fixed(abs_val, prec)
    elif tc == "e":
        raw = _float_exp(abs_val, prec, "e")
    elif tc == "E":
        raw = _float_exp(abs_val, prec, "E")
    elif tc == "g" or tc == "G":
        raw = _float_general(abs_val, prec, tc)
    elif tc == "%":
        raw = _float_fixed(abs_val * 100.0, prec) + "%"
    else:
        if tc == "" and precision != "":
            raw = _float_fixed(abs_val, prec)
        else:
            raw = _float_fixed(abs_val, prec)

    if grouping != "":
        # Apply grouping to integer part only.
        dot_pos: int = raw.find(".")
        if dot_pos >= 0:
            int_part: str = raw[:dot_pos]
            frac_part: str = raw[dot_pos:]
            raw = _insert_grouping(int_part, grouping, 3) + frac_part
        else:
            pct_pos: int = raw.find("%")
            if pct_pos >= 0:
                raw = _insert_grouping(raw[:pct_pos], grouping, 3) + "%"
            else:
                raw = _insert_grouping(raw, grouping, 3)

    return _apply_sign(raw, negative, sign)


# -- Numeric base conversions --

def _int_to_hex(value: int, upper: bool) -> str:
    if value == 0:
        return "0"
    hex_lower: str = "0123456789abcdef"
    hex_upper: str = "0123456789ABCDEF"
    table: str = hex_upper if upper else hex_lower
    digits: list[str] = []
    n: int = value
    while n > 0:
        digits.append(table[n % 16])
        n = n // 16
    result: str = ""
    i: int = len(digits) - 1
    while i >= 0:
        result = result + digits[i]
        i = i - 1
    return result


def _int_to_oct(value: int) -> str:
    if value == 0:
        return "0"
    digits: list[str] = []
    n: int = value
    while n > 0:
        digits.append(_int_to_str(n % 8))
        n = n // 8
    result: str = ""
    i: int = len(digits) - 1
    while i >= 0:
        result = result + digits[i]
        i = i - 1
    return result


def _int_to_bin(value: int) -> str:
    if value == 0:
        return "0"
    digits: list[str] = []
    n: int = value
    while n > 0:
        if n % 2 == 0:
            digits.append("0")
        else:
            digits.append("1")
        n = n // 2
    result: str = ""
    i: int = len(digits) - 1
    while i >= 0:
        result = result + digits[i]
        i = i - 1
    return result


# -- Float formatting helpers --

def _float_fixed(value: float, prec: int) -> str:
    """Format float as fixed-point with *prec* decimal places."""
    if prec == 0:
        rounded: int = int(value + 0.5)
        return _int_to_str(rounded)

    factor: float = 1.0
    i: int = 0
    while i < prec:
        factor = factor * 10.0
        i = i + 1
    rounded_val: int = int(value * factor + 0.5)
    int_part: int = rounded_val // int(factor)
    frac_part: int = rounded_val % int(factor)

    frac_str: str = _int_to_str(frac_part)
    # Zero-pad fraction to prec digits.
    while len(frac_str) < prec:
        frac_str = "0" + frac_str

    return _int_to_str(int_part) + "." + frac_str


def _float_exp(value: float, prec: int, e_char: str) -> str:
    """Format float in scientific notation."""
    if value == 0.0:
        frac: str = ""
        if prec > 0:
            frac = "." + "0" * prec
        return "0" + frac + e_char + "+00"

    exp: int = 0
    v: float = value
    if v >= 10.0:
        while v >= 10.0:
            v = v / 10.0
            exp = exp + 1
    elif v < 1.0:
        while v < 1.0:
            v = v * 10.0
            exp = exp - 1

    mantissa: str = _float_fixed(v, prec)
    exp_sign: str = "+" if exp >= 0 else "-"
    abs_exp: int = exp if exp >= 0 else -exp
    exp_str: str = _int_to_str(abs_exp)
    if len(exp_str) < 2:
        exp_str = "0" + exp_str
    return mantissa + e_char + exp_sign + exp_str


def _float_general(value: float, prec: int, tc: str) -> str:
    """Format float in general format (g/G)."""
    if prec == 0:
        prec = 1
    # Use fixed if exponent would be in range [-4, prec).
    if value == 0.0:
        return _float_fixed(value, prec - 1) if prec > 1 else "0"
    abs_val: float = value if value >= 0.0 else -value
    exp: int = 0
    v: float = abs_val
    if v >= 10.0:
        while v >= 10.0:
            v = v / 10.0
            exp = exp + 1
    elif v < 1.0 and v > 0.0:
        while v < 1.0:
            v = v * 10.0
            exp = exp - 1

    e_char: str = "e" if tc == "g" else "E"
    if exp >= -4 and exp < prec:
        fixed_prec: int = prec - 1 - exp
        if fixed_prec < 0:
            fixed_prec = 0
        result: str = _float_fixed(value, fixed_prec)
        # Strip trailing zeros after decimal.
        if "." in result:
            while result.endswith("0"):
                result = result[:-1]
            if result.endswith("."):
                result = result[:-1]
        return result
    return _float_exp(value, prec - 1, e_char)


# -- Sign and alignment helpers --

def _apply_sign(raw: str, negative: bool, sign: str) -> str:
    if negative:
        return "-" + raw
    if sign == "+":
        return "+" + raw
    if sign == " ":
        return " " + raw
    return raw


def _apply_align(raw: str, parsed: list[str]) -> str:
    width_str: str = _spec_width(parsed)
    if width_str == "":
        return raw
    width: int = _str_to_int(width_str)
    if len(raw) >= width:
        return raw

    fill: str = _spec_fill(parsed)
    if fill == "":
        fill = " "
    align: str = _spec_align(parsed)
    pad_count: int = width - len(raw)
    padding: str = fill * pad_count

    if align == "<":
        return raw + padding
    if align == "^":
        left: int = pad_count // 2
        right: int = pad_count - left
        return fill * left + raw + fill * right
    if align == "=":
        # Pad after sign.
        if len(raw) > 0 and (raw[0] == "-" or raw[0] == "+" or raw[0] == " "):
            return raw[0] + padding + raw[1:]
        return padding + raw
    # Default: right-align for numbers, left-align for strings.
    tc: str = _spec_type(parsed)
    if tc == "s":
        return raw + padding
    return padding + raw


# -- Utilities --

def _str_to_int(s: str) -> int:
    result: int = 0
    i: int = 0
    while i < len(s):
        c: str = s[i]
        d: int = 0
        if c == "1":
            d = 1
        elif c == "2":
            d = 2
        elif c == "3":
            d = 3
        elif c == "4":
            d = 4
        elif c == "5":
            d = 5
        elif c == "6":
            d = 6
        elif c == "7":
            d = 7
        elif c == "8":
            d = 8
        elif c == "9":
            d = 9
        result = result * 10 + d
        i = i + 1
    return result


def _insert_grouping(digits: str, sep: str, group_size: int) -> str:
    """Insert *sep* every *group_size* digits from the right."""
    n: int = len(digits)
    if n <= group_size:
        return digits
    parts: list[str] = []
    pos: int = n
    while pos > 0:
        start: int = pos - group_size
        if start < 0:
            start = 0
        parts.append(digits[start:pos])
        pos = start
    # Reverse parts.
    result: str = ""
    i: int = len(parts) - 1
    while i >= 0:
        if result != "":
            result = result + sep
        result = result + parts[i]
        i = i - 1
    return result
