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

func clamp01(v float64) float64 {
    if (__pytra_float(v) < __pytra_float(float64(0.0))) {
        return float64(0.0)
    }
    if (__pytra_float(v) > __pytra_float(float64(1.0))) {
        return float64(1.0)
    }
    return v
}

func hit_sphere(ox float64, oy float64, oz float64, dx float64, dy float64, dz float64, cx float64, cy float64, cz float64, r float64) float64 {
    var lx float64 = __pytra_float((__pytra_float(ox) - __pytra_float(cx)))
    var ly float64 = __pytra_float((__pytra_float(oy) - __pytra_float(cy)))
    var lz float64 = __pytra_float((__pytra_float(oz) - __pytra_float(cz)))
    var a float64 = __pytra_float((__pytra_float((__pytra_float((__pytra_float(dx) * __pytra_float(dx))) + __pytra_float((__pytra_float(dy) * __pytra_float(dy))))) + __pytra_float((__pytra_float(dz) * __pytra_float(dz)))))
    var b float64 = __pytra_float((__pytra_float(float64(2.0)) * __pytra_float((__pytra_float((__pytra_float((__pytra_float(lx) * __pytra_float(dx))) + __pytra_float((__pytra_float(ly) * __pytra_float(dy))))) + __pytra_float((__pytra_float(lz) * __pytra_float(dz)))))))
    var c float64 = __pytra_float((__pytra_float((__pytra_float((__pytra_float((__pytra_float(lx) * __pytra_float(lx))) + __pytra_float((__pytra_float(ly) * __pytra_float(ly))))) + __pytra_float((__pytra_float(lz) * __pytra_float(lz))))) - __pytra_float((__pytra_float(r) * __pytra_float(r)))))
    var d float64 = __pytra_float((__pytra_float((__pytra_float(b) * __pytra_float(b))) - __pytra_float((__pytra_float((__pytra_float(float64(4.0)) * __pytra_float(a))) * __pytra_float(c)))))
    if (__pytra_float(d) < __pytra_float(float64(0.0))) {
        return (-float64(1.0))
    }
    var sd float64 = __pytra_float(math.Sqrt(__pytra_float(d)))
    var t0 float64 = __pytra_float((__pytra_float((__pytra_float((-b)) - __pytra_float(sd))) / __pytra_float((__pytra_float(float64(2.0)) * __pytra_float(a)))))
    var t1 float64 = __pytra_float((__pytra_float((__pytra_float((-b)) + __pytra_float(sd))) / __pytra_float((__pytra_float(float64(2.0)) * __pytra_float(a)))))
    if (__pytra_float(t0) > __pytra_float(float64(0.001))) {
        return t0
    }
    if (__pytra_float(t1) > __pytra_float(float64(0.001))) {
        return t1
    }
    return (-float64(1.0))
}

func render(width int64, height int64, aa int64) []any {
    var pixels []any = __pytra_as_list([]any{})
    var ox float64 = __pytra_float(float64(0.0))
    var oy float64 = __pytra_float(float64(0.0))
    var oz float64 = __pytra_float((-float64(3.0)))
    var lx float64 = __pytra_float((-float64(0.4)))
    var ly float64 = __pytra_float(float64(0.8))
    var lz float64 = __pytra_float((-float64(0.45)))
    __step_0 := __pytra_int(int64(1))
    for y := __pytra_int(int64(0)); (__step_0 >= 0 && y < __pytra_int(height)) || (__step_0 < 0 && y > __pytra_int(height)); y += __step_0 {
        __step_1 := __pytra_int(int64(1))
        for x := __pytra_int(int64(0)); (__step_1 >= 0 && x < __pytra_int(width)) || (__step_1 < 0 && x > __pytra_int(width)); x += __step_1 {
            var ar int64 = __pytra_int(int64(0))
            var ag int64 = __pytra_int(int64(0))
            var ab int64 = __pytra_int(int64(0))
            __step_2 := __pytra_int(int64(1))
            for ay := __pytra_int(int64(0)); (__step_2 >= 0 && ay < __pytra_int(aa)) || (__step_2 < 0 && ay > __pytra_int(aa)); ay += __step_2 {
                __step_3 := __pytra_int(int64(1))
                for ax := __pytra_int(int64(0)); (__step_3 >= 0 && ax < __pytra_int(aa)) || (__step_3 < 0 && ax > __pytra_int(aa)); ax += __step_3 {
                    var fy float64 = __pytra_float((__pytra_float((__pytra_float(y) + __pytra_float((__pytra_float((__pytra_float(ay) + __pytra_float(float64(0.5)))) / __pytra_float(aa))))) / __pytra_float((__pytra_int(height) - __pytra_int(int64(1))))))
                    var fx float64 = __pytra_float((__pytra_float((__pytra_float(x) + __pytra_float((__pytra_float((__pytra_float(ax) + __pytra_float(float64(0.5)))) / __pytra_float(aa))))) / __pytra_float((__pytra_int(width) - __pytra_int(int64(1))))))
                    var sy float64 = __pytra_float((__pytra_float(float64(1.0)) - __pytra_float((__pytra_float(float64(2.0)) * __pytra_float(fy)))))
                    var sx float64 = __pytra_float((__pytra_float((__pytra_float((__pytra_float(float64(2.0)) * __pytra_float(fx))) - __pytra_float(float64(1.0)))) * __pytra_float((__pytra_float(width) / __pytra_float(height)))))
                    var dx float64 = __pytra_float(sx)
                    var dy float64 = __pytra_float(sy)
                    var dz float64 = __pytra_float(float64(1.0))
                    var inv_len float64 = __pytra_float((__pytra_float(float64(1.0)) / __pytra_float(math.Sqrt(__pytra_float((__pytra_float((__pytra_float((__pytra_float(dx) * __pytra_float(dx))) + __pytra_float((__pytra_float(dy) * __pytra_float(dy))))) + __pytra_float((__pytra_float(dz) * __pytra_float(dz)))))))))
                    dx *= inv_len
                    dy *= inv_len
                    dz *= inv_len
                    var t_min float64 = __pytra_float(float64(1e+30))
                    var hit_id int64 = __pytra_int((-int64(1)))
                    var t float64 = __pytra_float(hit_sphere(ox, oy, oz, dx, dy, dz, (-float64(0.8)), (-float64(0.2)), float64(2.2), float64(0.8)))
                    if ((__pytra_float(t) > __pytra_float(float64(0.0))) && (__pytra_float(t) < __pytra_float(t_min))) {
                        t_min = __pytra_float(t)
                        hit_id = __pytra_int(int64(0))
                    }
                    t = __pytra_float(hit_sphere(ox, oy, oz, dx, dy, dz, float64(0.9), float64(0.1), float64(2.9), float64(0.95)))
                    if ((__pytra_float(t) > __pytra_float(float64(0.0))) && (__pytra_float(t) < __pytra_float(t_min))) {
                        t_min = __pytra_float(t)
                        hit_id = __pytra_int(int64(1))
                    }
                    t = __pytra_float(hit_sphere(ox, oy, oz, dx, dy, dz, float64(0.0), (-float64(1001.0)), float64(3.0), float64(1000.0)))
                    if ((__pytra_float(t) > __pytra_float(float64(0.0))) && (__pytra_float(t) < __pytra_float(t_min))) {
                        t_min = __pytra_float(t)
                        hit_id = __pytra_int(int64(2))
                    }
                    var r int64 = __pytra_int(int64(0))
                    var g int64 = __pytra_int(int64(0))
                    var b int64 = __pytra_int(int64(0))
                    if (__pytra_int(hit_id) >= __pytra_int(int64(0))) {
                        var px float64 = __pytra_float((__pytra_float(ox) + __pytra_float((__pytra_float(dx) * __pytra_float(t_min)))))
                        var py float64 = __pytra_float((__pytra_float(oy) + __pytra_float((__pytra_float(dy) * __pytra_float(t_min)))))
                        var pz float64 = __pytra_float((__pytra_float(oz) + __pytra_float((__pytra_float(dz) * __pytra_float(t_min)))))
                        var nx float64 = __pytra_float(float64(0.0))
                        var ny float64 = __pytra_float(float64(0.0))
                        var nz float64 = __pytra_float(float64(0.0))
                        if (__pytra_int(hit_id) == __pytra_int(int64(0))) {
                            nx = __pytra_float((__pytra_float((__pytra_float(px) + __pytra_float(float64(0.8)))) / __pytra_float(float64(0.8))))
                            ny = __pytra_float((__pytra_float((__pytra_float(py) + __pytra_float(float64(0.2)))) / __pytra_float(float64(0.8))))
                            nz = __pytra_float((__pytra_float((__pytra_float(pz) - __pytra_float(float64(2.2)))) / __pytra_float(float64(0.8))))
                        } else {
                            if (__pytra_int(hit_id) == __pytra_int(int64(1))) {
                                nx = __pytra_float((__pytra_float((__pytra_float(px) - __pytra_float(float64(0.9)))) / __pytra_float(float64(0.95))))
                                ny = __pytra_float((__pytra_float((__pytra_float(py) - __pytra_float(float64(0.1)))) / __pytra_float(float64(0.95))))
                                nz = __pytra_float((__pytra_float((__pytra_float(pz) - __pytra_float(float64(2.9)))) / __pytra_float(float64(0.95))))
                            } else {
                                nx = __pytra_float(float64(0.0))
                                ny = __pytra_float(float64(1.0))
                                nz = __pytra_float(float64(0.0))
                            }
                        }
                        var diff float64 = __pytra_float((__pytra_float((__pytra_float((__pytra_float(nx) * __pytra_float((-lx)))) + __pytra_float((__pytra_float(ny) * __pytra_float((-ly)))))) + __pytra_float((__pytra_float(nz) * __pytra_float((-lz))))))
                        diff = __pytra_float(clamp01(diff))
                        var base_r float64 = __pytra_float(float64(0.0))
                        var base_g float64 = __pytra_float(float64(0.0))
                        var base_b float64 = __pytra_float(float64(0.0))
                        if (__pytra_int(hit_id) == __pytra_int(int64(0))) {
                            base_r = __pytra_float(float64(0.95))
                            base_g = __pytra_float(float64(0.35))
                            base_b = __pytra_float(float64(0.25))
                        } else {
                            if (__pytra_int(hit_id) == __pytra_int(int64(1))) {
                                base_r = __pytra_float(float64(0.25))
                                base_g = __pytra_float(float64(0.55))
                                base_b = __pytra_float(float64(0.95))
                            } else {
                                var checker int64 = __pytra_int((__pytra_int(__pytra_int((__pytra_float((__pytra_float(px) + __pytra_float(float64(50.0)))) * __pytra_float(float64(0.8))))) + __pytra_int(__pytra_int((__pytra_float((__pytra_float(pz) + __pytra_float(float64(50.0)))) * __pytra_float(float64(0.8)))))))
                                if (__pytra_int((__pytra_int(checker) % __pytra_int(int64(2)))) == __pytra_int(int64(0))) {
                                    base_r = __pytra_float(float64(0.85))
                                    base_g = __pytra_float(float64(0.85))
                                    base_b = __pytra_float(float64(0.85))
                                } else {
                                    base_r = __pytra_float(float64(0.2))
                                    base_g = __pytra_float(float64(0.2))
                                    base_b = __pytra_float(float64(0.2))
                                }
                            }
                        }
                        var shade float64 = __pytra_float((__pytra_float(float64(0.12)) + __pytra_float((__pytra_float(float64(0.88)) * __pytra_float(diff)))))
                        r = __pytra_int(__pytra_int((__pytra_float(float64(255.0)) * __pytra_float(clamp01((__pytra_float(base_r) * __pytra_float(shade)))))))
                        g = __pytra_int(__pytra_int((__pytra_float(float64(255.0)) * __pytra_float(clamp01((__pytra_float(base_g) * __pytra_float(shade)))))))
                        b = __pytra_int(__pytra_int((__pytra_float(float64(255.0)) * __pytra_float(clamp01((__pytra_float(base_b) * __pytra_float(shade)))))))
                    } else {
                        var tsky float64 = __pytra_float((__pytra_float(float64(0.5)) * __pytra_float((__pytra_float(dy) + __pytra_float(float64(1.0))))))
                        r = __pytra_int(__pytra_int((__pytra_float(float64(255.0)) * __pytra_float((__pytra_float(float64(0.65)) + __pytra_float((__pytra_float(float64(0.2)) * __pytra_float(tsky))))))))
                        g = __pytra_int(__pytra_int((__pytra_float(float64(255.0)) * __pytra_float((__pytra_float(float64(0.75)) + __pytra_float((__pytra_float(float64(0.18)) * __pytra_float(tsky))))))))
                        b = __pytra_int(__pytra_int((__pytra_float(float64(255.0)) * __pytra_float((__pytra_float(float64(0.9)) + __pytra_float((__pytra_float(float64(0.08)) * __pytra_float(tsky))))))))
                    }
                    ar += r
                    ag += g
                    ab += b
                }
            }
            var samples int64 = __pytra_int((__pytra_int(aa) * __pytra_int(aa)))
            pixels = append(__pytra_as_list(pixels), (__pytra_int(__pytra_int(ar) / __pytra_int(samples))))
            pixels = append(__pytra_as_list(pixels), (__pytra_int(__pytra_int(ag) / __pytra_int(samples))))
            pixels = append(__pytra_as_list(pixels), (__pytra_int(__pytra_int(ab) / __pytra_int(samples))))
        }
    }
    return pixels
}

func run_raytrace() {
    var width int64 = __pytra_int(int64(1600))
    var height int64 = __pytra_int(int64(900))
    var aa int64 = __pytra_int(int64(2))
    var out_path string = __pytra_str("sample/out/02_raytrace_spheres.png")
    var start float64 = __pytra_float(__pytra_perf_counter())
    var pixels []any = __pytra_as_list(render(width, height, aa))
    __pytra_noop(out_path, width, height, pixels)
    var elapsed float64 = __pytra_float((__pytra_perf_counter() - start))
    __pytra_print("output:", out_path)
    __pytra_print("size:", width, "x", height)
    __pytra_print("elapsed_sec:", elapsed)
}

func main() {
    run_raytrace()
}
