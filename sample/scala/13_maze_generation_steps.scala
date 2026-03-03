import scala.collection.mutable
import scala.util.boundary, boundary.break
import scala.math.*
import java.nio.file.{Files, Paths}


// 13: Sample that outputs DFS maze-generation progress as a GIF.

def capture(grid: mutable.ArrayBuffer[Any], w: Long, h: Long, scale: Long): mutable.ArrayBuffer[Long] = {
    var width: Long = w * scale
    var height: Long = h * scale
    var frame: mutable.ArrayBuffer[Long] = __pytra_bytearray(width * height)
    var y: Long = 0L
    while (y < h) {
        var x: Long = 0L
        while (x < w) {
            var v: Long = __pytra_int(__pytra_ifexp((__pytra_int(__pytra_get_index(__pytra_as_list(__pytra_get_index(grid, y)).asInstanceOf[mutable.ArrayBuffer[Long]], x)) == 0L), 255L, 40L))
            var yy: Long = 0L
            while (yy < scale) {
                var base: Long = ((((y * scale + yy)) * width) + x * scale)
                var xx: Long = 0L
                while (xx < scale) {
                    __pytra_set_index(frame, base + xx, v)
                    xx += 1L
                }
                yy += 1L
            }
            x += 1L
        }
        y += 1L
    }
    return __pytra_bytes(frame)
}

def run_13_maze_generation_steps(): Unit = {
    var cell_w: Long = 89L
    var cell_h: Long = 67L
    var scale: Long = 5L
    var capture_every: Long = 20L
    var out_path: String = "sample/out/13_maze_generation_steps.gif"
    var start: Double = __pytra_perf_counter()
    var grid: mutable.ArrayBuffer[Any] = __pytra_as_list({ val __out = mutable.ArrayBuffer[Any](); val __step = __pytra_int(1L); var i = __pytra_int(0L); while ((__step >= 0L && i < __pytra_int(cell_h)) || (__step < 0L && i > __pytra_int(cell_h))) { __out.append(__pytra_list_repeat(1L, cell_w)); i += __step }; __out })
    var stack: mutable.ArrayBuffer[Any] = __pytra_as_list(mutable.ArrayBuffer[Any](mutable.ArrayBuffer[Long](1L, 1L)))
    __pytra_set_index(__pytra_as_list(__pytra_get_index(grid, 1L)).asInstanceOf[mutable.ArrayBuffer[Long]], 1L, 0L)
    var dirs: mutable.ArrayBuffer[Any] = __pytra_as_list(mutable.ArrayBuffer[Any](mutable.ArrayBuffer[Long](2L, 0L), mutable.ArrayBuffer[Long]((-2L), 0L), mutable.ArrayBuffer[Long](0L, 2L), mutable.ArrayBuffer[Long](0L, (-2L))))
    var frames: mutable.ArrayBuffer[Any] = __pytra_as_list(mutable.ArrayBuffer[Any]())
    var step: Long = 0L
    while (__pytra_len(stack) != 0L) {
        val __tuple_0 = __pytra_as_list(__pytra_as_list(__pytra_get_index(stack, (-1L))).asInstanceOf[mutable.ArrayBuffer[Long]])
        var x: Long = __pytra_int(__tuple_0(0))
        var y: Long = __pytra_int(__tuple_0(1))
        var candidates: mutable.ArrayBuffer[Any] = __pytra_as_list(mutable.ArrayBuffer[Any]())
        var k: Long = 0L
        while (k < 4L) {
            val __tuple_2 = __pytra_as_list(__pytra_as_list(__pytra_get_index(dirs, k)).asInstanceOf[mutable.ArrayBuffer[Long]])
            var dx: Long = __pytra_int(__tuple_2(0))
            var dy: Long = __pytra_int(__tuple_2(1))
            var nx: Long = __pytra_int(x + dx)
            var ny: Long = __pytra_int(y + dy)
            if ((__pytra_int(nx) >= 1L) && (__pytra_int(nx) < cell_w - 1L) && (__pytra_int(ny) >= 1L) && (__pytra_int(ny) < cell_h - 1L) && (__pytra_int(__pytra_get_index(__pytra_as_list(__pytra_get_index(grid, ny)).asInstanceOf[mutable.ArrayBuffer[Long]], nx)) == 1L)) {
                if (__pytra_int(dx) == 2L) {
                    candidates.append(mutable.ArrayBuffer[Any](nx, ny, x + 1L, y))
                } else {
                    if (__pytra_int(dx) == (-2L)) {
                        candidates.append(mutable.ArrayBuffer[Any](nx, ny, x - 1L, y))
                    } else {
                        if (__pytra_int(dy) == 2L) {
                            candidates.append(mutable.ArrayBuffer[Any](nx, ny, x, y + 1L))
                        } else {
                            candidates.append(mutable.ArrayBuffer[Any](nx, ny, x, y - 1L))
                        }
                    }
                }
            }
            k += 1L
        }
        if (__pytra_len(candidates) == 0L) {
            stack = __pytra_pop_last(__pytra_as_list(stack))
        } else {
            var sel: mutable.ArrayBuffer[Long] = __pytra_as_list(__pytra_as_list(__pytra_get_index(candidates, ((__pytra_int((x * 17L + y * 29L) + __pytra_len(stack) * 13L)) % __pytra_len(candidates)))).asInstanceOf[mutable.ArrayBuffer[Long]]).asInstanceOf[mutable.ArrayBuffer[Long]]
            val __tuple_3 = __pytra_as_list(sel)
            var nx: Long = __pytra_int(__tuple_3(0))
            var ny: Long = __pytra_int(__tuple_3(1))
            var wx: Long = __pytra_int(__tuple_3(2))
            var wy: Long = __pytra_int(__tuple_3(3))
            __pytra_set_index(__pytra_as_list(__pytra_get_index(grid, wy)).asInstanceOf[mutable.ArrayBuffer[Long]], wx, 0L)
            __pytra_set_index(__pytra_as_list(__pytra_get_index(grid, ny)).asInstanceOf[mutable.ArrayBuffer[Long]], nx, 0L)
            stack.append(mutable.ArrayBuffer[Any](nx, ny))
        }
        if (step % capture_every == 0L) {
            frames.append(capture(grid, cell_w, cell_h, scale))
        }
        step += 1L
    }
    frames.append(capture(grid, cell_w, cell_h, scale))
    __pytra_save_gif(out_path, cell_w * scale, cell_h * scale, frames, __pytra_grayscale_palette())
    var elapsed: Double = __pytra_perf_counter() - start
    __pytra_print("output:", out_path)
    __pytra_print("frames:", __pytra_len(frames))
    __pytra_print("elapsed_sec:", elapsed)
}

def main(args: Array[String]): Unit = {
    run_13_maze_generation_steps()
}