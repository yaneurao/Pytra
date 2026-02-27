// Auto-generated Pytra Go native source from EAST3.
package main

import (
    "fmt"
    "math"
    "strconv"
    "time"
    "unicode"
)

var _ = math.Pi

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

func color_palette() []any {
    var p []any = __pytra_as_list([]any{})
    __step_0 := __pytra_int(int64(1))
    for i := __pytra_int(int64(0)); (__step_0 >= 0 && i < __pytra_int(int64(256))) || (__step_0 < 0 && i > __pytra_int(int64(256))); i += __step_0 {
        var r int64 = __pytra_int(i)
        var g int64 = __pytra_int((__pytra_int((__pytra_int(i) * __pytra_int(int64(3)))) % __pytra_int(int64(256))))
        var b int64 = __pytra_int((__pytra_int(int64(255)) - __pytra_int(i)))
        p = append(__pytra_as_list(p), r)
        p = append(__pytra_as_list(p), g)
        p = append(__pytra_as_list(p), b)
    }
    return __pytra_bytes(p)
}

func run_11_lissajous_particles() {
    var w int64 = __pytra_int(int64(320))
    var h int64 = __pytra_int(int64(240))
    var frames_n int64 = __pytra_int(int64(360))
    var particles int64 = __pytra_int(int64(48))
    var out_path string = __pytra_str("sample/out/11_lissajous_particles.gif")
    var start float64 = __pytra_float(__pytra_perf_counter())
    var frames []any = __pytra_as_list([]any{})
    __step_0 := __pytra_int(int64(1))
    for t := __pytra_int(int64(0)); (__step_0 >= 0 && t < __pytra_int(frames_n)) || (__step_0 < 0 && t > __pytra_int(frames_n)); t += __step_0 {
        var frame []any = __pytra_as_list(__pytra_bytearray((__pytra_int(w) * __pytra_int(h))))
        __step_1 := __pytra_int(int64(1))
        for p := __pytra_int(int64(0)); (__step_1 >= 0 && p < __pytra_int(particles)) || (__step_1 < 0 && p > __pytra_int(particles)); p += __step_1 {
            var phase float64 = __pytra_float((__pytra_float(p) * __pytra_float(float64(0.261799))))
            var x int64 = __pytra_int(__pytra_int(((__pytra_float(w) * __pytra_float(float64(0.5))) + ((__pytra_float(w) * __pytra_float(float64(0.38))) * math.Sin(__pytra_float((__pytra_float((__pytra_float(float64(0.11)) * __pytra_float(t))) + __pytra_float((__pytra_float(phase) * __pytra_float(float64(2.0)))))))))))
            var y int64 = __pytra_int(__pytra_int(((__pytra_float(h) * __pytra_float(float64(0.5))) + ((__pytra_float(h) * __pytra_float(float64(0.38))) * math.Sin(__pytra_float((__pytra_float((__pytra_float(float64(0.17)) * __pytra_float(t))) + __pytra_float((__pytra_float(phase) * __pytra_float(float64(3.0)))))))))))
            var color int64 = __pytra_int((__pytra_int(int64(30)) + __pytra_int((__pytra_int((__pytra_int(p) * __pytra_int(int64(9)))) % __pytra_int(int64(220))))))
            __step_2 := __pytra_int(int64(1))
            for dy := __pytra_int((-int64(2))); (__step_2 >= 0 && dy < __pytra_int(int64(3))) || (__step_2 < 0 && dy > __pytra_int(int64(3))); dy += __step_2 {
                __step_3 := __pytra_int(int64(1))
                for dx := __pytra_int((-int64(2))); (__step_3 >= 0 && dx < __pytra_int(int64(3))) || (__step_3 < 0 && dx > __pytra_int(int64(3))); dx += __step_3 {
                    var xx int64 = __pytra_int((__pytra_int(x) + __pytra_int(dx)))
                    var yy int64 = __pytra_int((__pytra_int(y) + __pytra_int(dy)))
                    if ((__pytra_int(xx) >= __pytra_int(int64(0))) && (__pytra_int(xx) < __pytra_int(w)) && (__pytra_int(yy) >= __pytra_int(int64(0))) && (__pytra_int(yy) < __pytra_int(h))) {
                        var d2 int64 = __pytra_int((__pytra_int((__pytra_int(dx) * __pytra_int(dx))) + __pytra_int((__pytra_int(dy) * __pytra_int(dy)))))
                        if (__pytra_int(d2) <= __pytra_int(int64(4))) {
                            var idx int64 = __pytra_int((__pytra_int((__pytra_int(yy) * __pytra_int(w))) + __pytra_int(xx)))
                            var v int64 = __pytra_int((__pytra_int(color) - __pytra_int((__pytra_int(d2) * __pytra_int(int64(20))))))
                            v = __pytra_int(__pytra_max(int64(0), v))
                            if (__pytra_int(v) > __pytra_int(__pytra_int(__pytra_get_index(frame, idx)))) {
                                __pytra_set_index(frame, idx, v)
                            }
                        }
                    }
                }
            }
        }
        frames = append(__pytra_as_list(frames), __pytra_bytes(frame))
    }
    __pytra_noop(out_path, w, h, frames, color_palette())
    var elapsed float64 = __pytra_float((__pytra_perf_counter() - start))
    __pytra_print("output:", out_path)
    __pytra_print("frames:", frames_n)
    __pytra_print("elapsed_sec:", elapsed)
}

func main() {
    run_11_lissajous_particles()
}
