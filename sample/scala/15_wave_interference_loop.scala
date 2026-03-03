import scala.collection.mutable
import scala.util.boundary, boundary.break
import scala.math.*
import java.nio.file.{Files, Paths}


// 15: Sample that renders wave interference animation and writes a GIF.

def run_15_wave_interference_loop(): Unit = {
    var w: Long = 320L
    var h: Long = 240L
    var frames_n: Long = 96L
    var out_path: String = "sample/out/15_wave_interference_loop.gif"
    var start: Double = __pytra_perf_counter()
    var frames: mutable.ArrayBuffer[Any] = __pytra_as_list(mutable.ArrayBuffer[Any]())
    var t: Long = 0L
    while (t < frames_n) {
        var frame: mutable.ArrayBuffer[Long] = __pytra_bytearray(w * h)
        var phase: Double = __pytra_float(t) * 0.12
        var y: Long = 0L
        while (y < h) {
            var row_base: Long = y * w
            var x: Long = 0L
            while (x < w) {
                var dx: Long = x - 160L
                var dy: Long = y - 120L
                var v: Double = __pytra_float((scala.math.sin(__pytra_float(((__pytra_float(x) + __pytra_float(t) * 1.5)) * 0.045)) + scala.math.sin(__pytra_float(((__pytra_float(y) - __pytra_float(t) * 1.2)) * 0.04)) + scala.math.sin(__pytra_float(((__pytra_float(x + y)) * 0.02) + phase))) + scala.math.sin(__pytra_float(scala.math.sqrt(__pytra_float(dx * dx + dy * dy)) * 0.08 - phase * 1.3)))
                var c: Long = __pytra_int((v + 4.0) * (255.0 / 8.0))
                if (c < 0L) {
                    c = 0L
                }
                if (c > 255L) {
                    c = 255L
                }
                __pytra_set_index(frame, row_base + x, c)
                x += 1L
            }
            y += 1L
        }
        frames.append(__pytra_bytes(frame))
        t += 1L
    }
    __pytra_save_gif(out_path, w, h, frames, __pytra_grayscale_palette())
    var elapsed: Double = __pytra_perf_counter() - start
    __pytra_print("output:", out_path)
    __pytra_print("frames:", frames_n)
    __pytra_print("elapsed_sec:", elapsed)
}

def main(args: Array[String]): Unit = {
    run_15_wave_interference_loop()
}