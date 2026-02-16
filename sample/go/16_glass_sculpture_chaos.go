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

func dot(ax float64, ay float64, az float64, bx float64, by float64, bz float64) any {
    return (((ax * bx) + (ay * by)) + (az * bz))
}

func length(x float64, y float64, z float64) any {
    return math.Sqrt(pyToFloat((((x * x) + (y * y)) + (z * z))))
}

func normalize(x float64, y float64, z float64) any {
    var l any = length(x, y, z)
    _ = l
    if (pyBool(pyLt(l, 1e-09))) {
        return []any{0.0, 0.0, 0.0}
    }
    return []any{pyDiv(x, l), pyDiv(y, l), pyDiv(z, l)}
}

func reflect(ix float64, iy float64, iz float64, nx float64, ny float64, nz float64) any {
    var d any = pyMul(dot(ix, iy, iz, nx, ny, nz), 2.0)
    _ = d
    return []any{pySub(ix, pyMul(d, nx)), pySub(iy, pyMul(d, ny)), pySub(iz, pyMul(d, nz))}
}

func refract(ix float64, iy float64, iz float64, nx float64, ny float64, nz float64, eta float64) any {
    var cosi any = pyNeg(dot(ix, iy, iz, nx, ny, nz))
    _ = cosi
    var sint2 any = pyMul((eta * eta), pySub(1.0, pyMul(cosi, cosi)))
    _ = sint2
    if (pyBool(pyGt(sint2, 1.0))) {
        return reflect(ix, iy, iz, nx, ny, nz)
    }
    var cost float64 = math.Sqrt(pyToFloat(pySub(1.0, sint2)))
    _ = cost
    var k any = pySub(pyMul(eta, cosi), cost)
    _ = k
    return []any{pyAdd((eta * ix), pyMul(k, nx)), pyAdd((eta * iy), pyMul(k, ny)), pyAdd((eta * iz), pyMul(k, nz))}
}

func schlick(cos_theta float64, f0 float64) any {
    var m float64 = (1.0 - cos_theta)
    _ = m
    return (f0 + ((1.0 - f0) * ((((m * m) * m) * m) * m)))
}

func sky_color(dx float64, dy float64, dz float64, tphase float64) any {
    var t float64 = (0.5 * (dy + 1.0))
    _ = t
    var r float64 = (0.06 + (0.2 * t))
    _ = r
    var g float64 = (0.1 + (0.25 * t))
    _ = g
    var b float64 = (0.16 + (0.45 * t))
    _ = b
    var band float64 = (0.5 + (0.5 * math.Sin(pyToFloat((((8.0 * dx) + (6.0 * dz)) + tphase)))))
    _ = band
    r = (r + (0.08 * band))
    g = (g + (0.05 * band))
    b = (b + (0.12 * band))
    return []any{clamp01(r), clamp01(g), clamp01(b)}
}

func sphere_intersect(ox float64, oy float64, oz float64, dx float64, dy float64, dz float64, cx float64, cy float64, cz float64, radius float64) any {
    var lx float64 = (ox - cx)
    _ = lx
    var ly float64 = (oy - cy)
    _ = ly
    var lz float64 = (oz - cz)
    _ = lz
    var b float64 = (((lx * dx) + (ly * dy)) + (lz * dz))
    _ = b
    var c float64 = ((((lx * lx) + (ly * ly)) + (lz * lz)) - (radius * radius))
    _ = c
    var h float64 = ((b * b) - c)
    _ = h
    if (pyBool((h < 0.0))) {
        return (-1.0)
    }
    var s float64 = math.Sqrt(pyToFloat(h))
    _ = s
    var t0 float64 = ((-b) - s)
    _ = t0
    if (pyBool((t0 > 0.0001))) {
        return t0
    }
    var t1 float64 = ((-b) + s)
    _ = t1
    if (pyBool((t1 > 0.0001))) {
        return t1
    }
    return (-1.0)
}

func palette_332() any {
    var p any = pyBytearray((256 * 3))
    _ = p
    __pytra_range_start_1 := pyToInt(0)
    __pytra_range_stop_2 := pyToInt(256)
    __pytra_range_step_3 := pyToInt(1)
    if __pytra_range_step_3 == 0 { panic("range() step must not be zero") }
    var i int = 0
    _ = i
    for __pytra_i_4 := __pytra_range_start_1; (__pytra_range_step_3 > 0 && __pytra_i_4 < __pytra_range_stop_2) || (__pytra_range_step_3 < 0 && __pytra_i_4 > __pytra_range_stop_2); __pytra_i_4 += __pytra_range_step_3 {
        i = __pytra_i_4
        var r int = ((i >> uint(5)) & 7)
        _ = r
        var g int = ((i >> uint(2)) & 7)
        _ = g
        var b int = (i & 3)
        _ = b
        pySet(p, ((i * 3) + 0), pyToInt((float64((255 * r)) / float64(7))))
        pySet(p, ((i * 3) + 1), pyToInt((float64((255 * g)) / float64(7))))
        pySet(p, ((i * 3) + 2), pyToInt((float64((255 * b)) / float64(3))))
    }
    return pyBytes(p)
}

func quantize_332(r float64, g float64, b float64) any {
    var rr int = pyToInt(pyMul(clamp01(r), 255.0))
    _ = rr
    var gg int = pyToInt(pyMul(clamp01(g), 255.0))
    _ = gg
    var bb int = pyToInt(pyMul(clamp01(b), 255.0))
    _ = bb
    return ((((rr >> uint(5)) << uint(5)) + ((gg >> uint(5)) << uint(2))) + (bb >> uint(6)))
}

func render_frame(width int, height int, frame_id int, frames_n int) any {
    var t float64 = (float64(frame_id) / float64(frames_n))
    _ = t
    var tphase any = pyMul(pyMul(2.0, pyMathPi()), t)
    _ = tphase
    var cam_r float64 = 3.0
    _ = cam_r
    var cam_x float64 = (cam_r * math.Cos(pyToFloat(pyMul(tphase, 0.9))))
    _ = cam_x
    var cam_y float64 = (1.1 + (0.25 * math.Sin(pyToFloat(pyMul(tphase, 0.6)))))
    _ = cam_y
    var cam_z float64 = (cam_r * math.Sin(pyToFloat(pyMul(tphase, 0.9))))
    _ = cam_z
    var look_x float64 = 0.0
    _ = look_x
    var look_y float64 = 0.35
    _ = look_y
    var look_z float64 = 0.0
    _ = look_z
    var __pytra_tuple_5 any = normalize((look_x - cam_x), (look_y - cam_y), (look_z - cam_z))
    _ = __pytra_tuple_5
    var fwd_x any = pyGet(__pytra_tuple_5, 0)
    _ = fwd_x
    var fwd_y any = pyGet(__pytra_tuple_5, 1)
    _ = fwd_y
    var fwd_z any = pyGet(__pytra_tuple_5, 2)
    _ = fwd_z
    var __pytra_tuple_6 any = normalize(pyToFloat(fwd_z), 0.0, pyToFloat(pyNeg(fwd_x)))
    _ = __pytra_tuple_6
    var right_x any = pyGet(__pytra_tuple_6, 0)
    _ = right_x
    var right_y any = pyGet(__pytra_tuple_6, 1)
    _ = right_y
    var right_z any = pyGet(__pytra_tuple_6, 2)
    _ = right_z
    var __pytra_tuple_7 any = normalize(pyToFloat(pySub(pyMul(right_y, fwd_z), pyMul(right_z, fwd_y))), pyToFloat(pySub(pyMul(right_z, fwd_x), pyMul(right_x, fwd_z))), pyToFloat(pySub(pyMul(right_x, fwd_y), pyMul(right_y, fwd_x))))
    _ = __pytra_tuple_7
    var up_x any = pyGet(__pytra_tuple_7, 0)
    _ = up_x
    var up_y any = pyGet(__pytra_tuple_7, 1)
    _ = up_y
    var up_z any = pyGet(__pytra_tuple_7, 2)
    _ = up_z
    var s0x float64 = (0.9 * math.Cos(pyToFloat(pyMul(1.3, tphase))))
    _ = s0x
    var s0y float64 = (0.15 + (0.35 * math.Sin(pyToFloat(pyMul(1.7, tphase)))))
    _ = s0y
    var s0z float64 = (0.9 * math.Sin(pyToFloat(pyMul(1.3, tphase))))
    _ = s0z
    var s1x float64 = (1.2 * math.Cos(pyToFloat(pyAdd(pyMul(1.3, tphase), 2.094))))
    _ = s1x
    var s1y float64 = (0.1 + (0.4 * math.Sin(pyToFloat(pyAdd(pyMul(1.1, tphase), 0.8)))))
    _ = s1y
    var s1z float64 = (1.2 * math.Sin(pyToFloat(pyAdd(pyMul(1.3, tphase), 2.094))))
    _ = s1z
    var s2x float64 = (1.0 * math.Cos(pyToFloat(pyAdd(pyMul(1.3, tphase), 4.188))))
    _ = s2x
    var s2y float64 = (0.2 + (0.3 * math.Sin(pyToFloat(pyAdd(pyMul(1.5, tphase), 1.9)))))
    _ = s2y
    var s2z float64 = (1.0 * math.Sin(pyToFloat(pyAdd(pyMul(1.3, tphase), 4.188))))
    _ = s2z
    var lr float64 = 0.35
    _ = lr
    var lx float64 = (2.4 * math.Cos(pyToFloat(pyMul(tphase, 1.8))))
    _ = lx
    var ly float64 = (1.8 + (0.8 * math.Sin(pyToFloat(pyMul(tphase, 1.2)))))
    _ = ly
    var lz float64 = (2.4 * math.Sin(pyToFloat(pyMul(tphase, 1.8))))
    _ = lz
    var frame any = pyBytearray((width * height))
    _ = frame
    var aspect float64 = (float64(width) / float64(height))
    _ = aspect
    var fov float64 = 1.25
    _ = fov
    var i int = 0
    _ = i
    __pytra_range_start_8 := pyToInt(0)
    __pytra_range_stop_9 := pyToInt(height)
    __pytra_range_step_10 := pyToInt(1)
    if __pytra_range_step_10 == 0 { panic("range() step must not be zero") }
    var py int = 0
    _ = py
    for __pytra_i_11 := __pytra_range_start_8; (__pytra_range_step_10 > 0 && __pytra_i_11 < __pytra_range_stop_9) || (__pytra_range_step_10 < 0 && __pytra_i_11 > __pytra_range_stop_9); __pytra_i_11 += __pytra_range_step_10 {
        py = __pytra_i_11
        var sy float64 = (1.0 - ((2.0 * (float64(py) + 0.5)) / float64(height)))
        _ = sy
        __pytra_range_start_12 := pyToInt(0)
        __pytra_range_stop_13 := pyToInt(width)
        __pytra_range_step_14 := pyToInt(1)
        if __pytra_range_step_14 == 0 { panic("range() step must not be zero") }
        var px int = 0
        _ = px
        for __pytra_i_15 := __pytra_range_start_12; (__pytra_range_step_14 > 0 && __pytra_i_15 < __pytra_range_stop_13) || (__pytra_range_step_14 < 0 && __pytra_i_15 > __pytra_range_stop_13); __pytra_i_15 += __pytra_range_step_14 {
            px = __pytra_i_15
            var sx float64 = ((((2.0 * (float64(px) + 0.5)) / float64(width)) - 1.0) * aspect)
            _ = sx
            var rx any = pyAdd(fwd_x, pyMul(fov, pyAdd(pyMul(sx, right_x), pyMul(sy, up_x))))
            _ = rx
            var ry any = pyAdd(fwd_y, pyMul(fov, pyAdd(pyMul(sx, right_y), pyMul(sy, up_y))))
            _ = ry
            var rz any = pyAdd(fwd_z, pyMul(fov, pyAdd(pyMul(sx, right_z), pyMul(sy, up_z))))
            _ = rz
            var __pytra_tuple_16 any = normalize(pyToFloat(rx), pyToFloat(ry), pyToFloat(rz))
            _ = __pytra_tuple_16
            var dx any = pyGet(__pytra_tuple_16, 0)
            _ = dx
            var dy any = pyGet(__pytra_tuple_16, 1)
            _ = dy
            var dz any = pyGet(__pytra_tuple_16, 2)
            _ = dz
            var best_t float64 = 1000000000.0
            _ = best_t
            var hit_kind int = 0
            _ = hit_kind
            var r float64 = 0.0
            _ = r
            var g float64 = 0.0
            _ = g
            var b float64 = 0.0
            _ = b
            if (pyBool(pyLt(dy, (-1e-06)))) {
                var tf any = pyDiv(((-1.2) - cam_y), dy)
                _ = tf
                if (pyBool((pyBool(pyGt(tf, 0.0001)) && pyBool(pyLt(tf, best_t))))) {
                    best_t = pyToFloat(tf)
                    hit_kind = 1
                }
            }
            var t0 any = sphere_intersect(cam_x, cam_y, cam_z, pyToFloat(dx), pyToFloat(dy), pyToFloat(dz), s0x, s0y, s0z, 0.65)
            _ = t0
            if (pyBool((pyBool(pyGt(t0, 0.0)) && pyBool(pyLt(t0, best_t))))) {
                best_t = pyToFloat(t0)
                hit_kind = 2
            }
            var t1 any = sphere_intersect(cam_x, cam_y, cam_z, pyToFloat(dx), pyToFloat(dy), pyToFloat(dz), s1x, s1y, s1z, 0.72)
            _ = t1
            if (pyBool((pyBool(pyGt(t1, 0.0)) && pyBool(pyLt(t1, best_t))))) {
                best_t = pyToFloat(t1)
                hit_kind = 3
            }
            var t2 any = sphere_intersect(cam_x, cam_y, cam_z, pyToFloat(dx), pyToFloat(dy), pyToFloat(dz), s2x, s2y, s2z, 0.58)
            _ = t2
            if (pyBool((pyBool(pyGt(t2, 0.0)) && pyBool(pyLt(t2, best_t))))) {
                best_t = pyToFloat(t2)
                hit_kind = 4
            }
            if (pyBool((hit_kind == 0))) {
                var __pytra_tuple_17 any = sky_color(pyToFloat(dx), pyToFloat(dy), pyToFloat(dz), pyToFloat(tphase))
                _ = __pytra_tuple_17
                r = pyToFloat(pyGet(__pytra_tuple_17, 0))
                g = pyToFloat(pyGet(__pytra_tuple_17, 1))
                b = pyToFloat(pyGet(__pytra_tuple_17, 2))
            } else {
                if (pyBool((hit_kind == 1))) {
                    var hx any = pyAdd(cam_x, pyMul(best_t, dx))
                    _ = hx
                    var hz any = pyAdd(cam_z, pyMul(best_t, dz))
                    _ = hz
                    var cx int = pyToInt(math.Floor(pyToFloat(pyMul(hx, 2.0))))
                    _ = cx
                    var cz int = pyToInt(math.Floor(pyToFloat(pyMul(hz, 2.0))))
                    _ = cz
                    var checker any = pyTernary(pyBool((((cx + cz) % 2) == 0)), 0, 1)
                    _ = checker
                    var base_r any = pyTernary(pyBool(pyEq(checker, 0)), 0.1, 0.04)
                    _ = base_r
                    var base_g any = pyTernary(pyBool(pyEq(checker, 0)), 0.11, 0.05)
                    _ = base_g
                    var base_b any = pyTernary(pyBool(pyEq(checker, 0)), 0.13, 0.08)
                    _ = base_b
                    var lxv any = pySub(lx, hx)
                    _ = lxv
                    var lyv float64 = (ly - (-1.2))
                    _ = lyv
                    var lzv any = pySub(lz, hz)
                    _ = lzv
                    var __pytra_tuple_18 any = normalize(pyToFloat(lxv), lyv, pyToFloat(lzv))
                    _ = __pytra_tuple_18
                    var ldx any = pyGet(__pytra_tuple_18, 0)
                    _ = ldx
                    var ldy any = pyGet(__pytra_tuple_18, 1)
                    _ = ldy
                    var ldz any = pyGet(__pytra_tuple_18, 2)
                    _ = ldz
                    var ndotl any = pyMax(ldy, 0.0)
                    _ = ndotl
                    var ldist2 any = pyAdd(pyAdd(pyMul(lxv, lxv), (lyv * lyv)), pyMul(lzv, lzv))
                    _ = ldist2
                    var glow any = pyDiv(8.0, pyAdd(1.0, ldist2))
                    _ = glow
                    r = pyToFloat(pyAdd(pyAdd(base_r, pyMul(0.8, glow)), pyMul(0.2, ndotl)))
                    g = pyToFloat(pyAdd(pyAdd(base_g, pyMul(0.5, glow)), pyMul(0.18, ndotl)))
                    b = pyToFloat(pyAdd(pyAdd(base_b, pyMul(1.0, glow)), pyMul(0.24, ndotl)))
                } else {
                    var cx float64 = 0.0
                    _ = cx
                    var cy float64 = 0.0
                    _ = cy
                    var cz float64 = 0.0
                    _ = cz
                    var rad float64 = 1.0
                    _ = rad
                    if (pyBool((hit_kind == 2))) {
                        cx = s0x
                        cy = s0y
                        cz = s0z
                        rad = 0.65
                    } else {
                        if (pyBool((hit_kind == 3))) {
                            cx = s1x
                            cy = s1y
                            cz = s1z
                            rad = 0.72
                        } else {
                            cx = s2x
                            cy = s2y
                            cz = s2z
                            rad = 0.58
                        }
                    }
                    var hx any = pyAdd(cam_x, pyMul(best_t, dx))
                    _ = hx
                    var hy any = pyAdd(cam_y, pyMul(best_t, dy))
                    _ = hy
                    var hz any = pyAdd(cam_z, pyMul(best_t, dz))
                    _ = hz
                    var __pytra_tuple_19 any = normalize(pyToFloat(pyDiv(pySub(hx, cx), rad)), pyToFloat(pyDiv(pySub(hy, cy), rad)), pyToFloat(pyDiv(pySub(hz, cz), rad)))
                    _ = __pytra_tuple_19
                    var nx any = pyGet(__pytra_tuple_19, 0)
                    _ = nx
                    var ny any = pyGet(__pytra_tuple_19, 1)
                    _ = ny
                    var nz any = pyGet(__pytra_tuple_19, 2)
                    _ = nz
                    var __pytra_tuple_20 any = reflect(pyToFloat(dx), pyToFloat(dy), pyToFloat(dz), pyToFloat(nx), pyToFloat(ny), pyToFloat(nz))
                    _ = __pytra_tuple_20
                    var rdx any = pyGet(__pytra_tuple_20, 0)
                    _ = rdx
                    var rdy any = pyGet(__pytra_tuple_20, 1)
                    _ = rdy
                    var rdz any = pyGet(__pytra_tuple_20, 2)
                    _ = rdz
                    var __pytra_tuple_21 any = refract(pyToFloat(dx), pyToFloat(dy), pyToFloat(dz), pyToFloat(nx), pyToFloat(ny), pyToFloat(nz), (1.0 / 1.45))
                    _ = __pytra_tuple_21
                    var tdx any = pyGet(__pytra_tuple_21, 0)
                    _ = tdx
                    var tdy any = pyGet(__pytra_tuple_21, 1)
                    _ = tdy
                    var tdz any = pyGet(__pytra_tuple_21, 2)
                    _ = tdz
                    var __pytra_tuple_22 any = sky_color(pyToFloat(rdx), pyToFloat(rdy), pyToFloat(rdz), pyToFloat(tphase))
                    _ = __pytra_tuple_22
                    var sr any = pyGet(__pytra_tuple_22, 0)
                    _ = sr
                    var sg any = pyGet(__pytra_tuple_22, 1)
                    _ = sg
                    var sb any = pyGet(__pytra_tuple_22, 2)
                    _ = sb
                    var __pytra_tuple_23 any = sky_color(pyToFloat(tdx), pyToFloat(tdy), pyToFloat(tdz), pyToFloat(pyAdd(tphase, 0.8)))
                    _ = __pytra_tuple_23
                    var tr any = pyGet(__pytra_tuple_23, 0)
                    _ = tr
                    var tg any = pyGet(__pytra_tuple_23, 1)
                    _ = tg
                    var tb any = pyGet(__pytra_tuple_23, 2)
                    _ = tb
                    var cosi any = pyMax(pyNeg(pyAdd(pyAdd(pyMul(dx, nx), pyMul(dy, ny)), pyMul(dz, nz))), 0.0)
                    _ = cosi
                    var fr any = schlick(pyToFloat(cosi), 0.04)
                    _ = fr
                    r = pyToFloat(pyAdd(pyMul(tr, pySub(1.0, fr)), pyMul(sr, fr)))
                    g = pyToFloat(pyAdd(pyMul(tg, pySub(1.0, fr)), pyMul(sg, fr)))
                    b = pyToFloat(pyAdd(pyMul(tb, pySub(1.0, fr)), pyMul(sb, fr)))
                    var lxv any = pySub(lx, hx)
                    _ = lxv
                    var lyv any = pySub(ly, hy)
                    _ = lyv
                    var lzv any = pySub(lz, hz)
                    _ = lzv
                    var __pytra_tuple_24 any = normalize(pyToFloat(lxv), pyToFloat(lyv), pyToFloat(lzv))
                    _ = __pytra_tuple_24
                    var ldx any = pyGet(__pytra_tuple_24, 0)
                    _ = ldx
                    var ldy any = pyGet(__pytra_tuple_24, 1)
                    _ = ldy
                    var ldz any = pyGet(__pytra_tuple_24, 2)
                    _ = ldz
                    var ndotl any = pyMax(pyAdd(pyAdd(pyMul(nx, ldx), pyMul(ny, ldy)), pyMul(nz, ldz)), 0.0)
                    _ = ndotl
                    var __pytra_tuple_25 any = normalize(pyToFloat(pySub(ldx, dx)), pyToFloat(pySub(ldy, dy)), pyToFloat(pySub(ldz, dz)))
                    _ = __pytra_tuple_25
                    var hvx any = pyGet(__pytra_tuple_25, 0)
                    _ = hvx
                    var hvy any = pyGet(__pytra_tuple_25, 1)
                    _ = hvy
                    var hvz any = pyGet(__pytra_tuple_25, 2)
                    _ = hvz
                    var ndoth any = pyMax(pyAdd(pyAdd(pyMul(nx, hvx), pyMul(ny, hvy)), pyMul(nz, hvz)), 0.0)
                    _ = ndoth
                    var spec any = pyMul(ndoth, ndoth)
                    _ = spec
                    spec = pyMul(spec, spec)
                    spec = pyMul(spec, spec)
                    spec = pyMul(spec, spec)
                    var glow any = pyDiv(10.0, pyAdd(pyAdd(pyAdd(1.0, pyMul(lxv, lxv)), pyMul(lyv, lyv)), pyMul(lzv, lzv)))
                    _ = glow
                    r = (r + pyToFloat(pyAdd(pyAdd(pyMul(0.2, ndotl), pyMul(0.8, spec)), pyMul(0.45, glow))))
                    g = (g + pyToFloat(pyAdd(pyAdd(pyMul(0.18, ndotl), pyMul(0.6, spec)), pyMul(0.35, glow))))
                    b = (b + pyToFloat(pyAdd(pyAdd(pyMul(0.26, ndotl), pyMul(1.0, spec)), pyMul(0.65, glow))))
                    if (pyBool((hit_kind == 2))) {
                        r = (r * 0.95)
                        g = (g * 1.05)
                        b = (b * 1.1)
                    } else {
                        if (pyBool((hit_kind == 3))) {
                            r = (r * 1.08)
                            g = (g * 0.98)
                            b = (b * 1.04)
                        } else {
                            r = (r * 1.02)
                            g = (g * 1.1)
                            b = (b * 0.95)
                        }
                    }
                }
            }
            r = math.Sqrt(pyToFloat(clamp01(r)))
            g = math.Sqrt(pyToFloat(clamp01(g)))
            b = math.Sqrt(pyToFloat(clamp01(b)))
            pySet(frame, i, quantize_332(r, g, b))
            i = (i + 1)
        }
    }
    return pyBytes(frame)
}

func run_16_glass_sculpture_chaos() any {
    var width int = 320
    _ = width
    var height int = 240
    _ = height
    var frames_n int = 72
    _ = frames_n
    var out_path string = "sample/out/16_glass_sculpture_chaos.gif"
    _ = out_path
    var start any = pyPerfCounter()
    _ = start
    var frames any = []any{}
    _ = frames
    __pytra_range_start_26 := pyToInt(0)
    __pytra_range_stop_27 := pyToInt(frames_n)
    __pytra_range_step_28 := pyToInt(1)
    if __pytra_range_step_28 == 0 { panic("range() step must not be zero") }
    var i int = 0
    _ = i
    for __pytra_i_29 := __pytra_range_start_26; (__pytra_range_step_28 > 0 && __pytra_i_29 < __pytra_range_stop_27) || (__pytra_range_step_28 < 0 && __pytra_i_29 > __pytra_range_stop_27); __pytra_i_29 += __pytra_range_step_28 {
        i = __pytra_i_29
        frames = pyAppend(frames, render_frame(width, height, i, frames_n))
    }
    pySaveGIF(out_path, width, height, frames, palette_332(), 6, 0)
    var elapsed any = pySub(pyPerfCounter(), start)
    _ = elapsed
    pyPrint("output:", out_path)
    pyPrint("frames:", frames_n)
    pyPrint("elapsed_sec:", elapsed)
    return nil
}

func main() {
    run_16_glass_sculpture_chaos()
}
