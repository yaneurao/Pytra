import scala.collection.mutable
import scala.util.boundary, boundary.break
import scala.math.*
import java.nio.file.{Files, Paths}


// 04: Sample that renders an orbit-trap Julia set and writes a PNG image.

def render_orbit_trap_julia(width: Long, height: Long, max_iter: Long, cx: Double, cy: Double): mutable.ArrayBuffer[Long] = {
    var pixels: mutable.ArrayBuffer[Long] = mutable.ArrayBuffer[Long]()
    var __hoisted_cast_1: Double = __pytra_float(height - 1L)
    var __hoisted_cast_2: Double = __pytra_float(width - 1L)
    var __hoisted_cast_3: Double = __pytra_float(max_iter)
    var y: Long = 0L
    while (y < height) {
        var zy0: Double = ((-1.3) + (2.6 * (__pytra_float(y) / __hoisted_cast_1)))
        var x: Long = 0L
        while (x < width) {
            var zx: Double = ((-1.9) + (3.8 * (__pytra_float(x) / __hoisted_cast_2)))
            var zy: Double = zy0
            var trap: Double = 1000000000.0
            var i: Long = 0L
            boundary:
                given __breakLabel_2: boundary.Label[Unit] = summon[boundary.Label[Unit]]
                while (i < max_iter) {
                    boundary:
                        given __continueLabel_3: boundary.Label[Unit] = summon[boundary.Label[Unit]]
                        var ax: Double = zx
                        if (ax < 0.0) {
                            ax = __pytra_float(-ax)
                        }
                        var ay: Double = zy
                        if (ay < 0.0) {
                            ay = __pytra_float(-ay)
                        }
                        var dxy: Double = zx - zy
                        if (dxy < 0.0) {
                            dxy = __pytra_float(-dxy)
                        }
                        if (ax < trap) {
                            trap = ax
                        }
                        if (ay < trap) {
                            trap = ay
                        }
                        if (dxy < trap) {
                            trap = dxy
                        }
                        var zx2: Double = zx * zx
                        var zy2: Double = zy * zy
                        if (zx2 + zy2 > 4.0) {
                            break(())(using __breakLabel_2)
                        }
                        zy = ((2.0 * zx * zy) + cy)
                        zx = (zx2 - zy2 + cx)
                        i += 1L
                }
            var r: Long = 0L
            var g: Long = 0L
            var b: Long = 0L
            if (i >= max_iter) {
                r = 0L
                g = 0L
                b = 0L
            } else {
                var trap_scaled: Double = trap * 3.2
                if (trap_scaled > 1.0) {
                    trap_scaled = 1.0
                }
                if (trap_scaled < 0.0) {
                    trap_scaled = 0.0
                }
                var t: Double = __pytra_float(i) / __hoisted_cast_3
                var tone: Long = __pytra_int(255.0 * (1.0 - trap_scaled))
                r = __pytra_int(__pytra_float(tone) * ((0.35 + 0.65 * t)))
                g = __pytra_int(__pytra_float(tone) * ((0.15 + (0.85 * (1.0 - t)))))
                b = __pytra_int(255.0 * ((0.25 + 0.75 * t)))
                if (r > 255L) {
                    r = 255L
                }
                if (g > 255L) {
                    g = 255L
                }
                if (b > 255L) {
                    b = 255L
                }
            }
            pixels.append(r)
            pixels.append(g)
            pixels.append(b)
            x += 1L
        }
        y += 1L
    }
    return pixels
}

def run_04_orbit_trap_julia(): Unit = {
    var width: Long = 1920L
    var height: Long = 1080L
    var max_iter: Long = 1400L
    var out_path: String = "sample/out/04_orbit_trap_julia.png"
    var start: Double = __pytra_perf_counter()
    var pixels: mutable.ArrayBuffer[Long] = render_orbit_trap_julia(width, height, max_iter, (-0.7269), 0.1889)
    __pytra_write_rgb_png(out_path, width, height, pixels)
    var elapsed: Double = __pytra_perf_counter() - start
    __pytra_print("output:", out_path)
    __pytra_print("size:", width, "x", height)
    __pytra_print("max_iter:", max_iter)
    __pytra_print("elapsed_sec:", elapsed)
}

def main(args: Array[String]): Unit = {
    run_04_orbit_trap_julia()
}