// AUTO-GENERATED FILE. DO NOT EDIT.
// source: src/pytra/std/random.py
// generated-by: tools/gen_runtime_from_manifest.py

package main


func seed(value int64) {
    var v int64 = (value & int64(2147483647))
    if (v == int64(0)) {
        v = int64(1)
    }
    __pytra_set_index(_state_box, int64(0), v)
    __pytra_set_index(_gauss_has_spare, int64(0), int64(0))
}

func _next_u31() int64 {
    var s any = __pytra_get_index(_state_box, int64(0))
    s = (((int64(1103515245) * s) + int64(12345)) & int64(2147483647))
    __pytra_set_index(_state_box, int64(0), s)
    return __pytra_int(s)
}

func random() float64 {
    return (float64(_next_u31()) / float64(2147483648.0))
}

func randint(a int64, b int64) int64 {
    var lo int64 = a
    var hi int64 = b
    if (hi < lo) {
        var __swap_0 = lo
        lo = hi
        hi = __swap_0
    }
    var span int64 = ((hi - lo) + int64(1))
    return (lo + __pytra_int((random() * float64(span))))
}

func choices(population []any, weights []any, k int64) []any {
    var n int64 = __pytra_len(population)
    if (n <= int64(0)) {
        return __pytra_as_list([]any{})
    }
    var draws int64 = k
    if (draws < int64(0)) {
        draws = int64(0)
    }
    var weight_vals []any = __pytra_as_list([]any{})
    __iter_0 := __pytra_as_list(weights)
    for __i_1 := int64(0); __i_1 < int64(len(__iter_0)); __i_1 += 1 {
        var w float64 = __pytra_float(__iter_0[__i_1])
        weight_vals = append(weight_vals, w)
    }
    var out []any = __pytra_as_list([]any{})
    if (__pytra_len(weight_vals) == n) {
        var total float64 = float64(0.0)
        __iter_2 := __pytra_as_list(weight_vals)
        for __i_3 := int64(0); __i_3 < int64(len(__iter_2)); __i_3 += 1 {
            var w float64 = __pytra_float(__iter_2[__i_3])
            if (w > float64(0.0)) {
                total += w
            }
        }
        if (total > float64(0.0)) {
            for __loop_4 := int64(0); __loop_4 < draws; __loop_4 += 1 {
                var r float64 = (random() * total)
                var acc float64 = float64(0.0)
                var picked_i int64 = (n - int64(1))
                for i := int64(0); i < n; i += 1 {
                    var w float64 = __pytra_float(__pytra_get_index(weight_vals, i))
                    if (w > float64(0.0)) {
                        acc += w
                    }
                    if (r < acc) {
                        picked_i = i
                        break
                    }
                }
                out = append(out, __pytra_int(__pytra_get_index(population, picked_i)))
            }
            return __pytra_as_list(out)
        }
    }
    for __loop_5 := int64(0); __loop_5 < draws; __loop_5 += 1 {
        out = append(out, __pytra_int(__pytra_get_index(population, randint(int64(0), (n - int64(1))))))
    }
    return __pytra_as_list(out)
}

func gauss(mu float64, sigma float64) float64 {
    if (__pytra_int(__pytra_get_index(_gauss_has_spare, int64(0))) != int64(0)) {
        __pytra_set_index(_gauss_has_spare, int64(0), int64(0))
        return (mu + (sigma * __pytra_get_index(_gauss_spare, int64(0))))
    }
    var u1 float64 = float64(0.0)
    for (u1 <= float64(1e-12)) {
        u1 = random()
    }
    var u2 float64 = random()
    var mag float64 = pyMathSqrt(((-float64(2.0)) * pyMathLog(u1)))
    var z0 float64 = (mag * pyMathCos(__pytra_float(((float64(2.0) * __pytra_float(pyMathPi())) * u2))))
    var z1 float64 = (mag * pyMathSin(__pytra_float(((float64(2.0) * __pytra_float(pyMathPi())) * u2))))
    __pytra_set_index(_gauss_spare, int64(0), z1)
    __pytra_set_index(_gauss_has_spare, int64(0), int64(1))
    return (mu + (sigma * z0))
}

func shuffle(xs []any) {
    var i int64 = (__pytra_len(xs) - int64(1))
    for (i > int64(0)) {
        var j int64 = randint(int64(0), i)
        if (j != i) {
            var tmp int64 = __pytra_int(__pytra_get_index(xs, i))
            __pytra_set_index(xs, i, __pytra_int(__pytra_get_index(xs, j)))
            __pytra_set_index(xs, j, tmp)
        }
        i -= int64(1)
    }
}
