// AUTO-GENERATED FILE. DO NOT EDIT.
// source: src/pytra/std/random.py
// generated-by: tools/gen_runtime_from_manifest.py

import Foundation


func seed(_ value: Int64) {
    var v: Int64 = (value & Int64(2147483647))
    if (__pytra_int(v) == __pytra_int(Int64(0))) {
        v = Int64(1)
    }
    __pytra_setIndex(_state_box, Int64(0), v)
    __pytra_setIndex(_gauss_has_spare, Int64(0), Int64(0))
}

func _next_u31() -> Int64 {
    var s: Any = __pytra_getIndex(_state_box, Int64(0))
    s = (((Int64(1103515245) * s) + Int64(12345)) & Int64(2147483647))
    __pytra_setIndex(_state_box, Int64(0), s)
    return __pytra_int(s)
}

func random() -> Double {
    return (__pytra_float(_next_u31()) / Double(2147483648.0))
}

func randint(_ a: Int64, _ b: Int64) -> Int64 {
    var lo: Int64 = a
    var hi: Int64 = b
    if (__pytra_int(hi) < __pytra_int(lo)) {
        var __swap_0: Int64 = lo
        lo = hi
        hi = __swap_0
    }
    var span: Int64 = ((hi - lo) + Int64(1))
    return (lo + __pytra_int(random() * __pytra_float(span)))
}

func choices(_ population: [Any], _ weights: [Any], _ k: Int64) -> [Any] {
    var n: Int64 = __pytra_len(population)
    if (__pytra_int(n) <= __pytra_int(Int64(0))) {
        return __pytra_as_list([])
    }
    var draws: Int64 = k
    if (__pytra_int(draws) < __pytra_int(Int64(0))) {
        draws = Int64(0)
    }
    var weight_vals: [Any] = __pytra_as_list([])
    do {
        let __iter_0 = __pytra_as_list(weights)
        var __i_1: Int64 = 0
        while __i_1 < Int64(__iter_0.count) {
            let w: Double = __pytra_float(__iter_0[Int(__i_1)])
            weight_vals.append(w)
            __i_1 += 1
        }
    }
    var out: [Any] = __pytra_as_list([])
    if (__pytra_int(__pytra_len(weight_vals)) == __pytra_int(n)) {
        var total: Double = Double(0.0)
        do {
            let __iter_2 = __pytra_as_list(weight_vals)
            var __i_3: Int64 = 0
            while __i_3 < Int64(__iter_2.count) {
                let w: Double = __pytra_float(__iter_2[Int(__i_3)])
                if (__pytra_float(w) > __pytra_float(Double(0.0))) {
                    total += w
                }
                __i_3 += 1
            }
        }
        if (__pytra_float(total) > __pytra_float(Double(0.0))) {
            do {
                var __loop_4 = __pytra_int(Int64(0))
                while (__loop_4 < __pytra_int(draws)) {
                    var r: Double = (random() * total)
                    var acc: Double = Double(0.0)
                    var picked_i: Int64 = (n - Int64(1))
                    do {
                        var i = __pytra_int(Int64(0))
                        while (i < __pytra_int(n)) {
                            var w: Double = __pytra_float(__pytra_getIndex(weight_vals, i))
                            if (__pytra_float(w) > __pytra_float(Double(0.0))) {
                                acc += w
                            }
                            if (__pytra_float(r) < __pytra_float(acc)) {
                                picked_i = i
                                break
                            }
                            i += 1
                        }
                    }
                    out.append(__pytra_int(__pytra_getIndex(population, picked_i)))
                    __loop_4 += 1
                }
            }
            return out
        }
    }
    do {
        var __loop_7 = __pytra_int(Int64(0))
        while (__loop_7 < __pytra_int(draws)) {
            out.append(__pytra_int(__pytra_getIndex(population, randint(Int64(0), (n - Int64(1))))))
            __loop_7 += 1
        }
    }
    return out
}

func gauss(_ mu: Double, _ sigma: Double) -> Double {
    if (__pytra_int(__pytra_getIndex(_gauss_has_spare, Int64(0))) != __pytra_int(Int64(0))) {
        __pytra_setIndex(_gauss_has_spare, Int64(0), Int64(0))
        return __pytra_float(mu + (sigma * __pytra_getIndex(_gauss_spare, Int64(0))))
    }
    var u1: Double = Double(0.0)
    while (__pytra_float(u1) <= __pytra_float(Double(1e-12))) {
        u1 = random()
    }
    var u2: Double = random()
    var mag: Double = pyMathSqrt(__pytra_float((-Double(2.0)) * pyMathLog(__pytra_float(u1))))
    var z0: Double = (mag * pyMathCos(__pytra_float((Double(2.0) * pyMathPi()) * u2)))
    var z1: Double = (mag * pyMathSin(__pytra_float((Double(2.0) * pyMathPi()) * u2)))
    __pytra_setIndex(_gauss_spare, Int64(0), z1)
    __pytra_setIndex(_gauss_has_spare, Int64(0), Int64(1))
    return (mu + (sigma * z0))
}

func shuffle(_ xs: [Any]) {
    var i: Int64 = (__pytra_len(xs) - Int64(1))
    while (__pytra_int(i) > __pytra_int(Int64(0))) {
        var j: Int64 = randint(Int64(0), i)
        if (__pytra_int(j) != __pytra_int(i)) {
            var tmp: Int64 = __pytra_int(__pytra_getIndex(xs, i))
            let __idx_0 = Int(__pytra_index(__pytra_int(i), Int64(xs.count)))
            if __idx_0 >= 0 && __idx_0 < xs.count {
                xs[__idx_0] = __pytra_int(__pytra_getIndex(xs, j))
            }
            let __idx_1 = Int(__pytra_index(__pytra_int(j), Int64(xs.count)))
            if __idx_1 >= 0 && __idx_1 < xs.count {
                xs[__idx_1] = tmp
            }
        }
        i -= Int64(1)
    }
}
