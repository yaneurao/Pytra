import scala.collection.mutable
import scala.util.boundary, boundary.break
import scala.math.*
import java.nio.file.{Files, Paths}


// 03: Sample that outputs a Julia set as a PNG image.
// Implemented with simple loop-centric logic for transpilation compatibility.

def render_julia(width: Long, height: Long, max_iter: Long, cx: Double, cy: Double): mutable.ArrayBuffer[Long] = {
    var pixels: mutable.ArrayBuffer[Long] = mutable.ArrayBuffer[Long]()
    var __hoisted_cast_1: Double = __pytra_float(height - 1L)
    var __hoisted_cast_2: Double = __pytra_float(width - 1L)
    var __hoisted_cast_3: Double = __pytra_float(max_iter)
    var y: Long = 0L
    while (y < height) {
        var zy0: Double = ((-1.2) + (2.4 * (__pytra_float(y) / __hoisted_cast_1)))
        var x: Long = 0L
        while (x < width) {
            var zx: Double = ((-1.8) + (3.6 * (__pytra_float(x) / __hoisted_cast_2)))
            var zy: Double = zy0
            var i: Long = 0L
            boundary:
                given __breakLabel_2: boundary.Label[Unit] = summon[boundary.Label[Unit]]
                while (i < max_iter) {
                    boundary:
                        given __continueLabel_3: boundary.Label[Unit] = summon[boundary.Label[Unit]]
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
                var t: Double = __pytra_float(i) / __hoisted_cast_3
                r = __pytra_int(255.0 * ((0.2 + 0.8 * t)))
                g = __pytra_int(255.0 * ((0.1 + (0.9 * t * t))))
                b = __pytra_int(255.0 * (1.0 - t))
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

def run_julia(): Unit = {
    var width: Long = 3840L
    var height: Long = 2160L
    var max_iter: Long = 20000L
    var out_path: String = "sample/out/03_julia_set.png"
    var start: Double = __pytra_perf_counter()
    var pixels: mutable.ArrayBuffer[Long] = render_julia(width, height, max_iter, (-0.8), 0.156)
    __pytra_write_rgb_png(out_path, width, height, pixels)
    var elapsed: Double = __pytra_perf_counter() - start
    __pytra_print("output:", out_path)
    __pytra_print("size:", width, "x", height)
    __pytra_print("max_iter:", max_iter)
    __pytra_print("elapsed_sec:", elapsed)
}

def main(args: Array[String]): Unit = {
    run_julia()
}