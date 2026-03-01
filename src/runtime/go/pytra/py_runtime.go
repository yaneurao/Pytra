// Go ネイティブ変換向け Python 互換ランタイム補助。

package main

import (
    "bytes"
    "compress/zlib"
    "fmt"
    "hash/crc32"
    "math"
    "os"
    "path/filepath"
    "strconv"
    "strings"
    "time"
    "unicode"
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
    case pyPath:
        return x.value
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
func pyMathTan(v any) any  { return math.Tan(pyToFloat(v)) }
func pyMathExp(v any) any  { return math.Exp(pyToFloat(v)) }
func pyMathLog(v any) any  { return math.Log(pyToFloat(v)) }
func pyMathLog10(v any) any { return math.Log10(pyToFloat(v)) }
func pyMathFabs(v any) any { return math.Abs(pyToFloat(v)) }
func pyMathFloor(v any) any { return float64(math.Floor(pyToFloat(v))) }
func pyMathCeil(v any) any { return float64(math.Ceil(pyToFloat(v))) }
func pyMathPow(a any, b any) any { return math.Pow(pyToFloat(a), pyToFloat(b)) }
func pyMathPi() any         { return math.Pi }

// -------- pathlib helper --------

type pyPath struct {
    value string
}

func pyPathString(v any) string {
    if p, ok := v.(pyPath); ok {
        return p.value
    }
    return pyToString(v)
}

func pyPathNew(v any) any {
    return pyPath{value: pyPathString(v)}
}

func pyPathJoin(base any, child any) any {
    return pyPath{value: filepath.Join(pyPathString(base), pyPathString(child))}
}

func pyPathResolve(v any) any {
    p, err := filepath.Abs(pyPathString(v))
    if err != nil {
        panic(err)
    }
    return pyPath{value: p}
}

func pyPathParent(v any) any {
    return pyPath{value: filepath.Dir(pyPathString(v))}
}

func pyPathName(v any) any {
    return filepath.Base(pyPathString(v))
}

func pyPathStem(v any) any {
    base := filepath.Base(pyPathString(v))
    ext := filepath.Ext(base)
    return strings.TrimSuffix(base, ext)
}

func pyPathExists(v any) any {
    _, err := os.Stat(pyPathString(v))
    return err == nil
}

func pyPathReadText(v any) any {
    b, err := os.ReadFile(pyPathString(v))
    if err != nil {
        panic(err)
    }
    return string(b)
}

func pyPathWriteText(v any, content any) any {
    if err := os.WriteFile(pyPathString(v), []byte(pyToString(content)), 0o644); err != nil {
        panic(err)
    }
    return nil
}

func pyPathMkdir(v any, parents any, existOK any) any {
    p := pyPathString(v)
    if pyBool(parents) {
        if err := os.MkdirAll(p, 0o755); err != nil {
            panic(err)
        }
        return nil
    }
    err := os.Mkdir(p, 0o755)
    if err != nil {
        if pyBool(existOK) && os.IsExist(err) {
            return nil
        }
        panic(err)
    }
    return nil
}

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
    zw, _ := zlib.NewWriterLevel(&zbuf, zlib.NoCompression)
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

// ---- legacy go emitter helper compatibility ----
func __pytra_noop(args ...any) {}

func __pytra_assert(args ...any) string {
    _ = args
    return "True"
}

func __pytra_perf_counter() float64 {
    return float64(time.Now().UnixNano()) / 1_000_000_000.0
}

func __pytra_truthy(v any) bool {
    switch t := v.(type) {
    case nil:
        return false
    case bool:
        return t
    case int:
        return t != 0
    case int64:
        return t != 0
    case float64:
        return t != 0.0
    case string:
        return t != ""
    case []any:
        return len(t) != 0
    case map[any]any:
        return len(t) != 0
    default:
        return true
    }
}

func __pytra_int(v any) int64 {
    switch t := v.(type) {
    case nil:
        return 0
    case int:
        return int64(t)
    case int64:
        return t
    case float64:
        return int64(t)
    case bool:
        if t {
            return 1
        }
        return 0
    case string:
        if t == "" {
            return 0
        }
        n, err := strconv.ParseInt(t, 10, 64)
        if err != nil {
            return 0
        }
        return n
    default:
        return 0
    }
}

func __pytra_float(v any) float64 {
    switch t := v.(type) {
    case nil:
        return 0.0
    case int:
        return float64(t)
    case int64:
        return float64(t)
    case float64:
        return t
    case bool:
        if t {
            return 1.0
        }
        return 0.0
    case string:
        if t == "" {
            return 0.0
        }
        n, err := strconv.ParseFloat(t, 64)
        if err != nil {
            return 0.0
        }
        return n
    default:
        return 0.0
    }
}

func __pytra_str(v any) string {
    if v == nil {
        return ""
    }
    switch t := v.(type) {
    case string:
        return t
    default:
        return fmt.Sprint(v)
    }
}

func __pytra_len(v any) int64 {
    switch t := v.(type) {
    case nil:
        return 0
    case string:
        return int64(len([]rune(t)))
    case []any:
        return int64(len(t))
    case map[any]any:
        return int64(len(t))
    default:
        return 0
    }
}

func __pytra_index(i int64, n int64) int64 {
    if i < 0 {
        i += n
    }
    return i
}

func __pytra_get_index(container any, index any) any {
    switch t := container.(type) {
    case []any:
        if len(t) == 0 {
            return nil
        }
        i := __pytra_index(__pytra_int(index), int64(len(t)))
        if i < 0 || i >= int64(len(t)) {
            return nil
        }
        return t[i]
    case map[any]any:
        return t[index]
    case string:
        runes := []rune(t)
        if len(runes) == 0 {
            return ""
        }
        i := __pytra_index(__pytra_int(index), int64(len(runes)))
        if i < 0 || i >= int64(len(runes)) {
            return ""
        }
        return string(runes[i])
    default:
        return nil
    }
}

func __pytra_set_index(container any, index any, value any) {
    switch t := container.(type) {
    case []any:
        if len(t) == 0 {
            return
        }
        i := __pytra_index(__pytra_int(index), int64(len(t)))
        if i < 0 || i >= int64(len(t)) {
            return
        }
        t[i] = value
    case map[any]any:
        t[index] = value
    }
}

func __pytra_slice(container any, lower any, upper any) any {
    switch t := container.(type) {
    case string:
        runes := []rune(t)
        n := int64(len(runes))
        lo := __pytra_index(__pytra_int(lower), n)
        hi := __pytra_index(__pytra_int(upper), n)
        if lo < 0 {
            lo = 0
        }
        if hi < 0 {
            hi = 0
        }
        if lo > n {
            lo = n
        }
        if hi > n {
            hi = n
        }
        if hi < lo {
            hi = lo
        }
        return string(runes[lo:hi])
    case []any:
        n := int64(len(t))
        lo := __pytra_index(__pytra_int(lower), n)
        hi := __pytra_index(__pytra_int(upper), n)
        if lo < 0 {
            lo = 0
        }
        if hi < 0 {
            hi = 0
        }
        if lo > n {
            lo = n
        }
        if hi > n {
            hi = n
        }
        if hi < lo {
            hi = lo
        }
        out := []any{}
        i := lo
        for i < hi {
            out = append(out, t[i])
            i += 1
        }
        return out
    default:
        return nil
    }
}

func __pytra_isdigit(v any) bool {
    s := __pytra_str(v)
    if s == "" {
        return false
    }
    for _, ch := range s {
        if !unicode.IsDigit(ch) {
            return false
        }
    }
    return true
}

func __pytra_isalpha(v any) bool {
    s := __pytra_str(v)
    if s == "" {
        return false
    }
    for _, ch := range s {
        if !unicode.IsLetter(ch) {
            return false
        }
    }
    return true
}

func __pytra_contains(container any, value any) bool {
    switch t := container.(type) {
    case []any:
        i := 0
        for i < len(t) {
            if t[i] == value {
                return true
            }
            i += 1
        }
        return false
    case map[any]any:
        _, ok := t[value]
        return ok
    case string:
        needle := __pytra_str(value)
        return needle != "" && len(needle) <= len(t) && __pytra_str_contains(t, needle)
    default:
        return false
    }
}

func __pytra_str_contains(haystack string, needle string) bool {
    if needle == "" {
        return true
    }
    i := 0
    limit := len(haystack) - len(needle)
    for i <= limit {
        if haystack[i:i+len(needle)] == needle {
            return true
        }
        i += 1
    }
    return false
}

func __pytra_ifexp(cond bool, a any, b any) any {
    if cond {
        return a
    }
    return b
}

func __pytra_bytearray(init any) []any {
    out := []any{}
    switch t := init.(type) {
    case int:
        i := 0
        for i < t {
            out = append(out, int64(0))
            i += 1
        }
    case int64:
        i := int64(0)
        for i < t {
            out = append(out, int64(0))
            i += 1
        }
    case []any:
        i := 0
        for i < len(t) {
            out = append(out, t[i])
            i += 1
        }
    }
    return out
}

func __pytra_bytes(v any) []any {
    switch t := v.(type) {
    case []any:
        out := []any{}
        i := 0
        for i < len(t) {
            out = append(out, t[i])
            i += 1
        }
        return out
    default:
        return []any{}
    }
}

func __pytra_list_repeat(value any, count any) []any {
    out := []any{}
    n := __pytra_int(count)
    i := int64(0)
    for i < n {
        out = append(out, value)
        i += 1
    }
    return out
}

func __pytra_enumerate(v any) []any {
    items := __pytra_as_list(v)
    out := []any{}
    i := int64(0)
    for i < int64(len(items)) {
        out = append(out, []any{i, items[i]})
        i += 1
    }
    return out
}

func __pytra_as_list(v any) []any {
    if t, ok := v.([]any); ok {
        return t
    }
    return []any{}
}

func __pytra_as_dict(v any) map[any]any {
    if t, ok := v.(map[any]any); ok {
        return t
    }
    return map[any]any{}
}

func __pytra_grayscale_palette() []any {
    raw := pyGrayscalePalette()
    return __pytra_bytes(raw)
}

func __pytra_write_rgb_png(path any, width any, height any, pixels any) {
    pyWriteRGBPNG(path, width, height, pixels)
}

func __pytra_save_gif(path any, width any, height any, frames any, palette any, delayCS any, loop any) {
    pySaveGIF(path, width, height, frames, palette, delayCS, loop)
}

func __pytra_pop_last(v []any) []any {
    if len(v) == 0 {
        return v
    }
    return v[:len(v)-1]
}

func __pytra_print(args ...any) {
    if len(args) == 0 {
        fmt.Println()
        return
    }
    fmt.Println(args...)
}

func __pytra_min(a any, b any) any {
    af := __pytra_float(a)
    bf := __pytra_float(b)
    if af < bf {
        if __pytra_is_float(a) || __pytra_is_float(b) {
            return af
        }
        return __pytra_int(a)
    }
    if __pytra_is_float(a) || __pytra_is_float(b) {
        return bf
    }
    return __pytra_int(b)
}

func __pytra_max(a any, b any) any {
    af := __pytra_float(a)
    bf := __pytra_float(b)
    if af > bf {
        if __pytra_is_float(a) || __pytra_is_float(b) {
            return af
        }
        return __pytra_int(a)
    }
    if __pytra_is_float(a) || __pytra_is_float(b) {
        return bf
    }
    return __pytra_int(b)
}

func __pytra_is_int(v any) bool {
    switch v.(type) {
    case int, int64:
        return true
    default:
        return false
    }
}

func __pytra_is_float(v any) bool {
    _, ok := v.(float64)
    return ok
}

func __pytra_is_bool(v any) bool {
    _, ok := v.(bool)
    return ok
}

func __pytra_is_str(v any) bool {
    _, ok := v.(string)
    return ok
}

func __pytra_is_list(v any) bool {
    _, ok := v.([]any)
    return ok
}
