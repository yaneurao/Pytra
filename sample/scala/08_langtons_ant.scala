// Auto-generated Pytra Scala 3 native source from EAST3.
import scala.collection.mutable
import scala.util.boundary, boundary.break
import scala.math.*
import java.nio.file.{Files, Paths}


// 08: Sample that outputs Langton's Ant trajectories as a GIF.

def capture(grid: mutable.ArrayBuffer[Any], w: Long, h: Long): mutable.ArrayBuffer[Long] = {
    var frame: mutable.ArrayBuffer[Long] = __pytra_bytearray((w * h))
    var y: Long = 0L
    while ((y < h)) {
        var row_base: Long = (y * w)
        var x: Long = 0L
        while ((x < w)) {
            __pytra_set_index(frame, (row_base + x), __pytra_ifexp((__pytra_int(__pytra_get_index(__pytra_get_index(grid, y), x)) != 0L), 255L, 0L))
            x += 1L
        }
        y += 1L
    }
    return __pytra_bytes(frame)
}

def run_08_langtons_ant(): Unit = {
    var w: Long = 420L
    var h: Long = 420L
    var out_path: String = "sample/out/08_langtons_ant.gif"
    var start: Double = __pytra_perf_counter()
    var grid: mutable.ArrayBuffer[Any] = __pytra_as_list({ val __out = mutable.ArrayBuffer[Any](); val __step = __pytra_int(1L); var i = __pytra_int(0L); while ((__step >= 0L && i < __pytra_int(h)) || (__step < 0L && i > __pytra_int(h))) { __out.append(__pytra_list_repeat(0L, w)); i += __step }; __out })
    var x: Long = (__pytra_int(w / 2L))
    var y: Long = (__pytra_int(h / 2L))
    var d: Long = 0L
    var steps_total: Long = 600000L
    var capture_every: Long = 3000L
    var frames: mutable.ArrayBuffer[Any] = __pytra_as_list(mutable.ArrayBuffer[Any]())
    var i: Long = 0L
    while ((i < steps_total)) {
        if ((__pytra_int(__pytra_get_index(__pytra_get_index(grid, y), x)) == 0L)) {
            d = ((d + 1L) % 4L)
            __pytra_set_index(__pytra_get_index(grid, y), x, 1L)
        } else {
            d = ((d + 3L) % 4L)
            __pytra_set_index(__pytra_get_index(grid, y), x, 0L)
        }
        if ((d == 0L)) {
            y = (((y - 1L) + h) % h)
        } else {
            if ((d == 1L)) {
                x = ((x + 1L) % w)
            } else {
                if ((d == 2L)) {
                    y = ((y + 1L) % h)
                } else {
                    x = (((x - 1L) + w) % w)
                }
            }
        }
        if (((i % capture_every) == 0L)) {
            frames.append(capture(grid, w, h))
        }
        i += 1L
    }
    __pytra_save_gif(out_path, w, h, frames, __pytra_grayscale_palette())
    var elapsed: Double = (__pytra_perf_counter() - start)
    __pytra_print("output:", out_path)
    __pytra_print("frames:", __pytra_len(frames))
    __pytra_print("elapsed_sec:", elapsed)
}

def main(args: Array[String]): Unit = {
    run_08_langtons_ant()
}