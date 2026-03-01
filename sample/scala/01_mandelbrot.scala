// Auto-generated Pytra Scala 3 native source from EAST3.
import scala.collection.mutable
import scala.util.boundary, boundary.break
import scala.math.*
import java.nio.file.{Files, Paths}


// 01: Sample that outputs the Mandelbrot set as a PNG image.
// Syntax is kept straightforward with future transpilation in mind.

def escape_count(cx: Double, cy: Double, max_iter: Long): Long = {
    var x: Double = 0.0
    var y: Double = 0.0
    var i: Long = 0L
    while ((i < max_iter)) {
        var x2: Double = (x * x)
        var y2: Double = (y * y)
        if (((x2 + y2) > 4.0)) {
            return i
        }
        y = (((2.0 * x) * y) + cy)
        x = ((x2 - y2) + cx)
        i += 1L
    }
    return max_iter
}

def color_map(iter_count: Long, max_iter: Long): mutable.ArrayBuffer[Long] = {
    if ((iter_count >= max_iter)) {
        return mutable.ArrayBuffer[Long](0L, 0L, 0L)
    }
    var t: Double = (__pytra_float(iter_count) / __pytra_float(max_iter))
    var r: Long = __pytra_int(255.0 * (t * t))
    var g: Long = __pytra_int(255.0 * t)
    var b: Long = __pytra_int(255.0 * (1.0 - t))
    return mutable.ArrayBuffer[Long](r, g, b)
}

def render_mandelbrot(width: Long, height: Long, max_iter: Long, x_min: Double, x_max: Double, y_min: Double, y_max: Double): mutable.ArrayBuffer[Long] = {
    var pixels: mutable.ArrayBuffer[Long] = mutable.ArrayBuffer[Long]()
    var __hoisted_cast_1: Double = __pytra_float(height - 1L)
    var __hoisted_cast_2: Double = __pytra_float(width - 1L)
    var __hoisted_cast_3: Double = __pytra_float(max_iter)
    var y: Long = 0L
    while ((y < height)) {
        var py: Double = (y_min + ((y_max - y_min) * (__pytra_float(y) / __hoisted_cast_1)))
        var x: Long = 0L
        while ((x < width)) {
            var px: Double = (x_min + ((x_max - x_min) * (__pytra_float(x) / __hoisted_cast_2)))
            var it: Long = __pytra_int(escape_count(px, py, max_iter))
            var r: Long = 0L
            var g: Long = 0L
            var b: Long = 0L
            if ((it >= max_iter)) {
                r = 0L
                g = 0L
                b = 0L
            } else {
                var t: Double = (__pytra_float(it) / __hoisted_cast_3)
                r = __pytra_int(255.0 * (t * t))
                g = __pytra_int(255.0 * t)
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

def run_mandelbrot(): Unit = {
    var width: Long = 1600L
    var height: Long = 1200L
    var max_iter: Long = 1000L
    var out_path: String = "sample/out/01_mandelbrot.png"
    var start: Double = __pytra_perf_counter()
    var pixels: mutable.ArrayBuffer[Long] = render_mandelbrot(width, height, max_iter, (-2.2), 1.0, (-1.2), 1.2)
    __pytra_write_rgb_png(out_path, width, height, pixels)
    var elapsed: Double = (__pytra_perf_counter() - start)
    __pytra_print("output:", out_path)
    __pytra_print("size:", width, "x", height)
    __pytra_print("max_iter:", max_iter)
    __pytra_print("elapsed_sec:", elapsed)
}

def main(args: Array[String]): Unit = {
    run_mandelbrot()
}