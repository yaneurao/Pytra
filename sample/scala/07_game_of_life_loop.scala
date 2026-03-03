import scala.collection.mutable
import scala.util.boundary, boundary.break
import scala.math.*
import java.nio.file.{Files, Paths}


// 07: Sample that outputs Game of Life evolution as a GIF.

def next_state(grid: mutable.ArrayBuffer[Any], w: Long, h: Long): mutable.ArrayBuffer[Any] = {
    var nxt: mutable.ArrayBuffer[Any] = __pytra_as_list(mutable.ArrayBuffer[Any]())
    var y: Long = 0L
    while (y < h) {
        var row: mutable.ArrayBuffer[Long] = __pytra_as_list(mutable.ArrayBuffer[Any]()).asInstanceOf[mutable.ArrayBuffer[Long]]
        var x: Long = 0L
        while (x < w) {
            var cnt: Long = 0L
            var dy: Long = (-1L)
            while (dy < 2L) {
                var dx: Long = (-1L)
                while (dx < 2L) {
                    if ((dx != 0L) || (dy != 0L)) {
                        var nx: Long = (((x + dx + w)) % w)
                        var ny: Long = (((y + dy + h)) % h)
                        cnt += __pytra_int(__pytra_get_index(__pytra_as_list(__pytra_get_index(grid, ny)).asInstanceOf[mutable.ArrayBuffer[Long]], nx))
                    }
                    dx += 1L
                }
                dy += 1L
            }
            var alive: Long = __pytra_int(__pytra_get_index(__pytra_as_list(__pytra_get_index(grid, y)).asInstanceOf[mutable.ArrayBuffer[Long]], x))
            if ((alive == 1L) && ((cnt == 2L) || (cnt == 3L))) {
                row.append(1L)
            } else {
                if ((alive == 0L) && (cnt == 3L)) {
                    row.append(1L)
                } else {
                    row.append(0L)
                }
            }
            x += 1L
        }
        nxt.append(row)
        y += 1L
    }
    return nxt
}

def render(grid: mutable.ArrayBuffer[Any], w: Long, h: Long, cell: Long): mutable.ArrayBuffer[Long] = {
    var width: Long = w * cell
    var height: Long = h * cell
    var frame: mutable.ArrayBuffer[Long] = __pytra_bytearray(width * height)
    var y: Long = 0L
    while (y < h) {
        var x: Long = 0L
        while (x < w) {
            var v: Long = __pytra_int(__pytra_ifexp((__pytra_int(__pytra_get_index(__pytra_as_list(__pytra_get_index(grid, y)).asInstanceOf[mutable.ArrayBuffer[Long]], x)) != 0L), 255L, 0L))
            var yy: Long = 0L
            while (yy < cell) {
                var base: Long = ((((y * cell + yy)) * width) + x * cell)
                var xx: Long = 0L
                while (xx < cell) {
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

def run_07_game_of_life_loop(): Unit = {
    var w: Long = 144L
    var h: Long = 108L
    var cell: Long = 4L
    var steps: Long = 105L
    var out_path: String = "sample/out/07_game_of_life_loop.gif"
    var start: Double = __pytra_perf_counter()
    var grid: mutable.ArrayBuffer[Any] = __pytra_as_list({ val __out = mutable.ArrayBuffer[Any](); val __step = __pytra_int(1L); var i = __pytra_int(0L); while ((__step >= 0L && i < __pytra_int(h)) || (__step < 0L && i > __pytra_int(h))) { __out.append(__pytra_list_repeat(0L, w)); i += __step }; __out })
    var y: Long = 0L
    while (y < h) {
        var x: Long = 0L
        while (x < w) {
            var noise: Long = (((((x * 37L + y * 73L) + (x * y % 19L)) + ((x + y) % 11L))) % 97L)
            if (noise < 3L) {
                __pytra_set_index(__pytra_as_list(__pytra_get_index(grid, y)).asInstanceOf[mutable.ArrayBuffer[Long]], x, 1L)
            }
            x += 1L
        }
        y += 1L
    }
    var glider: mutable.ArrayBuffer[Any] = __pytra_as_list(mutable.ArrayBuffer[Any](mutable.ArrayBuffer[Long](0L, 1L, 0L), mutable.ArrayBuffer[Long](0L, 0L, 1L), mutable.ArrayBuffer[Long](1L, 1L, 1L)))
    var r_pentomino: mutable.ArrayBuffer[Any] = __pytra_as_list(mutable.ArrayBuffer[Any](mutable.ArrayBuffer[Long](0L, 1L, 1L), mutable.ArrayBuffer[Long](1L, 1L, 0L), mutable.ArrayBuffer[Long](0L, 1L, 0L)))
    var lwss: mutable.ArrayBuffer[Any] = __pytra_as_list(mutable.ArrayBuffer[Any](mutable.ArrayBuffer[Long](0L, 1L, 1L, 1L, 1L), mutable.ArrayBuffer[Long](1L, 0L, 0L, 0L, 1L), mutable.ArrayBuffer[Long](0L, 0L, 0L, 0L, 1L), mutable.ArrayBuffer[Long](1L, 0L, 0L, 1L, 0L)))
    var gy: Long = 8L
    val __step_2 = 18L
    while ((__step_2 >= 0L && gy < h - 8L) || (__step_2 < 0L && gy > h - 8L)) {
        var gx: Long = 8L
        val __step_3 = 22L
        while ((__step_3 >= 0L && gx < w - 8L) || (__step_3 < 0L && gx > w - 8L)) {
            var kind: Long = (((gx * 7L + gy * 11L)) % 3L)
            if (kind == 0L) {
                var ph: Long = __pytra_len(glider)
                var py: Long = 0L
                while (py < ph) {
                    var pw: Long = __pytra_len(__pytra_as_list(__pytra_get_index(glider, py)).asInstanceOf[mutable.ArrayBuffer[Long]])
                    var px: Long = 0L
                    while (px < pw) {
                        if (__pytra_int(__pytra_get_index(__pytra_as_list(__pytra_get_index(glider, py)).asInstanceOf[mutable.ArrayBuffer[Long]], px)) == 1L) {
                            __pytra_set_index(__pytra_as_list(__pytra_get_index(grid, ((gy + py) % h))).asInstanceOf[mutable.ArrayBuffer[Long]], ((gx + px) % w), 1L)
                        }
                        px += 1L
                    }
                    py += 1L
                }
            } else {
                if (kind == 1L) {
                    var ph: Long = __pytra_len(r_pentomino)
                    var py: Long = 0L
                    while (py < ph) {
                        var pw: Long = __pytra_len(__pytra_as_list(__pytra_get_index(r_pentomino, py)).asInstanceOf[mutable.ArrayBuffer[Long]])
                        var px: Long = 0L
                        while (px < pw) {
                            if (__pytra_int(__pytra_get_index(__pytra_as_list(__pytra_get_index(r_pentomino, py)).asInstanceOf[mutable.ArrayBuffer[Long]], px)) == 1L) {
                                __pytra_set_index(__pytra_as_list(__pytra_get_index(grid, ((gy + py) % h))).asInstanceOf[mutable.ArrayBuffer[Long]], ((gx + px) % w), 1L)
                            }
                            px += 1L
                        }
                        py += 1L
                    }
                } else {
                    var ph: Long = __pytra_len(lwss)
                    var py: Long = 0L
                    while (py < ph) {
                        var pw: Long = __pytra_len(__pytra_as_list(__pytra_get_index(lwss, py)).asInstanceOf[mutable.ArrayBuffer[Long]])
                        var px: Long = 0L
                        while (px < pw) {
                            if (__pytra_int(__pytra_get_index(__pytra_as_list(__pytra_get_index(lwss, py)).asInstanceOf[mutable.ArrayBuffer[Long]], px)) == 1L) {
                                __pytra_set_index(__pytra_as_list(__pytra_get_index(grid, ((gy + py) % h))).asInstanceOf[mutable.ArrayBuffer[Long]], ((gx + px) % w), 1L)
                            }
                            px += 1L
                        }
                        py += 1L
                    }
                }
            }
            gx += __step_3
        }
        gy += __step_2
    }
    var frames: mutable.ArrayBuffer[Any] = __pytra_as_list(mutable.ArrayBuffer[Any]())
    var i: Long = 0L
    while (i < steps) {
        frames.append(render(grid, w, h, cell))
        grid = next_state(grid, w, h)
        i += 1L
    }
    __pytra_save_gif(out_path, w * cell, h * cell, frames, __pytra_grayscale_palette())
    var elapsed: Double = __pytra_perf_counter() - start
    __pytra_print("output:", out_path)
    __pytra_print("frames:", steps)
    __pytra_print("elapsed_sec:", elapsed)
}

def main(args: Array[String]): Unit = {
    run_07_game_of_life_loop()
}