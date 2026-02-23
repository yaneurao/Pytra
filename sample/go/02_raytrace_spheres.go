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

func clamp01(v float64) any {
    if (pyBool((v < 0.0))) {
        return 0.0
    }
    if (pyBool((v > 1.0))) {
        return 1.0
    }
    return v
}

func hit_sphere(ox float64, oy float64, oz float64, dx float64, dy float64, dz float64, cx float64, cy float64, cz float64, r float64) any {
    var lx float64 = (ox - cx)
    _ = lx
    var ly float64 = (oy - cy)
    _ = ly
    var lz float64 = (oz - cz)
    _ = lz
    var a float64 = (((dx * dx) + (dy * dy)) + (dz * dz))
    _ = a
    var b float64 = (2.0 * (((lx * dx) + (ly * dy)) + (lz * dz)))
    _ = b
    var c float64 = ((((lx * lx) + (ly * ly)) + (lz * lz)) - (r * r))
    _ = c
    var d float64 = ((b * b) - ((4.0 * a) * c))
    _ = d
    if (pyBool((d < 0.0))) {
        return (-1.0)
    }
    var sd float64 = math.Sqrt(pyToFloat(d))
    _ = sd
    var t0 float64 = (((-b) - sd) / (2.0 * a))
    _ = t0
    var t1 float64 = (((-b) + sd) / (2.0 * a))
    _ = t1
    if (pyBool((t0 > 0.001))) {
        return t0
    }
    if (pyBool((t1 > 0.001))) {
        return t1
    }
    return (-1.0)
}

func render(width int, height int, aa int) any {
    var pixels any = pyBytearray(nil)
    _ = pixels
    var ox float64 = 0.0
    _ = ox
    var oy float64 = 0.0
    _ = oy
    var oz float64 = (-3.0)
    _ = oz
    var lx float64 = (-0.4)
    _ = lx
    var ly float64 = 0.8
    _ = ly
    var lz float64 = (-0.45)
    _ = lz
    __pytra_range_start_1 := pyToInt(0)
    __pytra_range_stop_2 := pyToInt(height)
    __pytra_range_step_3 := pyToInt(1)
    if __pytra_range_step_3 == 0 { panic("range() step must not be zero") }
    var y int = 0
    _ = y
    for __pytra_i_4 := __pytra_range_start_1; (__pytra_range_step_3 > 0 && __pytra_i_4 < __pytra_range_stop_2) || (__pytra_range_step_3 < 0 && __pytra_i_4 > __pytra_range_stop_2); __pytra_i_4 += __pytra_range_step_3 {
        y = __pytra_i_4
        __pytra_range_start_5 := pyToInt(0)
        __pytra_range_stop_6 := pyToInt(width)
        __pytra_range_step_7 := pyToInt(1)
        if __pytra_range_step_7 == 0 { panic("range() step must not be zero") }
        var x int = 0
        _ = x
        for __pytra_i_8 := __pytra_range_start_5; (__pytra_range_step_7 > 0 && __pytra_i_8 < __pytra_range_stop_6) || (__pytra_range_step_7 < 0 && __pytra_i_8 > __pytra_range_stop_6); __pytra_i_8 += __pytra_range_step_7 {
            x = __pytra_i_8
            var ar int = 0
            _ = ar
            var ag int = 0
            _ = ag
            var ab int = 0
            _ = ab
            __pytra_range_start_9 := pyToInt(0)
            __pytra_range_stop_10 := pyToInt(aa)
            __pytra_range_step_11 := pyToInt(1)
            if __pytra_range_step_11 == 0 { panic("range() step must not be zero") }
            var ay int = 0
            _ = ay
            for __pytra_i_12 := __pytra_range_start_9; (__pytra_range_step_11 > 0 && __pytra_i_12 < __pytra_range_stop_10) || (__pytra_range_step_11 < 0 && __pytra_i_12 > __pytra_range_stop_10); __pytra_i_12 += __pytra_range_step_11 {
                ay = __pytra_i_12
                __pytra_range_start_13 := pyToInt(0)
                __pytra_range_stop_14 := pyToInt(aa)
                __pytra_range_step_15 := pyToInt(1)
                if __pytra_range_step_15 == 0 { panic("range() step must not be zero") }
                var ax int = 0
                _ = ax
                for __pytra_i_16 := __pytra_range_start_13; (__pytra_range_step_15 > 0 && __pytra_i_16 < __pytra_range_stop_14) || (__pytra_range_step_15 < 0 && __pytra_i_16 > __pytra_range_stop_14); __pytra_i_16 += __pytra_range_step_15 {
                    ax = __pytra_i_16
                    var fy float64 = ((float64(y) + ((float64(ay) + 0.5) / float64(aa))) / float64((height - 1)))
                    _ = fy
                    var fx float64 = ((float64(x) + ((float64(ax) + 0.5) / float64(aa))) / float64((width - 1)))
                    _ = fx
                    var sy float64 = (1.0 - (2.0 * fy))
                    _ = sy
                    var sx float64 = (((2.0 * fx) - 1.0) * (float64(width) / float64(height)))
                    _ = sx
                    var dx float64 = sx
                    _ = dx
                    var dy float64 = sy
                    _ = dy
                    var dz float64 = 1.0
                    _ = dz
                    var inv_len float64 = (1.0 / math.Sqrt(pyToFloat((((dx * dx) + (dy * dy)) + (dz * dz)))))
                    _ = inv_len
                    dx = (dx * inv_len)
                    dy = (dy * inv_len)
                    dz = (dz * inv_len)
                    var t_min float64 = 1e+30
                    _ = t_min
                    var hit_id int = (-1)
                    _ = hit_id
                    var t float64 = pyToFloat(hit_sphere(ox, oy, oz, dx, dy, dz, (-0.8), (-0.2), 2.2, 0.8))
                    _ = t
                    if (pyBool((pyBool((t > 0.0)) && pyBool((t < t_min))))) {
                        t_min = t
                        hit_id = 0
                    }
                    t = pyToFloat(hit_sphere(ox, oy, oz, dx, dy, dz, 0.9, 0.1, 2.9, 0.95))
                    if (pyBool((pyBool((t > 0.0)) && pyBool((t < t_min))))) {
                        t_min = t
                        hit_id = 1
                    }
                    t = pyToFloat(hit_sphere(ox, oy, oz, dx, dy, dz, 0.0, (-1001.0), 3.0, 1000.0))
                    if (pyBool((pyBool((t > 0.0)) && pyBool((t < t_min))))) {
                        t_min = t
                        hit_id = 2
                    }
                    var r int = 0
                    _ = r
                    var g int = 0
                    _ = g
                    var b int = 0
                    _ = b
                    if (pyBool((hit_id >= 0))) {
                        var px float64 = (ox + (dx * t_min))
                        _ = px
                        var py float64 = (oy + (dy * t_min))
                        _ = py
                        var pz float64 = (oz + (dz * t_min))
                        _ = pz
                        var nx float64 = 0.0
                        _ = nx
                        var ny float64 = 0.0
                        _ = ny
                        var nz float64 = 0.0
                        _ = nz
                        if (pyBool((hit_id == 0))) {
                            nx = ((px + 0.8) / 0.8)
                            ny = ((py + 0.2) / 0.8)
                            nz = ((pz - 2.2) / 0.8)
                        } else {
                            if (pyBool((hit_id == 1))) {
                                nx = ((px - 0.9) / 0.95)
                                ny = ((py - 0.1) / 0.95)
                                nz = ((pz - 2.9) / 0.95)
                            } else {
                                nx = 0.0
                                ny = 1.0
                                nz = 0.0
                            }
                        }
                        var diff float64 = (((nx * (-lx)) + (ny * (-ly))) + (nz * (-lz)))
                        _ = diff
                        diff = pyToFloat(clamp01(diff))
                        var base_r float64 = 0.0
                        _ = base_r
                        var base_g float64 = 0.0
                        _ = base_g
                        var base_b float64 = 0.0
                        _ = base_b
                        if (pyBool((hit_id == 0))) {
                            base_r = 0.95
                            base_g = 0.35
                            base_b = 0.25
                        } else {
                            if (pyBool((hit_id == 1))) {
                                base_r = 0.25
                                base_g = 0.55
                                base_b = 0.95
                            } else {
                                var checker int = (pyToInt(((px + 50.0) * 0.8)) + pyToInt(((pz + 50.0) * 0.8)))
                                _ = checker
                                if (pyBool(((checker % 2) == 0))) {
                                    base_r = 0.85
                                    base_g = 0.85
                                    base_b = 0.85
                                } else {
                                    base_r = 0.2
                                    base_g = 0.2
                                    base_b = 0.2
                                }
                            }
                        }
                        var shade float64 = (0.12 + (0.88 * diff))
                        _ = shade
                        r = pyToInt(pyMul(255.0, clamp01((base_r * shade))))
                        g = pyToInt(pyMul(255.0, clamp01((base_g * shade))))
                        b = pyToInt(pyMul(255.0, clamp01((base_b * shade))))
                    } else {
                        var tsky float64 = (0.5 * (dy + 1.0))
                        _ = tsky
                        r = pyToInt((255.0 * (0.65 + (0.2 * tsky))))
                        g = pyToInt((255.0 * (0.75 + (0.18 * tsky))))
                        b = pyToInt((255.0 * (0.9 + (0.08 * tsky))))
                    }
                    ar = (ar + r)
                    ag = (ag + g)
                    ab = (ab + b)
                }
            }
            var samples int = (aa * aa)
            _ = samples
            pixels = pyAppend(pixels, (ar / samples))
            pixels = pyAppend(pixels, (ag / samples))
            pixels = pyAppend(pixels, (ab / samples))
        }
    }
    return pixels
}

func run_raytrace() any {
    var width int = 1600
    _ = width
    var height int = 900
    _ = height
    var aa int = 2
    _ = aa
    var out_path string = "sample/out/02_raytrace_spheres.png"
    _ = out_path
    var start float64 = pyToFloat(pyPerfCounter())
    _ = start
    var pixels any = render(width, height, aa)
    _ = pixels
    pyWriteRGBPNG(out_path, width, height, pixels)
    var elapsed float64 = pyToFloat(pySub(pyPerfCounter(), start))
    _ = elapsed
    pyPrint("output:", out_path)
    pyPrint("size:", width, "x", height)
    pyPrint("elapsed_sec:", elapsed)
    return nil
}

func main() {
    run_raytrace()
}
