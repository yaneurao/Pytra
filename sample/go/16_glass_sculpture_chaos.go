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

func dot(ax float64, ay float64, az float64, bx float64, by float64, bz float64) float64 {
    return (__pytra_float((__pytra_float((__pytra_float(ax) * __pytra_float(bx))) + __pytra_float((__pytra_float(ay) * __pytra_float(by))))) + __pytra_float((__pytra_float(az) * __pytra_float(bz))))
}

func length(x float64, y float64, z float64) float64 {
    return math.Sqrt(__pytra_float((__pytra_float((__pytra_float((__pytra_float(x) * __pytra_float(x))) + __pytra_float((__pytra_float(y) * __pytra_float(y))))) + __pytra_float((__pytra_float(z) * __pytra_float(z))))))
}

func normalize(x float64, y float64, z float64) []any {
    var l float64 = __pytra_float(length(x, y, z))
    if (__pytra_float(l) < __pytra_float(float64(1e-09))) {
        return []any{float64(0.0), float64(0.0), float64(0.0)}
    }
    return []any{(__pytra_float(x) / __pytra_float(l)), (__pytra_float(y) / __pytra_float(l)), (__pytra_float(z) / __pytra_float(l))}
}

func reflect(ix float64, iy float64, iz float64, nx float64, ny float64, nz float64) []any {
    var d float64 = __pytra_float((__pytra_float(dot(ix, iy, iz, nx, ny, nz)) * __pytra_float(float64(2.0))))
    return []any{(__pytra_float(ix) - __pytra_float((__pytra_float(d) * __pytra_float(nx)))), (__pytra_float(iy) - __pytra_float((__pytra_float(d) * __pytra_float(ny)))), (__pytra_float(iz) - __pytra_float((__pytra_float(d) * __pytra_float(nz))))}
}

func refract(ix float64, iy float64, iz float64, nx float64, ny float64, nz float64, eta float64) []any {
    var cosi float64 = __pytra_float((-dot(ix, iy, iz, nx, ny, nz)))
    var sint2 float64 = __pytra_float((__pytra_float((__pytra_float(eta) * __pytra_float(eta))) * __pytra_float((__pytra_float(float64(1.0)) - __pytra_float((__pytra_float(cosi) * __pytra_float(cosi)))))))
    if (__pytra_float(sint2) > __pytra_float(float64(1.0))) {
        return reflect(ix, iy, iz, nx, ny, nz)
    }
    var cost any = math.Sqrt(__pytra_float((__pytra_float(float64(1.0)) - __pytra_float(sint2))))
    var k float64 = __pytra_float(((__pytra_float(eta) * __pytra_float(cosi)) - cost))
    return []any{((__pytra_float(eta) * __pytra_float(ix)) + (k * nx)), ((__pytra_float(eta) * __pytra_float(iy)) + (k * ny)), ((__pytra_float(eta) * __pytra_float(iz)) + (k * nz))}
}

func schlick(cos_theta float64, f0 float64) float64 {
    var m float64 = __pytra_float((__pytra_float(float64(1.0)) - __pytra_float(cos_theta)))
    return (__pytra_float(f0) + __pytra_float((__pytra_float((__pytra_float(float64(1.0)) - __pytra_float(f0))) * __pytra_float((__pytra_float((__pytra_float((__pytra_float((__pytra_float(m) * __pytra_float(m))) * __pytra_float(m))) * __pytra_float(m))) * __pytra_float(m))))))
}

func sky_color(dx float64, dy float64, dz float64, tphase float64) []any {
    var t float64 = __pytra_float((__pytra_float(float64(0.5)) * __pytra_float((__pytra_float(dy) + __pytra_float(float64(1.0))))))
    var r float64 = __pytra_float((__pytra_float(float64(0.06)) + __pytra_float((__pytra_float(float64(0.2)) * __pytra_float(t)))))
    var g float64 = __pytra_float((__pytra_float(float64(0.1)) + __pytra_float((__pytra_float(float64(0.25)) * __pytra_float(t)))))
    var b float64 = __pytra_float((__pytra_float(float64(0.16)) + __pytra_float((__pytra_float(float64(0.45)) * __pytra_float(t)))))
    var band float64 = __pytra_float((float64(0.5) + (float64(0.5) * math.Sin(__pytra_float((__pytra_float((__pytra_float((__pytra_float(float64(8.0)) * __pytra_float(dx))) + __pytra_float((__pytra_float(float64(6.0)) * __pytra_float(dz))))) + __pytra_float(tphase)))))))
    r += (float64(0.08) * band)
    g += (float64(0.05) * band)
    b += (float64(0.12) * band)
    return []any{clamp01(r), clamp01(g), clamp01(b)}
}

func sphere_intersect(ox float64, oy float64, oz float64, dx float64, dy float64, dz float64, cx float64, cy float64, cz float64, radius float64) float64 {
    var lx float64 = __pytra_float((__pytra_float(ox) - __pytra_float(cx)))
    var ly float64 = __pytra_float((__pytra_float(oy) - __pytra_float(cy)))
    var lz float64 = __pytra_float((__pytra_float(oz) - __pytra_float(cz)))
    var b float64 = __pytra_float((__pytra_float((__pytra_float((__pytra_float(lx) * __pytra_float(dx))) + __pytra_float((__pytra_float(ly) * __pytra_float(dy))))) + __pytra_float((__pytra_float(lz) * __pytra_float(dz)))))
    var c float64 = __pytra_float((__pytra_float((__pytra_float((__pytra_float((__pytra_float(lx) * __pytra_float(lx))) + __pytra_float((__pytra_float(ly) * __pytra_float(ly))))) + __pytra_float((__pytra_float(lz) * __pytra_float(lz))))) - __pytra_float((__pytra_float(radius) * __pytra_float(radius)))))
    var h float64 = __pytra_float((__pytra_float((__pytra_float(b) * __pytra_float(b))) - __pytra_float(c)))
    if (__pytra_float(h) < __pytra_float(float64(0.0))) {
        return (-float64(1.0))
    }
    var s any = math.Sqrt(__pytra_float(h))
    var t0 float64 = __pytra_float(((-b) - s))
    if (__pytra_float(t0) > __pytra_float(float64(0.0001))) {
        return t0
    }
    var t1 float64 = __pytra_float(((-b) + s))
    if (__pytra_float(t1) > __pytra_float(float64(0.0001))) {
        return t1
    }
    return (-float64(1.0))
}

func palette_332() []any {
    var p []any = __pytra_as_list(__pytra_bytearray((__pytra_int(int64(256)) * __pytra_int(int64(3)))))
    __step_0 := __pytra_int(int64(1))
    for i := __pytra_int(int64(0)); (__step_0 >= 0 && i < __pytra_int(int64(256))) || (__step_0 < 0 && i > __pytra_int(int64(256))); i += __step_0 {
        var r int64 = __pytra_int((__pytra_int((__pytra_int(i) + __pytra_int(int64(5)))) + __pytra_int(int64(7))))
        var g int64 = __pytra_int((__pytra_int((__pytra_int(i) + __pytra_int(int64(2)))) + __pytra_int(int64(7))))
        var b int64 = __pytra_int((__pytra_int(i) + __pytra_int(int64(3))))
        __pytra_set_index(p, (__pytra_int((__pytra_int(i) * __pytra_int(int64(3)))) + __pytra_int(int64(0))), __pytra_int((__pytra_float((__pytra_int(int64(255)) * __pytra_int(r))) / __pytra_float(int64(7)))))
        __pytra_set_index(p, (__pytra_int((__pytra_int(i) * __pytra_int(int64(3)))) + __pytra_int(int64(1))), __pytra_int((__pytra_float((__pytra_int(int64(255)) * __pytra_int(g))) / __pytra_float(int64(7)))))
        __pytra_set_index(p, (__pytra_int((__pytra_int(i) * __pytra_int(int64(3)))) + __pytra_int(int64(2))), __pytra_int((__pytra_float((__pytra_int(int64(255)) * __pytra_int(b))) / __pytra_float(int64(3)))))
    }
    return __pytra_bytes(p)
}

func quantize_332(r float64, g float64, b float64) int64 {
    var rr int64 = __pytra_int(__pytra_int((__pytra_float(clamp01(r)) * __pytra_float(float64(255.0)))))
    var gg int64 = __pytra_int(__pytra_int((__pytra_float(clamp01(g)) * __pytra_float(float64(255.0)))))
    var bb int64 = __pytra_int(__pytra_int((__pytra_float(clamp01(b)) * __pytra_float(float64(255.0)))))
    return (__pytra_int((__pytra_int((__pytra_int((__pytra_int(rr) + __pytra_int(int64(5)))) + __pytra_int(int64(5)))) + __pytra_int((__pytra_int((__pytra_int(gg) + __pytra_int(int64(5)))) + __pytra_int(int64(2)))))) + __pytra_int((__pytra_int(bb) + __pytra_int(int64(6)))))
}

func render_frame(width int64, height int64, frame_id int64, frames_n int64) []any {
    var t float64 = __pytra_float((__pytra_float(frame_id) / __pytra_float(frames_n)))
    var tphase float64 = __pytra_float(((float64(2.0) * math.Pi) * t))
    var cam_r float64 = __pytra_float(float64(3.0))
    var cam_x float64 = __pytra_float((cam_r * math.Cos(__pytra_float((tphase * float64(0.9))))))
    var cam_y float64 = __pytra_float((float64(1.1) + (float64(0.25) * math.Sin(__pytra_float((tphase * float64(0.6)))))))
    var cam_z float64 = __pytra_float((cam_r * math.Sin(__pytra_float((tphase * float64(0.9))))))
    var look_x float64 = __pytra_float(float64(0.0))
    var look_y float64 = __pytra_float(float64(0.35))
    var look_z float64 = __pytra_float(float64(0.0))
    __tuple_0 := __pytra_as_list(normalize((look_x - cam_x), (look_y - cam_y), (look_z - cam_z)))
    var fwd_x float64 = __pytra_float(__tuple_0[0])
    var fwd_y float64 = __pytra_float(__tuple_0[1])
    var fwd_z float64 = __pytra_float(__tuple_0[2])
    __tuple_1 := __pytra_as_list(normalize(fwd_z, float64(0.0), (-fwd_x)))
    var right_x float64 = __pytra_float(__tuple_1[0])
    var right_y float64 = __pytra_float(__tuple_1[1])
    var right_z float64 = __pytra_float(__tuple_1[2])
    __tuple_2 := __pytra_as_list(normalize(((right_y * fwd_z) - (right_z * fwd_y)), ((right_z * fwd_x) - (right_x * fwd_z)), ((right_x * fwd_y) - (right_y * fwd_x))))
    var up_x float64 = __pytra_float(__tuple_2[0])
    var up_y float64 = __pytra_float(__tuple_2[1])
    var up_z float64 = __pytra_float(__tuple_2[2])
    var s0x float64 = __pytra_float((float64(0.9) * math.Cos(__pytra_float((float64(1.3) * tphase)))))
    var s0y float64 = __pytra_float((float64(0.15) + (float64(0.35) * math.Sin(__pytra_float((float64(1.7) * tphase))))))
    var s0z float64 = __pytra_float((float64(0.9) * math.Sin(__pytra_float((float64(1.3) * tphase)))))
    var s1x float64 = __pytra_float((float64(1.2) * math.Cos(__pytra_float(((float64(1.3) * tphase) + float64(2.094))))))
    var s1y float64 = __pytra_float((float64(0.1) + (float64(0.4) * math.Sin(__pytra_float(((float64(1.1) * tphase) + float64(0.8)))))))
    var s1z float64 = __pytra_float((float64(1.2) * math.Sin(__pytra_float(((float64(1.3) * tphase) + float64(2.094))))))
    var s2x float64 = __pytra_float((float64(1.0) * math.Cos(__pytra_float(((float64(1.3) * tphase) + float64(4.188))))))
    var s2y float64 = __pytra_float((float64(0.2) + (float64(0.3) * math.Sin(__pytra_float(((float64(1.5) * tphase) + float64(1.9)))))))
    var s2z float64 = __pytra_float((float64(1.0) * math.Sin(__pytra_float(((float64(1.3) * tphase) + float64(4.188))))))
    var lr float64 = __pytra_float(float64(0.35))
    var lx float64 = __pytra_float((float64(2.4) * math.Cos(__pytra_float((tphase * float64(1.8))))))
    var ly float64 = __pytra_float((float64(1.8) + (float64(0.8) * math.Sin(__pytra_float((tphase * float64(1.2)))))))
    var lz float64 = __pytra_float((float64(2.4) * math.Sin(__pytra_float((tphase * float64(1.8))))))
    var frame []any = __pytra_as_list(__pytra_bytearray((__pytra_int(width) * __pytra_int(height))))
    var aspect float64 = __pytra_float((__pytra_float(width) / __pytra_float(height)))
    var fov float64 = __pytra_float(float64(1.25))
    __step_3 := __pytra_int(int64(1))
    for py := __pytra_int(int64(0)); (__step_3 >= 0 && py < __pytra_int(height)) || (__step_3 < 0 && py > __pytra_int(height)); py += __step_3 {
        var row_base int64 = __pytra_int((__pytra_int(py) * __pytra_int(width)))
        var sy float64 = __pytra_float((__pytra_float(float64(1.0)) - __pytra_float((__pytra_float((__pytra_float(float64(2.0)) * __pytra_float((__pytra_float(py) + __pytra_float(float64(0.5)))))) / __pytra_float(height)))))
        __step_4 := __pytra_int(int64(1))
        for px := __pytra_int(int64(0)); (__step_4 >= 0 && px < __pytra_int(width)) || (__step_4 < 0 && px > __pytra_int(width)); px += __step_4 {
            var sx float64 = __pytra_float((__pytra_float((__pytra_float((__pytra_float((__pytra_float(float64(2.0)) * __pytra_float((__pytra_float(px) + __pytra_float(float64(0.5)))))) / __pytra_float(width))) - __pytra_float(float64(1.0)))) * __pytra_float(aspect)))
            var rx float64 = __pytra_float((fwd_x + (fov * ((sx * right_x) + (sy * up_x)))))
            var ry float64 = __pytra_float((fwd_y + (fov * ((sx * right_y) + (sy * up_y)))))
            var rz float64 = __pytra_float((fwd_z + (fov * ((sx * right_z) + (sy * up_z)))))
            __tuple_5 := __pytra_as_list(normalize(rx, ry, rz))
            var dx float64 = __pytra_float(__tuple_5[0])
            var dy float64 = __pytra_float(__tuple_5[1])
            var dz float64 = __pytra_float(__tuple_5[2])
            var best_t float64 = __pytra_float(float64(1000000000.0))
            var hit_kind int64 = __pytra_int(int64(0))
            var r float64 = __pytra_float(float64(0.0))
            var g float64 = __pytra_float(float64(0.0))
            var b float64 = __pytra_float(float64(0.0))
            if (__pytra_float(dy) < __pytra_float((-float64(1e-06)))) {
                var tf float64 = __pytra_float((__pytra_float(((-float64(1.2)) - cam_y)) / __pytra_float(dy)))
                if ((__pytra_float(tf) > __pytra_float(float64(0.0001))) && (__pytra_float(tf) < __pytra_float(best_t))) {
                    best_t = __pytra_float(tf)
                    hit_kind = __pytra_int(int64(1))
                }
            }
            var t0 float64 = __pytra_float(sphere_intersect(cam_x, cam_y, cam_z, dx, dy, dz, s0x, s0y, s0z, float64(0.65)))
            if ((__pytra_float(t0) > __pytra_float(float64(0.0))) && (__pytra_float(t0) < __pytra_float(best_t))) {
                best_t = __pytra_float(t0)
                hit_kind = __pytra_int(int64(2))
            }
            var t1 float64 = __pytra_float(sphere_intersect(cam_x, cam_y, cam_z, dx, dy, dz, s1x, s1y, s1z, float64(0.72)))
            if ((__pytra_float(t1) > __pytra_float(float64(0.0))) && (__pytra_float(t1) < __pytra_float(best_t))) {
                best_t = __pytra_float(t1)
                hit_kind = __pytra_int(int64(3))
            }
            var t2 float64 = __pytra_float(sphere_intersect(cam_x, cam_y, cam_z, dx, dy, dz, s2x, s2y, s2z, float64(0.58)))
            if ((__pytra_float(t2) > __pytra_float(float64(0.0))) && (__pytra_float(t2) < __pytra_float(best_t))) {
                best_t = __pytra_float(t2)
                hit_kind = __pytra_int(int64(4))
            }
            if (__pytra_int(hit_kind) == __pytra_int(int64(0))) {
                __tuple_6 := __pytra_as_list(sky_color(dx, dy, dz, tphase))
                r = __pytra_float(__tuple_6[0])
                g = __pytra_float(__tuple_6[1])
                b = __pytra_float(__tuple_6[2])
            } else {
                if (__pytra_int(hit_kind) == __pytra_int(int64(1))) {
                    var hx float64 = __pytra_float((cam_x + (best_t * dx)))
                    var hz float64 = __pytra_float((cam_z + (best_t * dz)))
                    var cx int64 = __pytra_int(__pytra_int(math.floor(__pytra_float((hx * float64(2.0))))))
                    var cz int64 = __pytra_int(__pytra_int(math.floor(__pytra_float((hz * float64(2.0))))))
                    var checker int64 = __pytra_int(__pytra_ifexp((__pytra_int((__pytra_int((__pytra_int(cx) + __pytra_int(cz))) % __pytra_int(int64(2)))) == __pytra_int(int64(0))), int64(0), int64(1)))
                    var base_r float64 = __pytra_float(__pytra_ifexp((__pytra_int(checker) == __pytra_int(int64(0))), float64(0.1), float64(0.04)))
                    var base_g float64 = __pytra_float(__pytra_ifexp((__pytra_int(checker) == __pytra_int(int64(0))), float64(0.11), float64(0.05)))
                    var base_b float64 = __pytra_float(__pytra_ifexp((__pytra_int(checker) == __pytra_int(int64(0))), float64(0.13), float64(0.08)))
                    var lxv float64 = __pytra_float((lx - hx))
                    var lyv float64 = __pytra_float((ly - (-float64(1.2))))
                    var lzv float64 = __pytra_float((lz - hz))
                    __tuple_7 := __pytra_as_list(normalize(lxv, lyv, lzv))
                    var ldx float64 = __pytra_float(__tuple_7[0])
                    var ldy float64 = __pytra_float(__tuple_7[1])
                    var ldz float64 = __pytra_float(__tuple_7[2])
                    var ndotl int64 = __pytra_int(__pytra_max(ldy, float64(0.0)))
                    var ldist2 float64 = __pytra_float((((lxv * lxv) + (lyv * lyv)) + (lzv * lzv)))
                    var glow float64 = __pytra_float((__pytra_float(float64(8.0)) / __pytra_float((float64(1.0) + ldist2))))
                    r = __pytra_float(((base_r + (float64(0.8) * glow)) + (float64(0.2) * ndotl)))
                    g = __pytra_float(((base_g + (float64(0.5) * glow)) + (float64(0.18) * ndotl)))
                    b = __pytra_float(((base_b + (float64(1.0) * glow)) + (float64(0.24) * ndotl)))
                } else {
                    var cx float64 = __pytra_float(float64(0.0))
                    var cy float64 = __pytra_float(float64(0.0))
                    var cz float64 = __pytra_float(float64(0.0))
                    var rad float64 = __pytra_float(float64(1.0))
                    if (__pytra_int(hit_kind) == __pytra_int(int64(2))) {
                        cx = __pytra_float(s0x)
                        cy = __pytra_float(s0y)
                        cz = __pytra_float(s0z)
                        rad = __pytra_float(float64(0.65))
                    } else {
                        if (__pytra_int(hit_kind) == __pytra_int(int64(3))) {
                            cx = __pytra_float(s1x)
                            cy = __pytra_float(s1y)
                            cz = __pytra_float(s1z)
                            rad = __pytra_float(float64(0.72))
                        } else {
                            cx = __pytra_float(s2x)
                            cy = __pytra_float(s2y)
                            cz = __pytra_float(s2z)
                            rad = __pytra_float(float64(0.58))
                        }
                    }
                    var hx float64 = __pytra_float((cam_x + (best_t * dx)))
                    var hy float64 = __pytra_float((cam_y + (best_t * dy)))
                    var hz float64 = __pytra_float((cam_z + (best_t * dz)))
                    __tuple_8 := __pytra_as_list(normalize((__pytra_float((hx - cx)) / __pytra_float(rad)), (__pytra_float((hy - cy)) / __pytra_float(rad)), (__pytra_float((hz - cz)) / __pytra_float(rad))))
                    var nx float64 = __pytra_float(__tuple_8[0])
                    var ny float64 = __pytra_float(__tuple_8[1])
                    var nz float64 = __pytra_float(__tuple_8[2])
                    __tuple_9 := __pytra_as_list(reflect(dx, dy, dz, nx, ny, nz))
                    var rdx float64 = __pytra_float(__tuple_9[0])
                    var rdy float64 = __pytra_float(__tuple_9[1])
                    var rdz float64 = __pytra_float(__tuple_9[2])
                    __tuple_10 := __pytra_as_list(refract(dx, dy, dz, nx, ny, nz, (__pytra_float(float64(1.0)) / __pytra_float(float64(1.45)))))
                    var tdx float64 = __pytra_float(__tuple_10[0])
                    var tdy float64 = __pytra_float(__tuple_10[1])
                    var tdz float64 = __pytra_float(__tuple_10[2])
                    __tuple_11 := __pytra_as_list(sky_color(rdx, rdy, rdz, tphase))
                    var sr float64 = __pytra_float(__tuple_11[0])
                    var sg float64 = __pytra_float(__tuple_11[1])
                    var sb float64 = __pytra_float(__tuple_11[2])
                    __tuple_12 := __pytra_as_list(sky_color(tdx, tdy, tdz, (tphase + float64(0.8))))
                    var tr float64 = __pytra_float(__tuple_12[0])
                    var tg float64 = __pytra_float(__tuple_12[1])
                    var tb float64 = __pytra_float(__tuple_12[2])
                    var cosi int64 = __pytra_int(__pytra_max((-(((dx * nx) + (dy * ny)) + (dz * nz))), float64(0.0)))
                    var fr float64 = __pytra_float(schlick(cosi, float64(0.04)))
                    r = __pytra_float(((tr * (__pytra_float(float64(1.0)) - __pytra_float(fr))) + (sr * fr)))
                    g = __pytra_float(((tg * (__pytra_float(float64(1.0)) - __pytra_float(fr))) + (sg * fr)))
                    b = __pytra_float(((tb * (__pytra_float(float64(1.0)) - __pytra_float(fr))) + (sb * fr)))
                    var lxv float64 = __pytra_float((lx - hx))
                    var lyv float64 = __pytra_float((ly - hy))
                    var lzv float64 = __pytra_float((lz - hz))
                    __tuple_13 := __pytra_as_list(normalize(lxv, lyv, lzv))
                    var ldx float64 = __pytra_float(__tuple_13[0])
                    var ldy float64 = __pytra_float(__tuple_13[1])
                    var ldz float64 = __pytra_float(__tuple_13[2])
                    var ndotl int64 = __pytra_int(__pytra_max((((nx * ldx) + (ny * ldy)) + (nz * ldz)), float64(0.0)))
                    __tuple_14 := __pytra_as_list(normalize((ldx - dx), (ldy - dy), (ldz - dz)))
                    var hvx float64 = __pytra_float(__tuple_14[0])
                    var hvy float64 = __pytra_float(__tuple_14[1])
                    var hvz float64 = __pytra_float(__tuple_14[2])
                    var ndoth int64 = __pytra_int(__pytra_max((((nx * hvx) + (ny * hvy)) + (nz * hvz)), float64(0.0)))
                    var spec int64 = __pytra_int((ndoth * ndoth))
                    spec = __pytra_int((spec * spec))
                    spec = __pytra_int((spec * spec))
                    spec = __pytra_int((spec * spec))
                    var glow float64 = __pytra_float((__pytra_float(float64(10.0)) / __pytra_float((((float64(1.0) + (lxv * lxv)) + (lyv * lyv)) + (lzv * lzv)))))
                    r += (((float64(0.2) * ndotl) + (float64(0.8) * spec)) + (float64(0.45) * glow))
                    g += (((float64(0.18) * ndotl) + (float64(0.6) * spec)) + (float64(0.35) * glow))
                    b += (((float64(0.26) * ndotl) + (float64(1.0) * spec)) + (float64(0.65) * glow))
                    if (__pytra_int(hit_kind) == __pytra_int(int64(2))) {
                        r *= float64(0.95)
                        g *= float64(1.05)
                        b *= float64(1.1)
                    } else {
                        if (__pytra_int(hit_kind) == __pytra_int(int64(3))) {
                            r *= float64(1.08)
                            g *= float64(0.98)
                            b *= float64(1.04)
                        } else {
                            r *= float64(1.02)
                            g *= float64(1.1)
                            b *= float64(0.95)
                        }
                    }
                }
            }
            r = __pytra_float(math.Sqrt(__pytra_float(clamp01(r))))
            g = __pytra_float(math.Sqrt(__pytra_float(clamp01(g))))
            b = __pytra_float(math.Sqrt(__pytra_float(clamp01(b))))
            __pytra_set_index(frame, (__pytra_int(row_base) + __pytra_int(px)), quantize_332(r, g, b))
        }
    }
    return __pytra_bytes(frame)
}

func run_16_glass_sculpture_chaos() {
    var width int64 = __pytra_int(int64(320))
    var height int64 = __pytra_int(int64(240))
    var frames_n int64 = __pytra_int(int64(72))
    var out_path string = __pytra_str("sample/out/16_glass_sculpture_chaos.gif")
    var start float64 = __pytra_float(__pytra_perf_counter())
    var frames []any = __pytra_as_list([]any{})
    __step_0 := __pytra_int(int64(1))
    for i := __pytra_int(int64(0)); (__step_0 >= 0 && i < __pytra_int(frames_n)) || (__step_0 < 0 && i > __pytra_int(frames_n)); i += __step_0 {
        frames = append(__pytra_as_list(frames), render_frame(width, height, i, frames_n))
    }
    __pytra_noop(out_path, width, height, frames, palette_332())
    var elapsed float64 = __pytra_float((__pytra_perf_counter() - start))
    __pytra_print("output:", out_path)
    __pytra_print("frames:", frames_n)
    __pytra_print("elapsed_sec:", elapsed)
}

func main() {
    run_16_glass_sculpture_chaos()
}
