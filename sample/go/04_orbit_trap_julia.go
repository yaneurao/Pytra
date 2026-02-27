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

func render_orbit_trap_julia(width int64, height int64, max_iter int64, cx float64, cy float64) []any {
    var pixels []any = __pytra_as_list([]any{})
    __step_0 := __pytra_int(int64(1))
    for y := __pytra_int(int64(0)); (__step_0 >= 0 && y < __pytra_int(height)) || (__step_0 < 0 && y > __pytra_int(height)); y += __step_0 {
        var zy0 float64 = __pytra_float((__pytra_float((-float64(1.3))) + __pytra_float((__pytra_float(float64(2.6)) * __pytra_float((__pytra_float(y) / __pytra_float((__pytra_int(height) - __pytra_int(int64(1))))))))))
        __step_1 := __pytra_int(int64(1))
        for x := __pytra_int(int64(0)); (__step_1 >= 0 && x < __pytra_int(width)) || (__step_1 < 0 && x > __pytra_int(width)); x += __step_1 {
            var zx float64 = __pytra_float((__pytra_float((-float64(1.9))) + __pytra_float((__pytra_float(float64(3.8)) * __pytra_float((__pytra_float(x) / __pytra_float((__pytra_int(width) - __pytra_int(int64(1))))))))))
            var zy float64 = __pytra_float(zy0)
            var trap float64 = __pytra_float(float64(1000000000.0))
            var i int64 = __pytra_int(int64(0))
            for (__pytra_int(i) < __pytra_int(max_iter)) {
                var ax float64 = __pytra_float(zx)
                if (__pytra_float(ax) < __pytra_float(float64(0.0))) {
                    ax = __pytra_float((-ax))
                }
                var ay float64 = __pytra_float(zy)
                if (__pytra_float(ay) < __pytra_float(float64(0.0))) {
                    ay = __pytra_float((-ay))
                }
                var dxy float64 = __pytra_float((__pytra_float(zx) - __pytra_float(zy)))
                if (__pytra_float(dxy) < __pytra_float(float64(0.0))) {
                    dxy = __pytra_float((-dxy))
                }
                if (__pytra_float(ax) < __pytra_float(trap)) {
                    trap = __pytra_float(ax)
                }
                if (__pytra_float(ay) < __pytra_float(trap)) {
                    trap = __pytra_float(ay)
                }
                if (__pytra_float(dxy) < __pytra_float(trap)) {
                    trap = __pytra_float(dxy)
                }
                var zx2 float64 = __pytra_float((__pytra_float(zx) * __pytra_float(zx)))
                var zy2 float64 = __pytra_float((__pytra_float(zy) * __pytra_float(zy)))
                if (__pytra_float((__pytra_float(zx2) + __pytra_float(zy2))) > __pytra_float(float64(4.0))) {
                    break
                }
                zy = __pytra_float((__pytra_float((__pytra_float((__pytra_float(float64(2.0)) * __pytra_float(zx))) * __pytra_float(zy))) + __pytra_float(cy)))
                zx = __pytra_float((__pytra_float((__pytra_float(zx2) - __pytra_float(zy2))) + __pytra_float(cx)))
                i += int64(1)
            }
            var r int64 = __pytra_int(int64(0))
            var g int64 = __pytra_int(int64(0))
            var b int64 = __pytra_int(int64(0))
            if (__pytra_int(i) >= __pytra_int(max_iter)) {
                r = __pytra_int(int64(0))
                g = __pytra_int(int64(0))
                b = __pytra_int(int64(0))
            } else {
                var trap_scaled float64 = __pytra_float((__pytra_float(trap) * __pytra_float(float64(3.2))))
                if (__pytra_float(trap_scaled) > __pytra_float(float64(1.0))) {
                    trap_scaled = __pytra_float(float64(1.0))
                }
                if (__pytra_float(trap_scaled) < __pytra_float(float64(0.0))) {
                    trap_scaled = __pytra_float(float64(0.0))
                }
                var t float64 = __pytra_float((__pytra_float(i) / __pytra_float(max_iter)))
                var tone int64 = __pytra_int(__pytra_int((__pytra_float(float64(255.0)) * __pytra_float((__pytra_float(float64(1.0)) - __pytra_float(trap_scaled))))))
                r = __pytra_int(__pytra_int((__pytra_float(tone) * __pytra_float((__pytra_float(float64(0.35)) + __pytra_float((__pytra_float(float64(0.65)) * __pytra_float(t))))))))
                g = __pytra_int(__pytra_int((__pytra_float(tone) * __pytra_float((__pytra_float(float64(0.15)) + __pytra_float((__pytra_float(float64(0.85)) * __pytra_float((__pytra_float(float64(1.0)) - __pytra_float(t))))))))))
                b = __pytra_int(__pytra_int((__pytra_float(float64(255.0)) * __pytra_float((__pytra_float(float64(0.25)) + __pytra_float((__pytra_float(float64(0.75)) * __pytra_float(t))))))))
                if (__pytra_int(r) > __pytra_int(int64(255))) {
                    r = __pytra_int(int64(255))
                }
                if (__pytra_int(g) > __pytra_int(int64(255))) {
                    g = __pytra_int(int64(255))
                }
                if (__pytra_int(b) > __pytra_int(int64(255))) {
                    b = __pytra_int(int64(255))
                }
            }
            pixels = append(__pytra_as_list(pixels), r)
            pixels = append(__pytra_as_list(pixels), g)
            pixels = append(__pytra_as_list(pixels), b)
        }
    }
    return pixels
}

func run_04_orbit_trap_julia() {
    var width int64 = __pytra_int(int64(1920))
    var height int64 = __pytra_int(int64(1080))
    var max_iter int64 = __pytra_int(int64(1400))
    var out_path string = __pytra_str("sample/out/04_orbit_trap_julia.png")
    var start float64 = __pytra_float(__pytra_perf_counter())
    var pixels []any = __pytra_as_list(render_orbit_trap_julia(width, height, max_iter, (-float64(0.7269)), float64(0.1889)))
    __pytra_noop(out_path, width, height, pixels)
    var elapsed float64 = __pytra_float((__pytra_perf_counter() - start))
    __pytra_print("output:", out_path)
    __pytra_print("size:", width, "x", height)
    __pytra_print("max_iter:", max_iter)
    __pytra_print("elapsed_sec:", elapsed)
}

func main() {
    run_04_orbit_trap_julia()
}
