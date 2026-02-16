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

var __cls_Token = map[any]any{}
func NewToken(__args ...any) map[any]any {
    self := map[any]any{"__class": "Token"}
    var kind any = nil
    if len(__args) > 0 { kind = __args[0] }
    self["kind"] = kind
    var text any = nil
    if len(__args) > 1 { text = __args[1] }
    self["text"] = text
    var pos any = nil
    if len(__args) > 2 { pos = __args[2] }
    self["pos"] = pos
    return self
}

var __cls_ExprNode = map[any]any{}
func NewExprNode(__args ...any) map[any]any {
    self := map[any]any{"__class": "ExprNode"}
    var kind any = nil
    if len(__args) > 0 { kind = __args[0] }
    self["kind"] = kind
    var value any = nil
    if len(__args) > 1 { value = __args[1] }
    self["value"] = value
    var name any = nil
    if len(__args) > 2 { name = __args[2] }
    self["name"] = name
    var op any = nil
    if len(__args) > 3 { op = __args[3] }
    self["op"] = op
    var left any = nil
    if len(__args) > 4 { left = __args[4] }
    self["left"] = left
    var right any = nil
    if len(__args) > 5 { right = __args[5] }
    self["right"] = right
    return self
}

var __cls_StmtNode = map[any]any{}
func NewStmtNode(__args ...any) map[any]any {
    self := map[any]any{"__class": "StmtNode"}
    var kind any = nil
    if len(__args) > 0 { kind = __args[0] }
    self["kind"] = kind
    var name any = nil
    if len(__args) > 1 { name = __args[1] }
    self["name"] = name
    var expr_index any = nil
    if len(__args) > 2 { expr_index = __args[2] }
    self["expr_index"] = expr_index
    return self
}

var __cls_Parser = map[any]any{}
func NewParser(tokens any) map[any]any {
    self := map[any]any{"__class": "Parser"}
    pySet(self, "tokens", tokens)
    pySet(self, "pos", 0)
    pySet(self, "expr_nodes", Parser_new_expr_nodes(self))
    return self
}
func Parser_new_expr_nodes(self map[any]any) any {
    var nodes any = []any{}
    _ = nodes
    return nodes
}
func Parser_peek_kind(self map[any]any) any {
    return pyGet(pyGet(pyGet(self, "tokens"), pyGet(self, "pos")), "kind")
}
func Parser_match(self map[any]any, kind string) any {
    if (pyBool(pyEq(Parser_peek_kind(self), kind))) {
        pySet(self, "pos", pyAdd(pyGet(self, "pos"), 1))
        return true
    }
    return false
}
func Parser_expect(self map[any]any, kind string) any {
    if (pyBool(pyNe(Parser_peek_kind(self), kind))) {
        var t any = pyGet(pyGet(self, "tokens"), pyGet(self, "pos"))
        _ = t
        panic(pyAdd(pyAdd(pyAdd(pyAdd(pyAdd("parse error at pos=", pyToString(pyGet(t, "pos"))), ", expected="), kind), ", got="), pyGet(t, "kind")))
    }
    var token any = pyGet(pyGet(self, "tokens"), pyGet(self, "pos"))
    _ = token
    pySet(self, "pos", pyAdd(pyGet(self, "pos"), 1))
    return token
}
func Parser_skip_newlines(self map[any]any) any {
    for pyBool(Parser_match(self, "NEWLINE")) {
    }
    return nil
}
func Parser_add_expr(self map[any]any, node any) any {
    pySet(self, "expr_nodes", pyAppend(pyGet(self, "expr_nodes"), node))
    return pySub(pyLen(pyGet(self, "expr_nodes")), 1)
}
func Parser_parse_program(self map[any]any) any {
    var stmts any = []any{}
    _ = stmts
    Parser_skip_newlines(self)
    for pyBool(pyNe(Parser_peek_kind(self), "EOF")) {
        var stmt any = Parser_parse_stmt(self)
        _ = stmt
        stmts = pyAppend(stmts, stmt)
        Parser_skip_newlines(self)
    }
    return stmts
}
func Parser_parse_stmt(self map[any]any) any {
    if (pyBool(Parser_match(self, "LET"))) {
        var let_name string = pyToString(pyGet(Parser_expect(self, "IDENT"), "text"))
        _ = let_name
        Parser_expect(self, "EQUAL")
        var let_expr_index int = pyToInt(Parser_parse_expr(self))
        _ = let_expr_index
        return NewStmtNode("let", let_name, let_expr_index)
    }
    if (pyBool(Parser_match(self, "PRINT"))) {
        var print_expr_index int = pyToInt(Parser_parse_expr(self))
        _ = print_expr_index
        return NewStmtNode("print", "", print_expr_index)
    }
    var assign_name string = pyToString(pyGet(Parser_expect(self, "IDENT"), "text"))
    _ = assign_name
    Parser_expect(self, "EQUAL")
    var assign_expr_index int = pyToInt(Parser_parse_expr(self))
    _ = assign_expr_index
    return NewStmtNode("assign", assign_name, assign_expr_index)
}
func Parser_parse_expr(self map[any]any) any {
    return Parser_parse_add(self)
}
func Parser_parse_add(self map[any]any) any {
    var left int = pyToInt(Parser_parse_mul(self))
    _ = left
    var done bool = false
    _ = done
    for pyBool((!pyBool(done))) {
        if (pyBool(Parser_match(self, "PLUS"))) {
            var right int = pyToInt(Parser_parse_mul(self))
            _ = right
            left = pyToInt(Parser_add_expr(self, NewExprNode("bin", 0, "", "+", left, right)))
            continue
        }
        if (pyBool(Parser_match(self, "MINUS"))) {
            var right any = Parser_parse_mul(self)
            _ = right
            left = pyToInt(Parser_add_expr(self, NewExprNode("bin", 0, "", "-", left, right)))
            continue
        }
        done = true
    }
    return left
}
func Parser_parse_mul(self map[any]any) any {
    var left int = pyToInt(Parser_parse_unary(self))
    _ = left
    var done bool = false
    _ = done
    for pyBool((!pyBool(done))) {
        if (pyBool(Parser_match(self, "STAR"))) {
            var right int = pyToInt(Parser_parse_unary(self))
            _ = right
            left = pyToInt(Parser_add_expr(self, NewExprNode("bin", 0, "", "*", left, right)))
            continue
        }
        if (pyBool(Parser_match(self, "SLASH"))) {
            var right any = Parser_parse_unary(self)
            _ = right
            left = pyToInt(Parser_add_expr(self, NewExprNode("bin", 0, "", "/", left, right)))
            continue
        }
        done = true
    }
    return left
}
func Parser_parse_unary(self map[any]any) any {
    if (pyBool(Parser_match(self, "MINUS"))) {
        var child int = pyToInt(Parser_parse_unary(self))
        _ = child
        return Parser_add_expr(self, NewExprNode("neg", 0, "", "", child, (-1)))
    }
    return Parser_parse_primary(self)
}
func Parser_parse_primary(self map[any]any) any {
    if (pyBool(Parser_match(self, "NUMBER"))) {
        var token_num any = pyGet(pyGet(self, "tokens"), pySub(pyGet(self, "pos"), 1))
        _ = token_num
        var parsed_value int = 0
        _ = parsed_value
        var idx int = 0
        _ = idx
        for pyBool(pyLt(idx, pyLen(pyGet(token_num, "text")))) {
            var ch string = pyToString(pySlice(pyGet(token_num, "text"), idx, (idx + 1)))
            _ = ch
            parsed_value = pyToInt(pySub(pyAdd((parsed_value * 10), pyOrd(ch)), pyOrd("0")))
            idx = (idx + 1)
        }
        return Parser_add_expr(self, NewExprNode("lit", parsed_value, "", "", (-1), (-1)))
    }
    if (pyBool(Parser_match(self, "IDENT"))) {
        var token_ident any = pyGet(pyGet(self, "tokens"), pySub(pyGet(self, "pos"), 1))
        _ = token_ident
        return Parser_add_expr(self, NewExprNode("var", 0, pyGet(token_ident, "text"), "", (-1), (-1)))
    }
    if (pyBool(Parser_match(self, "LPAREN"))) {
        var expr_index int = pyToInt(Parser_parse_expr(self))
        _ = expr_index
        Parser_expect(self, "RPAREN")
        return expr_index
    }
    var t any = pyGet(pyGet(self, "tokens"), pyGet(self, "pos"))
    _ = t
    panic(pyAdd(pyAdd(pyAdd("primary parse error at pos=", pyToString(pyGet(t, "pos"))), " got="), pyGet(t, "kind")))
}

func tokenize(lines any) any {
    var tokens any = []any{}
    _ = tokens
    var line_index int = 0
    _ = line_index
    for pyBool(pyLt(line_index, pyLen(lines))) {
        var source string = pyToString(pyGet(lines, line_index))
        _ = source
        var i int = 0
        _ = i
        var n int = pyToInt(pyLen(source))
        _ = n
        for pyBool((i < n)) {
            var ch string = pyToString(pySlice(source, i, (i + 1)))
            _ = ch
            if (pyBool(pyEq(ch, " "))) {
                i = (i + 1)
                continue
            }
            if (pyBool(pyEq(ch, "+"))) {
                tokens = pyAppend(tokens, NewToken("PLUS", ch, i))
                i = (i + 1)
                continue
            }
            if (pyBool(pyEq(ch, "-"))) {
                tokens = pyAppend(tokens, NewToken("MINUS", ch, i))
                i = (i + 1)
                continue
            }
            if (pyBool(pyEq(ch, "*"))) {
                tokens = pyAppend(tokens, NewToken("STAR", ch, i))
                i = (i + 1)
                continue
            }
            if (pyBool(pyEq(ch, "/"))) {
                tokens = pyAppend(tokens, NewToken("SLASH", ch, i))
                i = (i + 1)
                continue
            }
            if (pyBool(pyEq(ch, "("))) {
                tokens = pyAppend(tokens, NewToken("LPAREN", ch, i))
                i = (i + 1)
                continue
            }
            if (pyBool(pyEq(ch, ")"))) {
                tokens = pyAppend(tokens, NewToken("RPAREN", ch, i))
                i = (i + 1)
                continue
            }
            if (pyBool(pyEq(ch, "="))) {
                tokens = pyAppend(tokens, NewToken("EQUAL", ch, i))
                i = (i + 1)
                continue
            }
            if (pyBool(pyIsDigit(ch))) {
                var start int = i
                _ = start
                for pyBool((pyBool((i < n)) && pyBool(pyIsDigit(pySlice(source, i, (i + 1)))))) {
                    i = (i + 1)
                }
                var text string = pyToString(pySlice(source, start, i))
                _ = text
                tokens = pyAppend(tokens, NewToken("NUMBER", text, start))
                continue
            }
            if (pyBool((pyBool(pyIsAlpha(ch)) || pyBool(pyEq(ch, "_"))))) {
                var start int = i
                _ = start
                for pyBool((pyBool((i < n)) && pyBool((pyBool((pyBool(pyIsAlpha(pySlice(source, i, (i + 1)))) || pyBool(pyEq(pySlice(source, i, (i + 1)), "_")))) || pyBool(pyIsDigit(pySlice(source, i, (i + 1)))))))) {
                    i = (i + 1)
                }
                var text any = pySlice(source, start, i)
                _ = text
                if (pyBool(pyEq(text, "let"))) {
                    tokens = pyAppend(tokens, NewToken("LET", text, start))
                } else {
                    if (pyBool(pyEq(text, "print"))) {
                        tokens = pyAppend(tokens, NewToken("PRINT", text, start))
                    } else {
                        tokens = pyAppend(tokens, NewToken("IDENT", text, start))
                    }
                }
                continue
            }
            panic(pyAdd(pyAdd(pyAdd(pyAdd(pyAdd("tokenize error at line=", pyToString(line_index)), " pos="), pyToString(i)), " ch="), ch))
        }
        tokens = pyAppend(tokens, NewToken("NEWLINE", "", n))
        line_index = (line_index + 1)
    }
    tokens = pyAppend(tokens, NewToken("EOF", "", pyLen(lines)))
    return tokens
}

func eval_expr(expr_index int, expr_nodes any, env any) any {
    if (pyBool(false)) {
        pySet(env, "__dummy__", 0)
    }
    var node any = pyGet(expr_nodes, expr_index)
    _ = node
    if (pyBool(pyEq(pyGet(node, "kind"), "lit"))) {
        return pyGet(node, "value")
    }
    if (pyBool(pyEq(pyGet(node, "kind"), "var"))) {
        if (pyBool((!pyBool(pyIn(pyGet(node, "name"), env))))) {
            panic(pyAdd("undefined variable: ", pyGet(node, "name")))
        }
        return pyGet(env, pyGet(node, "name"))
    }
    if (pyBool(pyEq(pyGet(node, "kind"), "neg"))) {
        return pyNeg(eval_expr(pyToInt(pyGet(node, "left")), expr_nodes, env))
    }
    if (pyBool(pyEq(pyGet(node, "kind"), "bin"))) {
        var lhs int = pyToInt(eval_expr(pyToInt(pyGet(node, "left")), expr_nodes, env))
        _ = lhs
        var rhs int = pyToInt(eval_expr(pyToInt(pyGet(node, "right")), expr_nodes, env))
        _ = rhs
        if (pyBool(pyEq(pyGet(node, "op"), "+"))) {
            return (lhs + rhs)
        }
        if (pyBool(pyEq(pyGet(node, "op"), "-"))) {
            return (lhs - rhs)
        }
        if (pyBool(pyEq(pyGet(node, "op"), "*"))) {
            return (lhs * rhs)
        }
        if (pyBool(pyEq(pyGet(node, "op"), "/"))) {
            if (pyBool((rhs == 0))) {
                panic("division by zero")
            }
            return (lhs / rhs)
        }
        panic(pyAdd("unknown operator: ", pyGet(node, "op")))
    }
    panic(pyAdd("unknown node kind: ", pyGet(node, "kind")))
}

func execute(stmts any, expr_nodes any, trace bool) any {
    var env any = map[any]any{}
    _ = env
    var checksum int = 0
    _ = checksum
    var printed int = 0
    _ = printed
    var stmt any = nil
    _ = stmt
    for _, __pytra_it_1 := range pyIter(stmts) {
        stmt = __pytra_it_1
        if (pyBool(pyEq(pyGet(stmt, "kind"), "let"))) {
            pySet(env, pyGet(stmt, "name"), eval_expr(pyToInt(pyGet(stmt, "expr_index")), expr_nodes, env))
            continue
        }
        if (pyBool(pyEq(pyGet(stmt, "kind"), "assign"))) {
            if (pyBool((!pyBool(pyIn(pyGet(stmt, "name"), env))))) {
                panic(pyAdd("assign to undefined variable: ", pyGet(stmt, "name")))
            }
            pySet(env, pyGet(stmt, "name"), eval_expr(pyToInt(pyGet(stmt, "expr_index")), expr_nodes, env))
            continue
        }
        var value int = pyToInt(eval_expr(pyToInt(pyGet(stmt, "expr_index")), expr_nodes, env))
        _ = value
        if (pyBool(trace)) {
            pyPrint(value)
        }
        var norm int = (value % 1000000007)
        _ = norm
        if (pyBool((norm < 0))) {
            norm = (norm + 1000000007)
        }
        checksum = (((checksum * 131) + norm) % 1000000007)
        printed = (printed + 1)
    }
    if (pyBool(trace)) {
        pyPrint("printed:", printed)
    }
    return checksum
}

func build_benchmark_source(var_count int, loops int) any {
    var lines any = []any{}
    _ = lines
    __pytra_range_start_2 := pyToInt(0)
    __pytra_range_stop_3 := pyToInt(var_count)
    __pytra_range_step_4 := pyToInt(1)
    if __pytra_range_step_4 == 0 { panic("range() step must not be zero") }
    var i int = 0
    _ = i
    for __pytra_i_5 := __pytra_range_start_2; (__pytra_range_step_4 > 0 && __pytra_i_5 < __pytra_range_stop_3) || (__pytra_range_step_4 < 0 && __pytra_i_5 > __pytra_range_stop_3); __pytra_i_5 += __pytra_range_step_4 {
        i = __pytra_i_5
        lines = pyAppend(lines, pyAdd(pyAdd(pyAdd("let v", pyToString(i)), " = "), pyToString((i + 1))))
    }
    __pytra_range_start_6 := pyToInt(0)
    __pytra_range_stop_7 := pyToInt(loops)
    __pytra_range_step_8 := pyToInt(1)
    if __pytra_range_step_8 == 0 { panic("range() step must not be zero") }
    for __pytra_i_9 := __pytra_range_start_6; (__pytra_range_step_8 > 0 && __pytra_i_9 < __pytra_range_stop_7) || (__pytra_range_step_8 < 0 && __pytra_i_9 > __pytra_range_stop_7); __pytra_i_9 += __pytra_range_step_8 {
        i = __pytra_i_9
        var x int = (i % var_count)
        _ = x
        var y int = ((i + 3) % var_count)
        _ = y
        var c1 int = ((i % 7) + 1)
        _ = c1
        var c2 int = ((i % 11) + 2)
        _ = c2
        lines = pyAppend(lines, pyAdd(pyAdd(pyAdd(pyAdd(pyAdd(pyAdd(pyAdd(pyAdd(pyAdd("v", pyToString(x)), " = (v"), pyToString(x)), " * "), pyToString(c1)), " + v"), pyToString(y)), " + 10000) / "), pyToString(c2)))
        if (pyBool(((i % 97) == 0))) {
            lines = pyAppend(lines, pyAdd("print v", pyToString(x)))
        }
    }
    lines = pyAppend(lines, "print (v0 + v1 + v2 + v3)")
    return lines
}

func run_demo() any {
    var demo_lines any = []any{}
    _ = demo_lines
    demo_lines = pyAppend(demo_lines, "let a = 10")
    demo_lines = pyAppend(demo_lines, "let b = 3")
    demo_lines = pyAppend(demo_lines, "a = (a + b) * 2")
    demo_lines = pyAppend(demo_lines, "print a")
    demo_lines = pyAppend(demo_lines, "print a / b")
    var tokens any = tokenize(demo_lines)
    _ = tokens
    var parser any = NewParser(tokens)
    _ = parser
    var stmts any = Parser_parse_program(parser.(map[any]any))
    _ = stmts
    var checksum int = pyToInt(execute(stmts, pyGet(parser, "expr_nodes"), true))
    _ = checksum
    pyPrint("demo_checksum:", checksum)
    return nil
}

func run_benchmark() any {
    var source_lines any = build_benchmark_source(32, 120000)
    _ = source_lines
    var start float64 = pyToFloat(pyPerfCounter())
    _ = start
    var tokens any = tokenize(source_lines)
    _ = tokens
    var parser any = NewParser(tokens)
    _ = parser
    var stmts any = Parser_parse_program(parser.(map[any]any))
    _ = stmts
    var checksum int = pyToInt(execute(stmts, pyGet(parser, "expr_nodes"), false))
    _ = checksum
    var elapsed float64 = pyToFloat(pySub(pyPerfCounter(), start))
    _ = elapsed
    pyPrint("token_count:", pyLen(tokens))
    pyPrint("expr_count:", pyLen(pyGet(parser, "expr_nodes")))
    pyPrint("stmt_count:", pyLen(stmts))
    pyPrint("checksum:", checksum)
    pyPrint("elapsed_sec:", elapsed)
    return nil
}

func py_main() any {
    run_demo()
    run_benchmark()
    return nil
}

func main() {
    py_main()
}
