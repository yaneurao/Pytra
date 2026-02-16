// このファイルは自動生成です（Python -> Go native mode）。

// Go ネイティブ変換向け Python 互換ランタイム補助。

package main

import (
    "fmt"
    "math"
    "strconv"
    "strings"
)

func pyToString(v any) string {
    switch x := v.(type) {
    case nil:
        return "None"
    case bool:
        if x { return "True" }
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
        for _, it := range x { parts = append(parts, pyToString(it)) }
        return "[" + strings.Join(parts, ", ") + "]"
    case map[any]any:
        parts := make([]string, 0, len(x))
        for k, v := range x { parts = append(parts, pyToString(k)+": "+pyToString(v)) }
        return "{" + strings.Join(parts, ", ") + "}"
    default:
        return fmt.Sprint(x)
    }
}

func pyPrint(args ...any) {
    parts := make([]string, 0, len(args))
    for _, a := range args { parts = append(parts, pyToString(a)) }
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
    case map[any]any:
        return len(x)
    default:
        panic("len() unsupported type")
    }
}

func pyRange(start, stop, step int) []any {
    if step == 0 { panic("range() step must not be zero") }
    out := []any{}
    if step > 0 {
        for i := start; i < stop; i += step { out = append(out, i) }
    } else {
        for i := start; i > stop; i += step { out = append(out, i) }
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
        if x { return 1.0 }
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
        if x { return 1 }
        return 0
    default:
        panic("cannot convert to int")
    }
}

func pyAdd(a, b any) any {
    if sa, ok := a.(string); ok { return sa + pyToString(b) }
    if sb, ok := b.(string); ok { return pyToString(a) + sb }
    _, aInt := a.(int)
    _, bInt := b.(int)
    if aInt && bInt { return pyToInt(a) + pyToInt(b) }
    return pyToFloat(a) + pyToFloat(b)
}
func pySub(a, b any) any {
    _, aInt := a.(int)
    _, bInt := b.(int)
    if aInt && bInt { return pyToInt(a) - pyToInt(b) }
    return pyToFloat(a) - pyToFloat(b)
}
func pyMul(a, b any) any {
    _, aInt := a.(int)
    _, bInt := b.(int)
    if aInt && bInt { return pyToInt(a) * pyToInt(b) }
    return pyToFloat(a) * pyToFloat(b)
}
func pyDiv(a, b any) any { return pyToFloat(a) / pyToFloat(b) }
func pyFloorDiv(a, b any) any { return int(math.Floor(pyToFloat(a) / pyToFloat(b))) }
func pyMod(a, b any) any {
    ai := pyToInt(a)
    bi := pyToInt(b)
    r := ai % bi
    if r != 0 && ((r > 0) != (bi > 0)) { r += bi }
    return r
}
func pyNeg(a any) any {
    if _, ok := a.(int); ok { return -pyToInt(a) }
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
        for _, v := range c { if pyEq(v, item) { return true } }
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
    case string:
        out := []any{}
        for _, ch := range []rune(v) { out = append(out, string(ch)) }
        return out
    case map[any]any:
        out := []any{}
        for k := range v { out = append(out, k) }
        return out
    default:
        panic("iter unsupported")
    }
}

func pyTernary(cond bool, a any, b any) any {
    if cond { return a }
    return b
}

func pyListFromIter(value any) any {
    it := pyIter(value)
    out := make([]any, len(it))
    copy(out, it)
    return out
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

func pySlice(value any, start any, end any) any {
    s := 0
    e := 0
    switch v := value.(type) {
    case string:
        r := []rune(v)
        n := len(r)
        if start == nil { s = 0 } else { s = pyToInt(start); if s < 0 { s += n }; if s < 0 { s = 0 }; if s > n { s = n } }
        if end == nil { e = n } else { e = pyToInt(end); if e < 0 { e += n }; if e < 0 { e = 0 }; if e > n { e = n } }
        if s > e { s = e }
        return string(r[s:e])
    case []any:
        n := len(v)
        if start == nil { s = 0 } else { s = pyToInt(start); if s < 0 { s += n }; if s < 0 { s = 0 }; if s > n { s = n } }
        if end == nil { e = n } else { e = pyToInt(end); if e < 0 { e += n }; if e < 0 { e = 0 }; if e > n { e = n } }
        if s > e { s = e }
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
        if i < 0 { i += len(v) }
        return v[i]
    case map[any]any:
        return v[key]
    case string:
        r := []rune(v)
        i := pyToInt(key)
        if i < 0 { i += len(r) }
        return string(r[i])
    default:
        panic("subscript unsupported")
    }
}

func pySet(value any, key any, newValue any) {
    switch v := value.(type) {
    case []any:
        i := pyToInt(key)
        if i < 0 { i += len(v) }
        v[i] = newValue
    case map[any]any:
        v[key] = newValue
    default:
        panic("setitem unsupported")
    }
}

func pyAppend(lst any, value any) {
    switch v := lst.(type) {
    case *[]any:
        *v = append(*v, value)
    default:
        panic("append unsupported")
    }
}

func pyPop(lst *any, idx any) any {
    arr := (*lst).([]any)
    n := len(arr)
    i := n - 1
    if idx != nil { i = pyToInt(idx); if i < 0 { i += n } }
    val := arr[i]
    arr = append(arr[:i], arr[i+1:]...)
    *lst = arr
    return val
}

func pyOrd(v any) any {
    s := pyToString(v)
    r := []rune(s)
    return int(r[0])
}

func pyChr(v any) any { return string(rune(pyToInt(v))) }

func pyBytearray(size any) any {
    if size == nil { return []any{} }
    n := pyToInt(size)
    out := make([]any, n)
    for i := 0; i < n; i++ { out[i] = 0 }
    return out
}

func pyBytes(v any) any { return v }

func pyIsDigit(v any) bool {
    s := pyToString(v)
    if s == "" { return false }
    for _, ch := range s { if ch < '0' || ch > '9' { return false } }
    return true
}

func pyIsAlpha(v any) bool {
    s := pyToString(v)
    if s == "" { return false }
    for _, ch := range s {
        if !((ch >= 'a' && ch <= 'z') || (ch >= 'A' && ch <= 'Z')) { return false }
    }
    return true
}

func add(a any, b any) any {
    return pyAdd(a, b)
}

func main() {
    pyPrint(add(3, 4))
}
