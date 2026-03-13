// AUTO-GENERATED FILE. DO NOT EDIT.
// source: src/pytra/std/random.py
// generated-by: tools/gen_runtime_from_manifest.py



fun seed(value: Long) {
    var v: Long = (value and 2147483647L)
    if ((__pytra_int(v) == __pytra_int(0L))) {
        v = 1L
    }
    __pytra_set_index(_state_box, 0L, v)
    __pytra_set_index(_gauss_has_spare, 0L, 0L)
}

fun _next_u31(): Long {
    var s: Any? = __pytra_get_index(_state_box, 0L)
    s = (((1103515245L * s) + 12345L) and 2147483647L)
    __pytra_set_index(_state_box, 0L, s)
    return __pytra_int(s)
}

fun random(): Double {
    return (__pytra_float(_next_u31()) / 2147483648.0)
}

fun randint(a: Long, b: Long): Long {
    var lo: Long = a
    var hi: Long = b
    if ((__pytra_int(hi) < __pytra_int(lo))) {
        var __swap_0: Long = lo
        lo = hi
        hi = __swap_0
    }
    var span: Long = ((hi - lo) + 1L)
    return (lo + __pytra_int(random() * __pytra_float(span)))
}

fun choices(population: MutableList<Any?>, weights: MutableList<Any?>, k: Long): MutableList<Any?> {
    var n: Long = __pytra_len(population)
    if ((__pytra_int(n) <= __pytra_int(0L))) {
        return __pytra_as_list(mutableListOf<Any?>())
    }
    var draws: Long = k
    if ((__pytra_int(draws) < __pytra_int(0L))) {
        draws = 0L
    }
    var weight_vals: MutableList<Any?> = __pytra_as_list(mutableListOf<Any?>())
    val __iter_0 = __pytra_as_list(weights)
    var __i_1: Long = 0L
    while (__i_1 < __iter_0.size.toLong()) {
        val w: Double = __pytra_float(__iter_0[__i_1.toInt()])
        weight_vals.add(w)
        __i_1 += 1L
    }
    var out: MutableList<Any?> = __pytra_as_list(mutableListOf<Any?>())
    if ((__pytra_int(__pytra_len(weight_vals)) == __pytra_int(n))) {
        var total: Double = 0.0
        val __iter_2 = __pytra_as_list(weight_vals)
        var __i_3: Long = 0L
        while (__i_3 < __iter_2.size.toLong()) {
            val w: Double = __pytra_float(__iter_2[__i_3.toInt()])
            if ((__pytra_float(w) > __pytra_float(0.0))) {
                total += w
            }
            __i_3 += 1L
        }
        if ((__pytra_float(total) > __pytra_float(0.0))) {
            var __loop_4 = __pytra_int(0L)
            while (__loop_4 < __pytra_int(draws)) {
                var r: Double = (random() * total)
                var acc: Double = 0.0
                var picked_i: Long = (n - 1L)
                var i = __pytra_int(0L)
                while (i < __pytra_int(n)) {
                    var w: Double = __pytra_float(__pytra_get_index(weight_vals, i))
                    if ((__pytra_float(w) > __pytra_float(0.0))) {
                        acc += w
                    }
                    if ((__pytra_float(r) < __pytra_float(acc))) {
                        picked_i = i
                        break
                    }
                    i += 1L
                }
                out.add(__pytra_int(__pytra_get_index(population, picked_i)))
                __loop_4 += 1L
            }
            return out
        }
    }
    var __loop_7 = __pytra_int(0L)
    while (__loop_7 < __pytra_int(draws)) {
        out.add(__pytra_int(__pytra_get_index(population, randint(0L, (n - 1L)))))
        __loop_7 += 1L
    }
    return out
}

fun gauss(mu: Double, sigma: Double): Double {
    if ((__pytra_int(__pytra_get_index(_gauss_has_spare, 0L)) != __pytra_int(0L))) {
        __pytra_set_index(_gauss_has_spare, 0L, 0L)
        return __pytra_float(mu + (sigma * __pytra_get_index(_gauss_spare, 0L)))
    }
    var u1: Double = 0.0
    while ((__pytra_float(u1) <= __pytra_float(1e-12))) {
        u1 = random()
    }
    var u2: Double = random()
    var mag: Double = pyMathSqrt(__pytra_float((-2.0) * pyMathLog(__pytra_float(u1))))
    var z0: Double = (mag * pyMathCos(__pytra_float((2.0 * pyMathPi()) * u2)))
    var z1: Double = (mag * pyMathSin(__pytra_float((2.0 * pyMathPi()) * u2)))
    __pytra_set_index(_gauss_spare, 0L, z1)
    __pytra_set_index(_gauss_has_spare, 0L, 1L)
    return (mu + (sigma * z0))
}

fun shuffle(xs: MutableList<Any?>) {
    var i: Long = (__pytra_len(xs) - 1L)
    while ((__pytra_int(i) > __pytra_int(0L))) {
        var j: Long = randint(0L, i)
        if ((__pytra_int(j) != __pytra_int(i))) {
            var tmp: Long = __pytra_int(__pytra_get_index(xs, i))
            __pytra_set_index(xs, i, __pytra_int(__pytra_get_index(xs, j)))
            __pytra_set_index(xs, j, tmp)
        }
        i -= 1L
    }
}
