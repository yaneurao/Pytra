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

func next_state(grid []any, w int64, h int64) []any {
    var nxt []any = __pytra_as_list([]any{})
    __step_0 := __pytra_int(int64(1))
    for y := __pytra_int(int64(0)); (__step_0 >= 0 && y < __pytra_int(h)) || (__step_0 < 0 && y > __pytra_int(h)); y += __step_0 {
        var row []any = __pytra_as_list([]any{})
        __step_1 := __pytra_int(int64(1))
        for x := __pytra_int(int64(0)); (__step_1 >= 0 && x < __pytra_int(w)) || (__step_1 < 0 && x > __pytra_int(w)); x += __step_1 {
            var cnt int64 = __pytra_int(int64(0))
            __step_2 := __pytra_int(int64(1))
            for dy := __pytra_int((-int64(1))); (__step_2 >= 0 && dy < __pytra_int(int64(2))) || (__step_2 < 0 && dy > __pytra_int(int64(2))); dy += __step_2 {
                __step_3 := __pytra_int(int64(1))
                for dx := __pytra_int((-int64(1))); (__step_3 >= 0 && dx < __pytra_int(int64(2))) || (__step_3 < 0 && dx > __pytra_int(int64(2))); dx += __step_3 {
                    if ((__pytra_int(dx) != __pytra_int(int64(0))) || (__pytra_int(dy) != __pytra_int(int64(0)))) {
                        var nx int64 = __pytra_int((__pytra_int((__pytra_int((__pytra_int(x) + __pytra_int(dx))) + __pytra_int(w))) % __pytra_int(w)))
                        var ny int64 = __pytra_int((__pytra_int((__pytra_int((__pytra_int(y) + __pytra_int(dy))) + __pytra_int(h))) % __pytra_int(h)))
                        cnt += __pytra_int(__pytra_get_index(__pytra_as_list(__pytra_get_index(grid, ny)), nx))
                    }
                }
            }
            var alive int64 = __pytra_int(__pytra_int(__pytra_get_index(__pytra_as_list(__pytra_get_index(grid, y)), x)))
            if ((__pytra_int(alive) == __pytra_int(int64(1))) && ((__pytra_int(cnt) == __pytra_int(int64(2))) || (__pytra_int(cnt) == __pytra_int(int64(3))))) {
                row = append(__pytra_as_list(row), int64(1))
            } else {
                if ((__pytra_int(alive) == __pytra_int(int64(0))) && (__pytra_int(cnt) == __pytra_int(int64(3)))) {
                    row = append(__pytra_as_list(row), int64(1))
                } else {
                    row = append(__pytra_as_list(row), int64(0))
                }
            }
        }
        nxt = append(__pytra_as_list(nxt), row)
    }
    return nxt
}

func render(grid []any, w int64, h int64, cell int64) []any {
    var width int64 = __pytra_int((__pytra_int(w) * __pytra_int(cell)))
    var height int64 = __pytra_int((__pytra_int(h) * __pytra_int(cell)))
    var frame []any = __pytra_as_list(__pytra_bytearray((__pytra_int(width) * __pytra_int(height))))
    __step_0 := __pytra_int(int64(1))
    for y := __pytra_int(int64(0)); (__step_0 >= 0 && y < __pytra_int(h)) || (__step_0 < 0 && y > __pytra_int(h)); y += __step_0 {
        __step_1 := __pytra_int(int64(1))
        for x := __pytra_int(int64(0)); (__step_1 >= 0 && x < __pytra_int(w)) || (__step_1 < 0 && x > __pytra_int(w)); x += __step_1 {
            var v int64 = __pytra_int(__pytra_ifexp((__pytra_int(__pytra_get_index(__pytra_as_list(__pytra_get_index(grid, y)), x)) != 0), int64(255), int64(0)))
            __step_2 := __pytra_int(int64(1))
            for yy := __pytra_int(int64(0)); (__step_2 >= 0 && yy < __pytra_int(cell)) || (__step_2 < 0 && yy > __pytra_int(cell)); yy += __step_2 {
                var base int64 = __pytra_int((__pytra_int((__pytra_int((__pytra_int((__pytra_int(y) * __pytra_int(cell))) + __pytra_int(yy))) * __pytra_int(width))) + __pytra_int((__pytra_int(x) * __pytra_int(cell)))))
                __step_3 := __pytra_int(int64(1))
                for xx := __pytra_int(int64(0)); (__step_3 >= 0 && xx < __pytra_int(cell)) || (__step_3 < 0 && xx > __pytra_int(cell)); xx += __step_3 {
                    __pytra_set_index(frame, (__pytra_int(base) + __pytra_int(xx)), v)
                }
            }
        }
    }
    return __pytra_bytes(frame)
}

func run_07_game_of_life_loop() {
    var w int64 = __pytra_int(int64(144))
    var h int64 = __pytra_int(int64(108))
    var cell int64 = __pytra_int(int64(4))
    var steps int64 = __pytra_int(int64(105))
    var out_path string = __pytra_str("sample/out/07_game_of_life_loop.gif")
    var start float64 = __pytra_float(__pytra_perf_counter())
    var grid []any = __pytra_as_list(func() []any { __out := []any{}; __step := __pytra_int(int64(1)); for __lc_i := __pytra_int(int64(0)); (__step >= 0 && __lc_i < __pytra_int(h)) || (__step < 0 && __lc_i > __pytra_int(h)); __lc_i += __step { __out = append(__out, __pytra_list_repeat(int64(0), w)) }; return __out }())
    __step_0 := __pytra_int(int64(1))
    for y := __pytra_int(int64(0)); (__step_0 >= 0 && y < __pytra_int(h)) || (__step_0 < 0 && y > __pytra_int(h)); y += __step_0 {
        __step_1 := __pytra_int(int64(1))
        for x := __pytra_int(int64(0)); (__step_1 >= 0 && x < __pytra_int(w)) || (__step_1 < 0 && x > __pytra_int(w)); x += __step_1 {
            var noise int64 = __pytra_int((__pytra_int((__pytra_int((__pytra_int((__pytra_int((__pytra_int(x) * __pytra_int(int64(37)))) + __pytra_int((__pytra_int(y) * __pytra_int(int64(73)))))) + __pytra_int((__pytra_int((__pytra_int(x) * __pytra_int(y))) % __pytra_int(int64(19)))))) + __pytra_int((__pytra_int((__pytra_int(x) + __pytra_int(y))) % __pytra_int(int64(11)))))) % __pytra_int(int64(97))))
            if (__pytra_int(noise) < __pytra_int(int64(3))) {
                __pytra_set_index(__pytra_as_list(__pytra_get_index(grid, y)), x, int64(1))
            }
        }
    }
    var glider []any = __pytra_as_list([]any{[]any{int64(0), int64(1), int64(0)}, []any{int64(0), int64(0), int64(1)}, []any{int64(1), int64(1), int64(1)}})
    var r_pentomino []any = __pytra_as_list([]any{[]any{int64(0), int64(1), int64(1)}, []any{int64(1), int64(1), int64(0)}, []any{int64(0), int64(1), int64(0)}})
    var lwss []any = __pytra_as_list([]any{[]any{int64(0), int64(1), int64(1), int64(1), int64(1)}, []any{int64(1), int64(0), int64(0), int64(0), int64(1)}, []any{int64(0), int64(0), int64(0), int64(0), int64(1)}, []any{int64(1), int64(0), int64(0), int64(1), int64(0)}})
    __step_2 := __pytra_int(int64(18))
    for gy := __pytra_int(int64(8)); (__step_2 >= 0 && gy < __pytra_int((__pytra_int(h) - __pytra_int(int64(8))))) || (__step_2 < 0 && gy > __pytra_int((__pytra_int(h) - __pytra_int(int64(8))))); gy += __step_2 {
        __step_3 := __pytra_int(int64(22))
        for gx := __pytra_int(int64(8)); (__step_3 >= 0 && gx < __pytra_int((__pytra_int(w) - __pytra_int(int64(8))))) || (__step_3 < 0 && gx > __pytra_int((__pytra_int(w) - __pytra_int(int64(8))))); gx += __step_3 {
            var kind int64 = __pytra_int((__pytra_int((__pytra_int((__pytra_int(gx) * __pytra_int(int64(7)))) + __pytra_int((__pytra_int(gy) * __pytra_int(int64(11)))))) % __pytra_int(int64(3))))
            if (__pytra_int(kind) == __pytra_int(int64(0))) {
                var ph int64 = __pytra_int(__pytra_len(glider))
                __step_4 := __pytra_int(int64(1))
                for py := __pytra_int(int64(0)); (__step_4 >= 0 && py < __pytra_int(ph)) || (__step_4 < 0 && py > __pytra_int(ph)); py += __step_4 {
                    var pw int64 = __pytra_int(__pytra_len(__pytra_as_list(__pytra_get_index(glider, py))))
                    __step_5 := __pytra_int(int64(1))
                    for px := __pytra_int(int64(0)); (__step_5 >= 0 && px < __pytra_int(pw)) || (__step_5 < 0 && px > __pytra_int(pw)); px += __step_5 {
                        if (__pytra_int(__pytra_int(__pytra_get_index(__pytra_as_list(__pytra_get_index(glider, py)), px))) == __pytra_int(int64(1))) {
                            __pytra_set_index(__pytra_as_list(__pytra_get_index(grid, (__pytra_int((__pytra_int(gy) + __pytra_int(py))) % __pytra_int(h)))), (__pytra_int((__pytra_int(gx) + __pytra_int(px))) % __pytra_int(w)), int64(1))
                        }
                    }
                }
            } else {
                if (__pytra_int(kind) == __pytra_int(int64(1))) {
                    var ph int64 = __pytra_int(__pytra_len(r_pentomino))
                    __step_6 := __pytra_int(int64(1))
                    for py := __pytra_int(int64(0)); (__step_6 >= 0 && py < __pytra_int(ph)) || (__step_6 < 0 && py > __pytra_int(ph)); py += __step_6 {
                        var pw int64 = __pytra_int(__pytra_len(__pytra_as_list(__pytra_get_index(r_pentomino, py))))
                        __step_7 := __pytra_int(int64(1))
                        for px := __pytra_int(int64(0)); (__step_7 >= 0 && px < __pytra_int(pw)) || (__step_7 < 0 && px > __pytra_int(pw)); px += __step_7 {
                            if (__pytra_int(__pytra_int(__pytra_get_index(__pytra_as_list(__pytra_get_index(r_pentomino, py)), px))) == __pytra_int(int64(1))) {
                                __pytra_set_index(__pytra_as_list(__pytra_get_index(grid, (__pytra_int((__pytra_int(gy) + __pytra_int(py))) % __pytra_int(h)))), (__pytra_int((__pytra_int(gx) + __pytra_int(px))) % __pytra_int(w)), int64(1))
                            }
                        }
                    }
                } else {
                    var ph int64 = __pytra_int(__pytra_len(lwss))
                    __step_8 := __pytra_int(int64(1))
                    for py := __pytra_int(int64(0)); (__step_8 >= 0 && py < __pytra_int(ph)) || (__step_8 < 0 && py > __pytra_int(ph)); py += __step_8 {
                        var pw int64 = __pytra_int(__pytra_len(__pytra_as_list(__pytra_get_index(lwss, py))))
                        __step_9 := __pytra_int(int64(1))
                        for px := __pytra_int(int64(0)); (__step_9 >= 0 && px < __pytra_int(pw)) || (__step_9 < 0 && px > __pytra_int(pw)); px += __step_9 {
                            if (__pytra_int(__pytra_int(__pytra_get_index(__pytra_as_list(__pytra_get_index(lwss, py)), px))) == __pytra_int(int64(1))) {
                                __pytra_set_index(__pytra_as_list(__pytra_get_index(grid, (__pytra_int((__pytra_int(gy) + __pytra_int(py))) % __pytra_int(h)))), (__pytra_int((__pytra_int(gx) + __pytra_int(px))) % __pytra_int(w)), int64(1))
                            }
                        }
                    }
                }
            }
        }
    }
    var frames []any = __pytra_as_list([]any{})
    __step_11 := __pytra_int(int64(1))
    for __loop_10 := __pytra_int(int64(0)); (__step_11 >= 0 && __loop_10 < __pytra_int(steps)) || (__step_11 < 0 && __loop_10 > __pytra_int(steps)); __loop_10 += __step_11 {
        frames = append(__pytra_as_list(frames), render(grid, w, h, cell))
        grid = __pytra_as_list(next_state(grid, w, h))
    }
    __pytra_noop(out_path, (__pytra_int(w) * __pytra_int(cell)), (__pytra_int(h) * __pytra_int(cell)), frames, []any{})
    var elapsed float64 = __pytra_float((__pytra_perf_counter() - start))
    __pytra_print("output:", out_path)
    __pytra_print("frames:", steps)
    __pytra_print("elapsed_sec:", elapsed)
}

func main() {
    run_07_game_of_life_loop()
}
