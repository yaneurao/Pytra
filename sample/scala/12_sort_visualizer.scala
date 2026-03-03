import scala.collection.mutable
import scala.util.boundary, boundary.break
import scala.math.*
import java.nio.file.{Files, Paths}


// 12: Sample that outputs intermediate states of bubble sort as a GIF.

def render(values: mutable.ArrayBuffer[Long], w: Long, h: Long): mutable.ArrayBuffer[Long] = {
    var frame: mutable.ArrayBuffer[Long] = __pytra_bytearray(w * h)
    var n: Long = __pytra_len(values)
    var bar_w: Double = __pytra_float(w) / __pytra_float(n)
    var __hoisted_cast_1: Double = __pytra_float(n)
    var __hoisted_cast_2: Double = __pytra_float(h)
    var i: Long = 0L
    while (i < n) {
        var x0: Long = __pytra_int(__pytra_float(i) * bar_w)
        var x1: Long = __pytra_int((__pytra_float(i + 1L)) * bar_w)
        if (x1 <= x0) {
            x1 = x0 + 1L
        }
        var bh: Long = __pytra_int((__pytra_float(__pytra_int(__pytra_get_index(values, i))) / __hoisted_cast_1) * __hoisted_cast_2)
        var y: Long = h - bh
        y = y
        while (y < h) {
            var x: Long = x0
            while (x < x1) {
                __pytra_set_index(frame, (y * w + x), 255L)
                x += 1L
            }
            y += 1L
        }
        i += 1L
    }
    return __pytra_bytes(frame)
}

def run_12_sort_visualizer(): Unit = {
    var w: Long = 320L
    var h: Long = 180L
    var n: Long = 124L
    var out_path: String = "sample/out/12_sort_visualizer.gif"
    var start: Double = __pytra_perf_counter()
    var values: mutable.ArrayBuffer[Long] = __pytra_as_list(mutable.ArrayBuffer[Any]()).asInstanceOf[mutable.ArrayBuffer[Long]]
    var i: Long = 0L
    while (i < n) {
        values.append((((i * 37L + 19L)) % n))
        i += 1L
    }
    var frames: mutable.ArrayBuffer[Any] = __pytra_as_list(mutable.ArrayBuffer[Any](render(values, w, h)))
    var frame_stride: Long = 16L
    var op: Long = 0L
    i = 0L
    boundary:
        given __breakLabel_2: boundary.Label[Unit] = summon[boundary.Label[Unit]]
        while (i < n) {
            boundary:
                given __continueLabel_3: boundary.Label[Unit] = summon[boundary.Label[Unit]]
                var swapped: Boolean = false
                var j: Long = 0L
                while (j < (n - i - 1L)) {
                    if (__pytra_int(__pytra_get_index(values, j)) > __pytra_int(__pytra_get_index(values, j + 1L))) {
                        val __tuple_5 = __pytra_as_list(mutable.ArrayBuffer[Long](__pytra_int(__pytra_get_index(values, j + 1L)), __pytra_int(__pytra_get_index(values, j))))
                        __pytra_set_index(values, j, __pytra_int(__tuple_5(0)))
                        __pytra_set_index(values, j + 1L, __pytra_int(__tuple_5(1)))
                        swapped = true
                    }
                    if (op % frame_stride == 0L) {
                        frames.append(render(values, w, h))
                    }
                    op += 1L
                    j += 1L
                }
                if (!swapped) {
                    break(())(using __breakLabel_2)
                }
            i += 1L
        }
    __pytra_save_gif(out_path, w, h, frames, __pytra_grayscale_palette())
    var elapsed: Double = __pytra_perf_counter() - start
    __pytra_print("output:", out_path)
    __pytra_print("frames:", __pytra_len(frames))
    __pytra_print("elapsed_sec:", elapsed)
}

def main(args: Array[String]): Unit = {
    run_12_sort_visualizer()
}