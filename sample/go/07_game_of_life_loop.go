// このファイルは自動生成です（Python -> Go native mode）。

// Go ネイティブ変換向け Python 互換ランタイム補助。

package main

import (
    "bytes"
    "compress/zlib"
    "fmt"
    "hash/crc32"
    "math"
    "os"
    "strconv"
    "strings"
    "time"
)

func pyToString(v any) string {
    switch x := v.(type) {
    case nil:
        return "None"
    case bool:
        if x {
            return "True"
        }
        return "False"
    case string:
        return x
    case int:
        return strconv.Itoa(x)
    case int64:
        return strconv.FormatInt(x, 10)
    case float64:
        return strconv.FormatFloat(x, 'f', -1, 64)
    case []any:
        parts := make([]string, 0, len(x))
        for _, it := range x {
            parts = append(parts, pyToString(it))
        }
        return "[" + strings.Join(parts, ", ") + "]"
    case map[any]any:
        parts := make([]string, 0, len(x))
        for k, v := range x {
            parts = append(parts, pyToString(k)+": "+pyToString(v))
        }
        return "{" + strings.Join(parts, ", ") + "}"
    default:
        return fmt.Sprint(x)
    }
}

func pyPrint(args ...any) {
    parts := make([]string, 0, len(args))
    for _, a := range args {
        parts = append(parts, pyToString(a))
    }
    fmt.Println(strings.Join(parts, " "))
}

func pyBool(v any) bool {
    switch x := v.(type) {
    case nil:
        return false
    case bool:
        return x
    case int:
        return x != 0
    case int64:
        return x != 0
    case float64:
        return x != 0.0
    case string:
        return x != ""
    case []any:
        return len(x) > 0
    case []byte:
        return len(x) > 0
    case map[any]any:
        return len(x) > 0
    default:
        return true
    }
}

func pyLen(v any) int {
    switch x := v.(type) {
    case string:
        return len([]rune(x))
    case []any:
        return len(x)
    case []byte:
        return len(x)
    case map[any]any:
        return len(x)
    default:
        panic("len() unsupported type")
    }
}

func pyRange(start, stop, step int) []any {
    if step == 0 {
        panic("range() step must not be zero")
    }
    out := []any{}
    if step > 0 {
        for i := start; i < stop; i += step {
            out = append(out, i)
        }
    } else {
        for i := start; i > stop; i += step {
            out = append(out, i)
        }
    }
    return out
}

func pyToFloat(v any) float64 {
    switch x := v.(type) {
    case int:
        return float64(x)
    case int64:
        return float64(x)
    case float64:
        return x
    case bool:
        if x {
            return 1.0
        }
        return 0.0
    default:
        panic("cannot convert to float")
    }
}

func pyToInt(v any) int {
    switch x := v.(type) {
    case int:
        return x
    case int64:
        return int(x)
    case float64:
        return int(math.Trunc(x))
    case bool:
        if x {
            return 1
        }
        return 0
    default:
        panic("cannot convert to int")
    }
}

func pyAdd(a, b any) any {
    if sa, ok := a.(string); ok {
        return sa + pyToString(b)
    }
    if sb, ok := b.(string); ok {
        return pyToString(a) + sb
    }
    _, aInt := a.(int)
    _, bInt := b.(int)
    if aInt && bInt {
        return pyToInt(a) + pyToInt(b)
    }
    return pyToFloat(a) + pyToFloat(b)
}
func pySub(a, b any) any {
    _, aInt := a.(int)
    _, bInt := b.(int)
    if aInt && bInt {
        return pyToInt(a) - pyToInt(b)
    }
    return pyToFloat(a) - pyToFloat(b)
}
func pyMul(a, b any) any {
    _, aInt := a.(int)
    _, bInt := b.(int)
    if aInt && bInt {
        return pyToInt(a) * pyToInt(b)
    }
    return pyToFloat(a) * pyToFloat(b)
}
func pyDiv(a, b any) any { return pyToFloat(a) / pyToFloat(b) }
func pyFloorDiv(a, b any) any { return int(math.Floor(pyToFloat(a) / pyToFloat(b))) }
func pyMod(a, b any) any {
    ai := pyToInt(a)
    bi := pyToInt(b)
    r := ai % bi
    if r != 0 && ((r > 0) != (bi > 0)) {
        r += bi
    }
    return r
}
func pyMin(values ...any) any {
    if len(values) == 0 {
        panic("min() arg is empty")
    }
    out := values[0]
    for i := 1; i < len(values); i++ {
        a := out
        b := values[i]
        if _, ok := a.(int); ok {
            if _, ok2 := b.(int); ok2 {
                ai := pyToInt(a)
                bi := pyToInt(b)
                if bi < ai {
                    out = bi
                }
                continue
            }
        }
        af := pyToFloat(a)
        bf := pyToFloat(b)
        if bf < af {
            out = bf
        }
    }
    return out
}
func pyMax(values ...any) any {
    if len(values) == 0 {
        panic("max() arg is empty")
    }
    out := values[0]
    for i := 1; i < len(values); i++ {
        a := out
        b := values[i]
        if _, ok := a.(int); ok {
            if _, ok2 := b.(int); ok2 {
                ai := pyToInt(a)
                bi := pyToInt(b)
                if bi > ai {
                    out = bi
                }
                continue
            }
        }
        af := pyToFloat(a)
        bf := pyToFloat(b)
        if bf > af {
            out = bf
        }
    }
    return out
}
func pyLShift(a, b any) any { return pyToInt(a) << uint(pyToInt(b)) }
func pyRShift(a, b any) any { return pyToInt(a) >> uint(pyToInt(b)) }
func pyBitAnd(a, b any) any { return pyToInt(a) & pyToInt(b) }
func pyBitOr(a, b any) any  { return pyToInt(a) | pyToInt(b) }
func pyBitXor(a, b any) any { return pyToInt(a) ^ pyToInt(b) }
func pyNeg(a any) any {
    if _, ok := a.(int); ok {
        return -pyToInt(a)
    }
    return -pyToFloat(a)
}

func pyEq(a, b any) bool { return pyToString(a) == pyToString(b) }
func pyNe(a, b any) bool { return !pyEq(a, b) }
func pyLt(a, b any) bool { return pyToFloat(a) < pyToFloat(b) }
func pyLe(a, b any) bool { return pyToFloat(a) <= pyToFloat(b) }
func pyGt(a, b any) bool { return pyToFloat(a) > pyToFloat(b) }
func pyGe(a, b any) bool { return pyToFloat(a) >= pyToFloat(b) }

func pyIn(item, container any) bool {
    switch c := container.(type) {
    case string:
        return strings.Contains(c, pyToString(item))
    case []any:
        for _, v := range c {
            if pyEq(v, item) {
                return true
            }
        }
        return false
    case map[any]any:
        _, ok := c[item]
        return ok
    default:
        return false
    }
}

func pyIter(value any) []any {
    switch v := value.(type) {
    case []any:
        return v
    case []byte:
        out := make([]any, 0, len(v))
        for _, b := range v {
            out = append(out, int(b))
        }
        return out
    case string:
        out := []any{}
        for _, ch := range []rune(v) {
            out = append(out, string(ch))
        }
        return out
    case map[any]any:
        out := []any{}
        for k := range v {
            out = append(out, k)
        }
        return out
    default:
        panic("iter unsupported")
    }
}

func pyTernary(cond bool, a any, b any) any {
    if cond {
        return a
    }
    return b
}

func pyListFromIter(value any) any {
    it := pyIter(value)
    out := make([]any, len(it))
    copy(out, it)
    return out
}

func pySlice(value any, start any, end any) any {
    s := 0
    e := 0
    switch v := value.(type) {
    case string:
        r := []rune(v)
        n := len(r)
        if start == nil {
            s = 0
        } else {
            s = pyToInt(start)
            if s < 0 {
                s += n
            }
            if s < 0 {
                s = 0
            }
            if s > n {
                s = n
            }
        }
        if end == nil {
            e = n
        } else {
            e = pyToInt(end)
            if e < 0 {
                e += n
            }
            if e < 0 {
                e = 0
            }
            if e > n {
                e = n
            }
        }
        if s > e {
            s = e
        }
        return string(r[s:e])
    case []any:
        n := len(v)
        if start == nil {
            s = 0
        } else {
            s = pyToInt(start)
            if s < 0 {
                s += n
            }
            if s < 0 {
                s = 0
            }
            if s > n {
                s = n
            }
        }
        if end == nil {
            e = n
        } else {
            e = pyToInt(end)
            if e < 0 {
                e += n
            }
            if e < 0 {
                e = 0
            }
            if e > n {
                e = n
            }
        }
        if s > e {
            s = e
        }
        out := make([]any, e-s)
        copy(out, v[s:e])
        return out
    default:
        panic("slice unsupported")
    }
}

func pyGet(value any, key any) any {
    switch v := value.(type) {
    case []any:
        i := pyToInt(key)
        if i < 0 {
            i += len(v)
        }
        return v[i]
    case []byte:
        i := pyToInt(key)
        if i < 0 {
            i += len(v)
        }
        return int(v[i])
    case map[any]any:
        return v[key]
    case string:
        r := []rune(v)
        i := pyToInt(key)
        if i < 0 {
            i += len(r)
        }
        return string(r[i])
    default:
        panic("subscript unsupported")
    }
}

func pySet(value any, key any, newValue any) {
    switch v := value.(type) {
    case []any:
        i := pyToInt(key)
        if i < 0 {
            i += len(v)
        }
        v[i] = newValue
    case []byte:
        i := pyToInt(key)
        if i < 0 {
            i += len(v)
        }
        v[i] = byte(pyToInt(newValue))
    case map[any]any:
        v[key] = newValue
    default:
        panic("setitem unsupported")
    }
}

func pyPop(lst *any, idx any) any {
    arr := (*lst).([]any)
    n := len(arr)
    i := n - 1
    if idx != nil {
        i = pyToInt(idx)
        if i < 0 {
            i += n
        }
    }
    val := arr[i]
    arr = append(arr[:i], arr[i+1:]...)
    *lst = arr
    return val
}

func pyPopAt(container any, key any, idx any) any {
    lst := pyGet(container, key)
    val := pyPop(&lst, idx)
    pySet(container, key, lst)
    return val
}

func pyOrd(v any) any {
    s := pyToString(v)
    r := []rune(s)
    return int(r[0])
}

func pyChr(v any) any { return string(rune(pyToInt(v))) }

func pyBytearray(size any) any {
    if size == nil {
        return []byte{}
    }
    n := pyToInt(size)
    out := make([]byte, n)
    return out
}

func pyBytes(v any) any { return v }

func pyAppend(seq any, value any) any {
    switch s := seq.(type) {
    case []any:
        return append(s, value)
    case []byte:
        return append(s, byte(pyToInt(value)))
    default:
        panic("append unsupported type")
    }
}

func pyIsDigit(v any) bool {
    s := pyToString(v)
    if s == "" {
        return false
    }
    for _, ch := range s {
        if ch < '0' || ch > '9' {
            return false
        }
    }
    return true
}

func pyIsAlpha(v any) bool {
    s := pyToString(v)
    if s == "" {
        return false
    }
    for _, ch := range s {
        if !((ch >= 'a' && ch <= 'z') || (ch >= 'A' && ch <= 'Z')) {
            return false
        }
    }
    return true
}

func pyTryCatch(body func() any, handler func(any) any, finalizer func()) (ret any) {
    defer finalizer()
    defer func() {
        if r := recover(); r != nil {
            ret = handler(r)
        }
    }()
    ret = body()
    return
}

// -------- time/math helper --------

func pyPerfCounter() any {
    return float64(time.Now().UnixNano()) / 1_000_000_000.0
}

func pyMathSqrt(v any) any { return math.Sqrt(pyToFloat(v)) }
func pyMathSin(v any) any  { return math.Sin(pyToFloat(v)) }
func pyMathCos(v any) any  { return math.Cos(pyToFloat(v)) }
func pyMathExp(v any) any  { return math.Exp(pyToFloat(v)) }
func pyMathFloor(v any) any { return float64(math.Floor(pyToFloat(v))) }
func pyMathPi() any        { return math.Pi }

// -------- png/gif helper --------

func pyToBytes(v any) []byte {
    switch x := v.(type) {
    case []byte:
        out := make([]byte, len(x))
        copy(out, x)
        return out
    case []any:
        out := make([]byte, len(x))
        for i, e := range x {
            out[i] = byte(pyToInt(e))
        }
        return out
    case string:
        return []byte(x)
    default:
        panic("cannot convert to bytes")
    }
}

func pyChunk(chunkType []byte, data []byte) []byte {
    var out bytes.Buffer
    n := uint32(len(data))
    out.Write([]byte{byte(n >> 24), byte(n >> 16), byte(n >> 8), byte(n)})
    out.Write(chunkType)
    out.Write(data)
    crc := crc32.ChecksumIEEE(append(append([]byte{}, chunkType...), data...))
    out.Write([]byte{byte(crc >> 24), byte(crc >> 16), byte(crc >> 8), byte(crc)})
    return out.Bytes()
}

func pyWriteRGBPNG(path any, width any, height any, pixels any) {
    w := pyToInt(width)
    h := pyToInt(height)
    raw := pyToBytes(pixels)
    expected := w * h * 3
    if len(raw) != expected {
        panic("pixels length mismatch")
    }

    scan := make([]byte, 0, h*(1+w*3))
    rowBytes := w * 3
    for y := 0; y < h; y++ {
        scan = append(scan, 0)
        start := y * rowBytes
        end := start + rowBytes
        scan = append(scan, raw[start:end]...)
    }

    var zbuf bytes.Buffer
    zw, _ := zlib.NewWriterLevel(&zbuf, 6)
    _, _ = zw.Write(scan)
    _ = zw.Close()
    idat := zbuf.Bytes()

    ihdr := []byte{
        byte(uint32(w) >> 24), byte(uint32(w) >> 16), byte(uint32(w) >> 8), byte(uint32(w)),
        byte(uint32(h) >> 24), byte(uint32(h) >> 16), byte(uint32(h) >> 8), byte(uint32(h)),
        8, 2, 0, 0, 0,
    }

    var png bytes.Buffer
    png.Write([]byte{0x89, 'P', 'N', 'G', '\r', '\n', 0x1a, '\n'})
    png.Write(pyChunk([]byte("IHDR"), ihdr))
    png.Write(pyChunk([]byte("IDAT"), idat))
    png.Write(pyChunk([]byte("IEND"), []byte{}))

    _ = os.WriteFile(pyToString(path), png.Bytes(), 0o644)
}

func pyLzwEncode(data []byte, minCodeSize int) []byte {
    if len(data) == 0 {
        return []byte{}
    }
    clearCode := 1 << minCodeSize
    endCode := clearCode + 1
    codeSize := minCodeSize + 1
    out := []byte{}
    bitBuffer := 0
    bitCount := 0

    emit := func(code int) {
        bitBuffer |= (code << bitCount)
        bitCount += codeSize
        for bitCount >= 8 {
            out = append(out, byte(bitBuffer&0xff))
            bitBuffer >>= 8
            bitCount -= 8
        }
    }

    emit(clearCode)
    for _, v := range data {
        emit(int(v))
        emit(clearCode)
    }
    emit(endCode)
    if bitCount > 0 {
        out = append(out, byte(bitBuffer&0xff))
    }
    return out
}

func pyGrayscalePalette() any {
    p := make([]byte, 0, 256*3)
    for i := 0; i < 256; i++ {
        p = append(p, byte(i), byte(i), byte(i))
    }
    return p
}

func pySaveGIF(path any, width any, height any, frames any, palette any, delayCS any, loop any) {
    w := pyToInt(width)
    h := pyToInt(height)
    frameBytes := w * h
    pal := pyToBytes(palette)
    if len(pal) != 256*3 {
        panic("palette must be 256*3 bytes")
    }
    dcs := pyToInt(delayCS)
    lp := pyToInt(loop)

    frs := pyIter(frames)
    out := []byte{}
    out = append(out, []byte("GIF89a")...)
    out = append(out, byte(w), byte(w>>8), byte(h), byte(h>>8))
    out = append(out, 0xF7, 0, 0)
    out = append(out, pal...)

    out = append(out, 0x21, 0xFF, 0x0B)
    out = append(out, []byte("NETSCAPE2.0")...)
    out = append(out, 0x03, 0x01, byte(lp), byte(lp>>8), 0x00)

    for _, frAny := range frs {
        fr := pyToBytes(frAny)
        if len(fr) != frameBytes {
            panic("frame size mismatch")
        }
        out = append(out, 0x21, 0xF9, 0x04, 0x00, byte(dcs), byte(dcs>>8), 0x00, 0x00)
        out = append(out, 0x2C, 0, 0, 0, 0, byte(w), byte(w>>8), byte(h), byte(h>>8), 0x00)
        out = append(out, 0x08)
        compressed := pyLzwEncode(fr, 8)
        pos := 0
        for pos < len(compressed) {
            ln := len(compressed) - pos
            if ln > 255 {
                ln = 255
            }
            out = append(out, byte(ln))
            out = append(out, compressed[pos:pos+ln]...)
            pos += ln
        }
        out = append(out, 0x00)
    }
    out = append(out, 0x3B)
    _ = os.WriteFile(pyToString(path), out, 0o644)
}

func next_state(grid any, w int, h int) any {
    var nxt any = []any{}
    _ = nxt
    __pytra_range_start_1 := pyToInt(0)
    __pytra_range_stop_2 := pyToInt(h)
    __pytra_range_step_3 := pyToInt(1)
    if __pytra_range_step_3 == 0 { panic("range() step must not be zero") }
    var y int = 0
    _ = y
    for __pytra_i_4 := __pytra_range_start_1; (__pytra_range_step_3 > 0 && __pytra_i_4 < __pytra_range_stop_2) || (__pytra_range_step_3 < 0 && __pytra_i_4 > __pytra_range_stop_2); __pytra_i_4 += __pytra_range_step_3 {
        y = __pytra_i_4
        var row any = []any{}
        _ = row
        __pytra_range_start_5 := pyToInt(0)
        __pytra_range_stop_6 := pyToInt(w)
        __pytra_range_step_7 := pyToInt(1)
        if __pytra_range_step_7 == 0 { panic("range() step must not be zero") }
        var x int = 0
        _ = x
        for __pytra_i_8 := __pytra_range_start_5; (__pytra_range_step_7 > 0 && __pytra_i_8 < __pytra_range_stop_6) || (__pytra_range_step_7 < 0 && __pytra_i_8 > __pytra_range_stop_6); __pytra_i_8 += __pytra_range_step_7 {
            x = __pytra_i_8
            var cnt int = 0
            _ = cnt
            __pytra_range_start_9 := pyToInt((-1))
            __pytra_range_stop_10 := pyToInt(2)
            __pytra_range_step_11 := pyToInt(1)
            if __pytra_range_step_11 == 0 { panic("range() step must not be zero") }
            var dy int = 0
            _ = dy
            for __pytra_i_12 := __pytra_range_start_9; (__pytra_range_step_11 > 0 && __pytra_i_12 < __pytra_range_stop_10) || (__pytra_range_step_11 < 0 && __pytra_i_12 > __pytra_range_stop_10); __pytra_i_12 += __pytra_range_step_11 {
                dy = __pytra_i_12
                __pytra_range_start_13 := pyToInt((-1))
                __pytra_range_stop_14 := pyToInt(2)
                __pytra_range_step_15 := pyToInt(1)
                if __pytra_range_step_15 == 0 { panic("range() step must not be zero") }
                var dx int = 0
                _ = dx
                for __pytra_i_16 := __pytra_range_start_13; (__pytra_range_step_15 > 0 && __pytra_i_16 < __pytra_range_stop_14) || (__pytra_range_step_15 < 0 && __pytra_i_16 > __pytra_range_stop_14); __pytra_i_16 += __pytra_range_step_15 {
                    dx = __pytra_i_16
                    if (pyBool((pyBool((dx != 0)) || pyBool((dy != 0))))) {
                        var nx int = (((x + dx) + w) % w)
                        _ = nx
                        var ny int = (((y + dy) + h) % h)
                        _ = ny
                        cnt = (cnt + pyToInt(pyGet(pyGet(grid, ny), nx)))
                    }
                }
            }
            var alive any = pyGet(pyGet(grid, y), x)
            _ = alive
            if (pyBool((pyBool(pyEq(alive, 1)) && pyBool((pyBool((cnt == 2)) || pyBool((cnt == 3))))))) {
                row = pyAppend(row, 1)
            } else {
                if (pyBool((pyBool(pyEq(alive, 0)) && pyBool((cnt == 3))))) {
                    row = pyAppend(row, 1)
                } else {
                    row = pyAppend(row, 0)
                }
            }
        }
        nxt = pyAppend(nxt, row)
    }
    return nxt
}

func render(grid any, w int, h int, cell int) any {
    var width int = (w * cell)
    _ = width
    var height int = (h * cell)
    _ = height
    var frame any = pyBytearray((width * height))
    _ = frame
    __pytra_range_start_17 := pyToInt(0)
    __pytra_range_stop_18 := pyToInt(h)
    __pytra_range_step_19 := pyToInt(1)
    if __pytra_range_step_19 == 0 { panic("range() step must not be zero") }
    var y int = 0
    _ = y
    for __pytra_i_20 := __pytra_range_start_17; (__pytra_range_step_19 > 0 && __pytra_i_20 < __pytra_range_stop_18) || (__pytra_range_step_19 < 0 && __pytra_i_20 > __pytra_range_stop_18); __pytra_i_20 += __pytra_range_step_19 {
        y = __pytra_i_20
        __pytra_range_start_21 := pyToInt(0)
        __pytra_range_stop_22 := pyToInt(w)
        __pytra_range_step_23 := pyToInt(1)
        if __pytra_range_step_23 == 0 { panic("range() step must not be zero") }
        var x int = 0
        _ = x
        for __pytra_i_24 := __pytra_range_start_21; (__pytra_range_step_23 > 0 && __pytra_i_24 < __pytra_range_stop_22) || (__pytra_range_step_23 < 0 && __pytra_i_24 > __pytra_range_stop_22); __pytra_i_24 += __pytra_range_step_23 {
            x = __pytra_i_24
            var v any = pyTernary(pyBool(pyGet(pyGet(grid, y), x)), 255, 0)
            _ = v
            __pytra_range_start_25 := pyToInt(0)
            __pytra_range_stop_26 := pyToInt(cell)
            __pytra_range_step_27 := pyToInt(1)
            if __pytra_range_step_27 == 0 { panic("range() step must not be zero") }
            var yy int = 0
            _ = yy
            for __pytra_i_28 := __pytra_range_start_25; (__pytra_range_step_27 > 0 && __pytra_i_28 < __pytra_range_stop_26) || (__pytra_range_step_27 < 0 && __pytra_i_28 > __pytra_range_stop_26); __pytra_i_28 += __pytra_range_step_27 {
                yy = __pytra_i_28
                var base int = ((((y * cell) + yy) * width) + (x * cell))
                _ = base
                __pytra_range_start_29 := pyToInt(0)
                __pytra_range_stop_30 := pyToInt(cell)
                __pytra_range_step_31 := pyToInt(1)
                if __pytra_range_step_31 == 0 { panic("range() step must not be zero") }
                var xx int = 0
                _ = xx
                for __pytra_i_32 := __pytra_range_start_29; (__pytra_range_step_31 > 0 && __pytra_i_32 < __pytra_range_stop_30) || (__pytra_range_step_31 < 0 && __pytra_i_32 > __pytra_range_stop_30); __pytra_i_32 += __pytra_range_step_31 {
                    xx = __pytra_i_32
                    pySet(frame, (base + xx), v)
                }
            }
        }
    }
    return pyBytes(frame)
}

func run_07_game_of_life_loop() any {
    var w int = 144
    _ = w
    var h int = 108
    _ = h
    var cell int = 4
    _ = cell
    var steps int = 210
    _ = steps
    var out_path string = "sample/out/07_game_of_life_loop.gif"
    _ = out_path
    var start any = pyPerfCounter()
    _ = start
    var grid any = []any{}
    _ = grid
    __pytra_range_start_33 := pyToInt(0)
    __pytra_range_stop_34 := pyToInt(h)
    __pytra_range_step_35 := pyToInt(1)
    if __pytra_range_step_35 == 0 { panic("range() step must not be zero") }
    var __pytra_discard int = 0
    _ = __pytra_discard
    for __pytra_i_36 := __pytra_range_start_33; (__pytra_range_step_35 > 0 && __pytra_i_36 < __pytra_range_stop_34) || (__pytra_range_step_35 < 0 && __pytra_i_36 > __pytra_range_stop_34); __pytra_i_36 += __pytra_range_step_35 {
        __pytra_discard = __pytra_i_36
        var row any = []any{}
        _ = row
        __pytra_range_start_37 := pyToInt(0)
        __pytra_range_stop_38 := pyToInt(w)
        __pytra_range_step_39 := pyToInt(1)
        if __pytra_range_step_39 == 0 { panic("range() step must not be zero") }
        for __pytra_i_40 := __pytra_range_start_37; (__pytra_range_step_39 > 0 && __pytra_i_40 < __pytra_range_stop_38) || (__pytra_range_step_39 < 0 && __pytra_i_40 > __pytra_range_stop_38); __pytra_i_40 += __pytra_range_step_39 {
            __pytra_discard = __pytra_i_40
            row = pyAppend(row, 0)
        }
        grid = pyAppend(grid, row)
    }
    __pytra_range_start_41 := pyToInt(0)
    __pytra_range_stop_42 := pyToInt(h)
    __pytra_range_step_43 := pyToInt(1)
    if __pytra_range_step_43 == 0 { panic("range() step must not be zero") }
    var y int = 0
    _ = y
    for __pytra_i_44 := __pytra_range_start_41; (__pytra_range_step_43 > 0 && __pytra_i_44 < __pytra_range_stop_42) || (__pytra_range_step_43 < 0 && __pytra_i_44 > __pytra_range_stop_42); __pytra_i_44 += __pytra_range_step_43 {
        y = __pytra_i_44
        __pytra_range_start_45 := pyToInt(0)
        __pytra_range_stop_46 := pyToInt(w)
        __pytra_range_step_47 := pyToInt(1)
        if __pytra_range_step_47 == 0 { panic("range() step must not be zero") }
        var x int = 0
        _ = x
        for __pytra_i_48 := __pytra_range_start_45; (__pytra_range_step_47 > 0 && __pytra_i_48 < __pytra_range_stop_46) || (__pytra_range_step_47 < 0 && __pytra_i_48 > __pytra_range_stop_46); __pytra_i_48 += __pytra_range_step_47 {
            x = __pytra_i_48
            var noise int = (((((x * 37) + (y * 73)) + ((x * y) % 19)) + ((x + y) % 11)) % 97)
            _ = noise
            if (pyBool((noise < 3))) {
                pySet(pyGet(grid, y), x, 1)
            }
        }
    }
    var glider any = []any{[]any{0, 1, 0}, []any{0, 0, 1}, []any{1, 1, 1}}
    _ = glider
    var r_pentomino any = []any{[]any{0, 1, 1}, []any{1, 1, 0}, []any{0, 1, 0}}
    _ = r_pentomino
    var lwss any = []any{[]any{0, 1, 1, 1, 1}, []any{1, 0, 0, 0, 1}, []any{0, 0, 0, 0, 1}, []any{1, 0, 0, 1, 0}}
    _ = lwss
    __pytra_range_start_49 := pyToInt(8)
    __pytra_range_stop_50 := pyToInt((h - 8))
    __pytra_range_step_51 := pyToInt(18)
    if __pytra_range_step_51 == 0 { panic("range() step must not be zero") }
    var gy int = 0
    _ = gy
    for __pytra_i_52 := __pytra_range_start_49; (__pytra_range_step_51 > 0 && __pytra_i_52 < __pytra_range_stop_50) || (__pytra_range_step_51 < 0 && __pytra_i_52 > __pytra_range_stop_50); __pytra_i_52 += __pytra_range_step_51 {
        gy = __pytra_i_52
        __pytra_range_start_53 := pyToInt(8)
        __pytra_range_stop_54 := pyToInt((w - 8))
        __pytra_range_step_55 := pyToInt(22)
        if __pytra_range_step_55 == 0 { panic("range() step must not be zero") }
        var gx int = 0
        _ = gx
        for __pytra_i_56 := __pytra_range_start_53; (__pytra_range_step_55 > 0 && __pytra_i_56 < __pytra_range_stop_54) || (__pytra_range_step_55 < 0 && __pytra_i_56 > __pytra_range_stop_54); __pytra_i_56 += __pytra_range_step_55 {
            gx = __pytra_i_56
            var kind int = (((gx * 7) + (gy * 11)) % 3)
            _ = kind
            if (pyBool((kind == 0))) {
                var ph any = pyLen(glider)
                _ = ph
                __pytra_range_start_57 := pyToInt(0)
                __pytra_range_stop_58 := pyToInt(ph)
                __pytra_range_step_59 := pyToInt(1)
                if __pytra_range_step_59 == 0 { panic("range() step must not be zero") }
                var py int = 0
                _ = py
                for __pytra_i_60 := __pytra_range_start_57; (__pytra_range_step_59 > 0 && __pytra_i_60 < __pytra_range_stop_58) || (__pytra_range_step_59 < 0 && __pytra_i_60 > __pytra_range_stop_58); __pytra_i_60 += __pytra_range_step_59 {
                    py = __pytra_i_60
                    var pw any = pyLen(pyGet(glider, py))
                    _ = pw
                    __pytra_range_start_61 := pyToInt(0)
                    __pytra_range_stop_62 := pyToInt(pw)
                    __pytra_range_step_63 := pyToInt(1)
                    if __pytra_range_step_63 == 0 { panic("range() step must not be zero") }
                    var px int = 0
                    _ = px
                    for __pytra_i_64 := __pytra_range_start_61; (__pytra_range_step_63 > 0 && __pytra_i_64 < __pytra_range_stop_62) || (__pytra_range_step_63 < 0 && __pytra_i_64 > __pytra_range_stop_62); __pytra_i_64 += __pytra_range_step_63 {
                        px = __pytra_i_64
                        if (pyBool(pyEq(pyGet(pyGet(glider, py), px), 1))) {
                            pySet(pyGet(grid, ((gy + py) % h)), ((gx + px) % w), 1)
                        }
                    }
                }
            } else {
                if (pyBool((kind == 1))) {
                    var ph any = pyLen(r_pentomino)
                    _ = ph
                    __pytra_range_start_65 := pyToInt(0)
                    __pytra_range_stop_66 := pyToInt(ph)
                    __pytra_range_step_67 := pyToInt(1)
                    if __pytra_range_step_67 == 0 { panic("range() step must not be zero") }
                    var py int = 0
                    _ = py
                    for __pytra_i_68 := __pytra_range_start_65; (__pytra_range_step_67 > 0 && __pytra_i_68 < __pytra_range_stop_66) || (__pytra_range_step_67 < 0 && __pytra_i_68 > __pytra_range_stop_66); __pytra_i_68 += __pytra_range_step_67 {
                        py = __pytra_i_68
                        var pw any = pyLen(pyGet(r_pentomino, py))
                        _ = pw
                        __pytra_range_start_69 := pyToInt(0)
                        __pytra_range_stop_70 := pyToInt(pw)
                        __pytra_range_step_71 := pyToInt(1)
                        if __pytra_range_step_71 == 0 { panic("range() step must not be zero") }
                        var px int = 0
                        _ = px
                        for __pytra_i_72 := __pytra_range_start_69; (__pytra_range_step_71 > 0 && __pytra_i_72 < __pytra_range_stop_70) || (__pytra_range_step_71 < 0 && __pytra_i_72 > __pytra_range_stop_70); __pytra_i_72 += __pytra_range_step_71 {
                            px = __pytra_i_72
                            if (pyBool(pyEq(pyGet(pyGet(r_pentomino, py), px), 1))) {
                                pySet(pyGet(grid, ((gy + py) % h)), ((gx + px) % w), 1)
                            }
                        }
                    }
                } else {
                    var ph any = pyLen(lwss)
                    _ = ph
                    __pytra_range_start_73 := pyToInt(0)
                    __pytra_range_stop_74 := pyToInt(ph)
                    __pytra_range_step_75 := pyToInt(1)
                    if __pytra_range_step_75 == 0 { panic("range() step must not be zero") }
                    var py int = 0
                    _ = py
                    for __pytra_i_76 := __pytra_range_start_73; (__pytra_range_step_75 > 0 && __pytra_i_76 < __pytra_range_stop_74) || (__pytra_range_step_75 < 0 && __pytra_i_76 > __pytra_range_stop_74); __pytra_i_76 += __pytra_range_step_75 {
                        py = __pytra_i_76
                        var pw any = pyLen(pyGet(lwss, py))
                        _ = pw
                        __pytra_range_start_77 := pyToInt(0)
                        __pytra_range_stop_78 := pyToInt(pw)
                        __pytra_range_step_79 := pyToInt(1)
                        if __pytra_range_step_79 == 0 { panic("range() step must not be zero") }
                        var px int = 0
                        _ = px
                        for __pytra_i_80 := __pytra_range_start_77; (__pytra_range_step_79 > 0 && __pytra_i_80 < __pytra_range_stop_78) || (__pytra_range_step_79 < 0 && __pytra_i_80 > __pytra_range_stop_78); __pytra_i_80 += __pytra_range_step_79 {
                            px = __pytra_i_80
                            if (pyBool(pyEq(pyGet(pyGet(lwss, py), px), 1))) {
                                pySet(pyGet(grid, ((gy + py) % h)), ((gx + px) % w), 1)
                            }
                        }
                    }
                }
            }
        }
    }
    var frames any = []any{}
    _ = frames
    __pytra_range_start_81 := pyToInt(0)
    __pytra_range_stop_82 := pyToInt(steps)
    __pytra_range_step_83 := pyToInt(1)
    if __pytra_range_step_83 == 0 { panic("range() step must not be zero") }
    for __pytra_i_84 := __pytra_range_start_81; (__pytra_range_step_83 > 0 && __pytra_i_84 < __pytra_range_stop_82) || (__pytra_range_step_83 < 0 && __pytra_i_84 > __pytra_range_stop_82); __pytra_i_84 += __pytra_range_step_83 {
        __pytra_discard = __pytra_i_84
        frames = pyAppend(frames, render(grid, w, h, cell))
        grid = next_state(grid, w, h)
    }
    pySaveGIF(out_path, (w * cell), (h * cell), frames, pyGrayscalePalette(), 4, 0)
    var elapsed any = pySub(pyPerfCounter(), start)
    _ = elapsed
    pyPrint("output:", out_path)
    pyPrint("frames:", steps)
    pyPrint("elapsed_sec:", elapsed)
    return nil
}

func main() {
    run_07_game_of_life_loop()
}
