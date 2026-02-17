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
    "path/filepath"
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

func py_main() any {
    pyPrint(pyLt(math.Abs(pyToFloat(math.Tan(pyToFloat(0.0)))), 1e-12))
    pyPrint(pyLt(math.Abs(pyToFloat(pySub(math.Log(pyToFloat(math.Exp(pyToFloat(1.0)))), 1.0))), 1e-12))
    pyPrint(pyToInt(math.Log10(pyToFloat(1000.0))))
    pyPrint(pyToInt(pyMul(math.Abs(pyToFloat((-3.5))), 10.0)))
    pyPrint(pyToInt(math.Ceil(pyToFloat(2.1))))
    pyPrint(pyToInt(math.Pow(pyToFloat(2.0), pyToFloat(5.0))))
    return nil
}

func main() {
    py_main()
}
