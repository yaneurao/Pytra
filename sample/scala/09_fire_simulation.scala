import scala.collection.mutable
import scala.util.boundary, boundary.break
import scala.math.*
import java.nio.file.{Files, Paths}


// 09: Sample that outputs a simple fire effect as a GIF.

def fire_palette(): mutable.ArrayBuffer[Long] = {
    var p: mutable.ArrayBuffer[Long] = mutable.ArrayBuffer[Long]()
    var i: Long = 0L
    while (i < 256L) {
        var r: Long = 0L
        var g: Long = 0L
        var b: Long = 0L
        if (i < 85L) {
            r = i * 3L
            g = 0L
            b = 0L
        } else {
            if (i < 170L) {
                r = 255L
                g = ((i - 85L) * 3L)
                b = 0L
            } else {
                r = 255L
                g = 255L
                b = ((i - 170L) * 3L)
            }
        }
        p.append(r)
        p.append(g)
        p.append(b)
        i += 1L
    }
    return __pytra_bytes(p)
}

def run_09_fire_simulation(): Unit = {
    var w: Long = 380L
    var h: Long = 260L
    var steps: Long = 420L
    var out_path: String = "sample/out/09_fire_simulation.gif"
    var start: Double = __pytra_perf_counter()
    var heat: mutable.ArrayBuffer[Any] = __pytra_as_list({ val __out = mutable.ArrayBuffer[Any](); val __step = __pytra_int(1L); var i = __pytra_int(0L); while ((__step >= 0L && i < __pytra_int(h)) || (__step < 0L && i > __pytra_int(h))) { __out.append(__pytra_list_repeat(0L, w)); i += __step }; __out })
    var frames: mutable.ArrayBuffer[Any] = __pytra_as_list(mutable.ArrayBuffer[Any]())
    var t: Long = 0L
    while (t < steps) {
        var x: Long = 0L
        while (x < w) {
            var py_val: Long = (170L + (((x * 13L + t * 17L)) % 86L))
            __pytra_set_index(__pytra_as_list(__pytra_get_index(heat, h - 1L)).asInstanceOf[mutable.ArrayBuffer[Long]], x, py_val)
            x += 1L
        }
        var y: Long = 1L
        while (y < h) {
            x = 0L
            while (x < w) {
                var a: Long = __pytra_int(__pytra_get_index(__pytra_as_list(__pytra_get_index(heat, y)).asInstanceOf[mutable.ArrayBuffer[Long]], x))
                var b: Long = __pytra_int(__pytra_get_index(__pytra_as_list(__pytra_get_index(heat, y)).asInstanceOf[mutable.ArrayBuffer[Long]], (((x - 1L + w)) % w)))
                var c: Long = __pytra_int(__pytra_get_index(__pytra_as_list(__pytra_get_index(heat, y)).asInstanceOf[mutable.ArrayBuffer[Long]], ((x + 1L) % w)))
                var d: Long = __pytra_int(__pytra_get_index(__pytra_as_list(__pytra_get_index(heat, ((y + 1L) % h))).asInstanceOf[mutable.ArrayBuffer[Long]], x))
                var v: Long = __pytra_int(((a + b + c) + d) / 4L)
                var cool: Long = (1L + (((x + y + t)) % 3L))
                var nv: Long = v - cool
                __pytra_set_index(__pytra_as_list(__pytra_get_index(heat, y - 1L)).asInstanceOf[mutable.ArrayBuffer[Long]], x, __pytra_ifexp((nv > 0L), nv, 0L))
                x += 1L
            }
            y += 1L
        }
        var frame: mutable.ArrayBuffer[Long] = __pytra_bytearray(w * h)
        var yy: Long = 0L
        while (yy < h) {
            var row_base: Long = yy * w
            var xx: Long = 0L
            while (xx < w) {
                __pytra_set_index(frame, row_base + xx, __pytra_int(__pytra_get_index(__pytra_as_list(__pytra_get_index(heat, yy)).asInstanceOf[mutable.ArrayBuffer[Long]], xx)))
                xx += 1L
            }
            yy += 1L
        }
        frames.append(__pytra_bytes(frame))
        t += 1L
    }
    __pytra_save_gif(out_path, w, h, frames, fire_palette())
    var elapsed: Double = __pytra_perf_counter() - start
    __pytra_print("output:", out_path)
    __pytra_print("frames:", steps)
    __pytra_print("elapsed_sec:", elapsed)
}

def main(args: Array[String]): Unit = {
    run_09_fire_simulation()
}