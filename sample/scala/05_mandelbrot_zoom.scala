import scala.collection.mutable
import scala.util.boundary, boundary.break
import scala.math.*
import java.nio.file.{Files, Paths}


// 05: Sample that outputs a Mandelbrot zoom as an animated GIF.

def render_frame(width: Long, height: Long, center_x: Double, center_y: Double, scale: Double, max_iter: Long): mutable.ArrayBuffer[Long] = {
    var frame: mutable.ArrayBuffer[Long] = __pytra_bytearray(width * height)
    var __hoisted_cast_1: Double = __pytra_float(max_iter)
    var y: Long = 0L
    while (y < height) {
        var row_base: Long = y * width
        var cy: Double = (center_y + (((__pytra_float(y) - __pytra_float(height) * 0.5)) * scale))
        var x: Long = 0L
        while (x < width) {
            var cx: Double = (center_x + (((__pytra_float(x) - __pytra_float(width) * 0.5)) * scale))
            var zx: Double = 0.0
            var zy: Double = 0.0
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
            __pytra_set_index(frame, row_base + x, __pytra_int(255.0 * __pytra_float(i) / __hoisted_cast_1))
            x += 1L
        }
        y += 1L
    }
    return __pytra_bytes(frame)
}

def run_05_mandelbrot_zoom(): Unit = {
    var width: Long = 320L
    var height: Long = 240L
    var frame_count: Long = 48L
    var max_iter: Long = 110L
    var center_x: Double = __pytra_float(-0.743643887037151)
    var center_y: Double = 0.13182590420533
    var base_scale: Double = 3.2 / __pytra_float(width)
    var zoom_per_frame: Double = 0.93
    var out_path: String = "sample/out/05_mandelbrot_zoom.gif"
    var start: Double = __pytra_perf_counter()
    var frames: mutable.ArrayBuffer[Any] = __pytra_as_list(mutable.ArrayBuffer[Any]())
    var scale: Double = base_scale
    var i: Long = 0L
    while (i < frame_count) {
        frames.append(render_frame(width, height, center_x, center_y, scale, max_iter))
        scale *= zoom_per_frame
        i += 1L
    }
    __pytra_save_gif(out_path, width, height, frames, __pytra_grayscale_palette())
    var elapsed: Double = __pytra_perf_counter() - start
    __pytra_print("output:", out_path)
    __pytra_print("frames:", frame_count)
    __pytra_print("elapsed_sec:", elapsed)
}

def main(args: Array[String]): Unit = {
    run_05_mandelbrot_zoom()
}