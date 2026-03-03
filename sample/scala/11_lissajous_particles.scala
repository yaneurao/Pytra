import scala.collection.mutable
import scala.util.boundary, boundary.break
import scala.math.*
import java.nio.file.{Files, Paths}


// 11: Sample that outputs Lissajous-motion particles as a GIF.

def color_palette(): mutable.ArrayBuffer[Long] = {
    var p: mutable.ArrayBuffer[Long] = mutable.ArrayBuffer[Long]()
    var i: Long = 0L
    while (i < 256L) {
        var r: Long = i
        var g: Long = (i * 3L % 256L)
        var b: Long = 255L - i
        p.append(r)
        p.append(g)
        p.append(b)
        i += 1L
    }
    return __pytra_bytes(p)
}

def run_11_lissajous_particles(): Unit = {
    var w: Long = 320L
    var h: Long = 240L
    var frames_n: Long = 360L
    var particles: Long = 48L
    var out_path: String = "sample/out/11_lissajous_particles.gif"
    var start: Double = __pytra_perf_counter()
    var frames: mutable.ArrayBuffer[Any] = __pytra_as_list(mutable.ArrayBuffer[Any]())
    var t: Long = 0L
    while (t < frames_n) {
        var frame: mutable.ArrayBuffer[Long] = __pytra_bytearray(w * h)
        var __hoisted_cast_1: Double = __pytra_float(t)
        var p: Long = 0L
        while (p < particles) {
            var phase: Double = __pytra_float(p) * 0.261799
            var x: Long = __pytra_int(__pytra_float(w) * 0.5 + (__pytra_float(w) * 0.38 * scala.math.sin(__pytra_float(0.11 * __hoisted_cast_1 + phase * 2.0))))
            var y: Long = __pytra_int(__pytra_float(h) * 0.5 + (__pytra_float(h) * 0.38 * scala.math.sin(__pytra_float(0.17 * __hoisted_cast_1 + phase * 3.0))))
            var color: Long = (30L + (p * 9L % 220L))
            var dy: Long = (-2L)
            while (dy < 3L) {
                var dx: Long = (-2L)
                while (dx < 3L) {
                    var xx: Long = x + dx
                    var yy: Long = y + dy
                    if ((xx >= 0L) && (xx < w) && (yy >= 0L) && (yy < h)) {
                        var d2: Long = (dx * dx + dy * dy)
                        if (d2 <= 4L) {
                            var idx: Long = (yy * w + xx)
                            var v: Long = (color - d2 * 20L)
                            v = __pytra_int(__pytra_max(0L, v))
                            if (__pytra_int(v) > __pytra_int(__pytra_get_index(frame, idx))) {
                                __pytra_set_index(frame, idx, v)
                            }
                        }
                    }
                    dx += 1L
                }
                dy += 1L
            }
            p += 1L
        }
        frames.append(__pytra_bytes(frame))
        t += 1L
    }
    __pytra_save_gif(out_path, w, h, frames, color_palette())
    var elapsed: Double = __pytra_perf_counter() - start
    __pytra_print("output:", out_path)
    __pytra_print("frames:", frames_n)
    __pytra_print("elapsed_sec:", elapsed)
}

def main(args: Array[String]): Unit = {
    run_11_lissajous_particles()
}