// AUTO-GENERATED FILE. DO NOT EDIT.
// source: src/pytra/std/random.py
// generated-by: tools/gen_runtime_from_manifest.py

import scala.collection.mutable
import scala.util.boundary, boundary.break
import java.nio.file.{Files, Paths}


def seed(value: Long): Unit = {
    var v: Long = value & 2147483647L
    if (v == 0L) {
        v = 1L
    }
    __pytra_set_index(_state_box, 0L, v)
    __pytra_set_index(_gauss_has_spare, 0L, 0L)
}

def _next_u31(): Long = {
    var s: Any = __pytra_get_index(_state_box, 0L)
    s = ((1103515245L * s + 12345L) & 2147483647L)
    __pytra_set_index(_state_box, 0L, s)
    return __pytra_int(s)
}

def random(): Double = {
    return __pytra_float(_next_u31()) / 2147483648.0
}

def randint(a: Long, b: Long): Long = {
    var lo: Long = a
    var hi: Long = b
    if (hi < lo) {
        val __swap_0 = lo
        lo = hi
        hi = __swap_0
    }
    var span: Long = (hi - lo + 1L)
    return lo + __pytra_int(random() * __pytra_float(span))
}

def choices(population: mutable.ArrayBuffer[Long], weights: mutable.ArrayBuffer[Double], k: Long): mutable.ArrayBuffer[Long] = {
    var n: Long = __pytra_len(population)
    if (n <= 0L) {
        return __pytra_as_list(mutable.ArrayBuffer[Any]()).asInstanceOf[mutable.ArrayBuffer[Long]]
    }
    var draws: Long = k
    if (draws < 0L) {
        draws = 0L
    }
    var weight_vals: mutable.ArrayBuffer[Double] = __pytra_as_list(mutable.ArrayBuffer[Any]()).asInstanceOf[mutable.ArrayBuffer[Double]]
    val __iter_0 = __pytra_as_list(weights)
    var __i_1: Long = 0L
    while (__i_1 < __iter_0.size.toLong) {
        val w: Double = __pytra_float(__iter_0(__i_1.toInt))
        weight_vals.append(w)
        __i_1 += 1L
    }
    var out: mutable.ArrayBuffer[Long] = __pytra_as_list(mutable.ArrayBuffer[Any]()).asInstanceOf[mutable.ArrayBuffer[Long]]
    if (__pytra_len(weight_vals) == n) {
        var total: Double = 0.0
        val __iter_2 = __pytra_as_list(weight_vals)
        var __i_3: Long = 0L
        while (__i_3 < __iter_2.size.toLong) {
            val w: Double = __pytra_float(__iter_2(__i_3.toInt))
            if (w > 0.0) {
                total += w
            }
            __i_3 += 1L
        }
        if (total > 0.0) {
            var i: Long = 0L
            while (i < draws) {
                var r: Double = random() * total
                var acc: Double = 0.0
                var picked_i: Long = n - 1L
                i = 0L
                boundary:
                    given __breakLabel_6: boundary.Label[Unit] = summon[boundary.Label[Unit]]
                    while (i < n) {
                        boundary:
                            given __continueLabel_7: boundary.Label[Unit] = summon[boundary.Label[Unit]]
                            var w: Double = __pytra_float(__pytra_get_index(weight_vals, i))
                            if (w > 0.0) {
                                acc += w
                            }
                            if (r < acc) {
                                picked_i = i
                                break(())(using __breakLabel_6)
                            }
                        i += 1L
                    }
                out.append(__pytra_int(__pytra_get_index(population, picked_i)))
                i += 1L
            }
            return out
        }
    }
    var i: Long = 0L
    while (i < draws) {
        out.append(__pytra_int(__pytra_get_index(population, randint(0L, n - 1L))))
        i += 1L
    }
    return out
}

def gauss(mu: Double, sigma: Double): Double = {
    if (__pytra_int(__pytra_get_index(_gauss_has_spare, 0L)) != 0L) {
        __pytra_set_index(_gauss_has_spare, 0L, 0L)
        return __pytra_float(mu + sigma * __pytra_get_index(_gauss_spare, 0L))
    }
    var u1: Double = 0.0
    while (u1 <= 1e-12) {
        u1 = random()
    }
    var u2: Double = random()
    var mag: Double = scala.math.sqrt(__pytra_float((-2.0) * scala.math.log(__pytra_float(u1))))
    var z0: Double = mag * scala.math.cos(__pytra_float(2.0 * scala.math.Pi * u2))
    var z1: Double = mag * scala.math.sin(__pytra_float(2.0 * scala.math.Pi * u2))
    __pytra_set_index(_gauss_spare, 0L, z1)
    __pytra_set_index(_gauss_has_spare, 0L, 1L)
    return (mu + sigma * z0)
}

def shuffle(xs: mutable.ArrayBuffer[Long]): Unit = {
    var i: Long = __pytra_len(xs) - 1L
    while (i > 0L) {
        var j: Long = randint(0L, i)
        if (j != i) {
            var tmp: Long = __pytra_int(__pytra_get_index(xs, i))
            __pytra_set_index(xs, i, __pytra_int(__pytra_get_index(xs, j)))
            __pytra_set_index(xs, j, tmp)
        }
        i -= 1L
    }
}
