// Auto-generated Pytra Scala 3 native source from EAST3.
import scala.collection.mutable
import scala.util.boundary, boundary.break
import scala.math.*
import java.nio.file.{Files, Paths}

def __pytra_to_byte(v: Any): Int = {
    (__pytra_int(v) & 0xFFL).toInt
}

def __pytra_to_byte_buffer(v: Any): mutable.ArrayBuffer[Byte] = {
    val src = __pytra_as_list(v)
    val out = mutable.ArrayBuffer[Byte]()
    var i = 0
    while (i < src.size) {
        out.append(__pytra_to_byte(src(i)).toByte)
        i += 1
    }
    out
}

def __pytra_append_u16le(out: mutable.ArrayBuffer[Byte], value: Int): Unit = {
    out.append((value & 0xFF).toByte)
    out.append(((value >>> 8) & 0xFF).toByte)
}

def __pytra_write_file_bytes(path: Any, data: mutable.ArrayBuffer[Byte]): Unit = {
    val p = Paths.get(__pytra_str(path))
    val parent = p.getParent
    if (parent != null) Files.createDirectories(parent)
    Files.write(p, data.toArray)
}

def __pytra_grayscale_palette(): mutable.ArrayBuffer[Any] = {
    val p = mutable.ArrayBuffer[Any]()
    var i = 0L
    while (i < 256L) {
        p.append(i)
        p.append(i)
        p.append(i)
        i += 1L
    }
    p
}

def __pytra_gif_lzw_encode(data: mutable.ArrayBuffer[Byte], minCodeSize: Int = 8): mutable.ArrayBuffer[Byte] = {
    if (data.isEmpty) return mutable.ArrayBuffer[Byte]()
    val clearCode = 1 << minCodeSize
    val endCode = clearCode + 1
    var codeSize = minCodeSize + 1
    val out = mutable.ArrayBuffer[Byte]()
    var bitBuffer = 0
    var bitCount = 0
    def writeCode(code: Int): Unit = {
        bitBuffer |= (code << bitCount)
        bitCount += codeSize
        while (bitCount >= 8) {
            out.append((bitBuffer & 0xFF).toByte)
            bitBuffer = bitBuffer >>> 8
            bitCount -= 8
        }
    }
    writeCode(clearCode)
    codeSize = minCodeSize + 1
    var i = 0
    while (i < data.size) {
        val v = data(i) & 0xFF
        writeCode(v)
        writeCode(clearCode)
        codeSize = minCodeSize + 1
        i += 1
    }
    writeCode(endCode)
    if (bitCount > 0) out.append((bitBuffer & 0xFF).toByte)
    out
}

def __pytra_save_gif(path: Any, width: Any, height: Any, frames: Any, palette: Any, delayCsArg: Any = 4L, loopArg: Any = 0L): Unit = {
    val w = __pytra_int(width).toInt
    val h = __pytra_int(height).toInt
    val delayCs = __pytra_int(delayCsArg).toInt
    val loop = __pytra_int(loopArg).toInt
    val paletteBytes = __pytra_to_byte_buffer(palette)
    if (paletteBytes.size != 256 * 3) {
        throw new RuntimeException("palette must be 256*3 bytes")
    }
    val frameItems = __pytra_as_list(frames)
    val out = mutable.ArrayBuffer[Byte]('G'.toByte, 'I'.toByte, 'F'.toByte, '8'.toByte, '9'.toByte, 'a'.toByte)
    __pytra_append_u16le(out, w)
    __pytra_append_u16le(out, h)
    out.append(0xF7.toByte)
    out.append(0.toByte)
    out.append(0.toByte)
    out ++= paletteBytes
    out.append(0x21.toByte)
    out.append(0xFF.toByte)
    out.append(0x0B.toByte)
    out ++= mutable.ArrayBuffer[Byte]('N'.toByte, 'E'.toByte, 'T'.toByte, 'S'.toByte, 'C'.toByte, 'A'.toByte, 'P'.toByte, 'E'.toByte, '2'.toByte, '.'.toByte, '0'.toByte)
    out.append(0x03.toByte)
    out.append(0x01.toByte)
    __pytra_append_u16le(out, loop)
    out.append(0.toByte)
    var i = 0
    while (i < frameItems.size) {
        val fr = __pytra_to_byte_buffer(frameItems(i))
        if (fr.size != w * h) {
            throw new RuntimeException("frame size mismatch")
        }
        out.append(0x21.toByte)
        out.append(0xF9.toByte)
        out.append(0x04.toByte)
        out.append(0x00.toByte)
        __pytra_append_u16le(out, delayCs)
        out.append(0x00.toByte)
        out.append(0x00.toByte)
        out.append(0x2C.toByte)
        __pytra_append_u16le(out, 0)
        __pytra_append_u16le(out, 0)
        __pytra_append_u16le(out, w)
        __pytra_append_u16le(out, h)
        out.append(0x00.toByte)
        out.append(8.toByte)
        val compressed = __pytra_gif_lzw_encode(fr, 8)
        var pos = 0
        while (pos < compressed.size) {
            val remain = compressed.size - pos
            val chunkLen = if (remain > 255) 255 else remain
            out.append(chunkLen.toByte)
            var j = 0
            while (j < chunkLen) {
                out.append(compressed(pos + j))
                j += 1
            }
            pos += chunkLen
        }
        out.append(0.toByte)
        i += 1
    }
    out.append(0x3B.toByte)
    __pytra_write_file_bytes(path, out)
}

def __pytra_any_default(): Any = {
    0L
}

def __pytra_perf_counter(): Double = {
    System.nanoTime().toDouble / 1_000_000_000.0
}

def __pytra_int(v: Any): Long = {
    if (v == null) return 0L
    v match {
        case l: Long => l
        case i: Int => i.toLong
        case d: Double => d.toLong
        case f: Float => f.toLong
        case b: Boolean => if (b) 1L else 0L
        case s: String =>
            try s.toLong
            catch { case _: NumberFormatException => 0L }
        case _ => 0L
    }
}

def __pytra_str(v: Any): String = {
    if (v == null) return "None"
    v match {
        case b: Boolean => if (b) "True" else "False"
        case _ => v.toString
    }
}

def __pytra_len(v: Any): Long = {
    if (v == null) return 0L
    v match {
        case s: String => s.length.toLong
        case xs: scala.collection.Seq[?] => xs.size.toLong
        case m: scala.collection.Map[?, ?] => m.size.toLong
        case _ => 0L
    }
}

def __pytra_index(i: Long, n: Long): Long = {
    if (i < 0L) i + n else i
}

def __pytra_get_index(container: Any, index: Any): Any = {
    container match {
        case s: String =>
            if (s.isEmpty) return ""
            val i = __pytra_index(__pytra_int(index), s.length.toLong)
            if (i < 0L || i >= s.length.toLong) return ""
            s.charAt(i.toInt).toString
        case m: mutable.LinkedHashMap[?, ?] =>
            m.asInstanceOf[mutable.LinkedHashMap[Any, Any]].getOrElse(__pytra_str(index), __pytra_any_default())
        case m: scala.collection.Map[?, ?] =>
            m.asInstanceOf[scala.collection.Map[Any, Any]].getOrElse(__pytra_str(index), __pytra_any_default())
        case _ =>
            val list = __pytra_as_list(container)
            if (list.nonEmpty) {
                val i = __pytra_index(__pytra_int(index), list.size.toLong)
                if (i >= 0L && i < list.size.toLong) return list(i.toInt)
            }
            __pytra_any_default()
    }
}

def __pytra_set_index(container: Any, index: Any, value: Any): Unit = {
    container match {
        case m: mutable.LinkedHashMap[?, ?] =>
            m.asInstanceOf[mutable.LinkedHashMap[Any, Any]](__pytra_str(index)) = value
            return
        case m: scala.collection.mutable.Map[?, ?] =>
            m.asInstanceOf[scala.collection.mutable.Map[Any, Any]](__pytra_str(index)) = value
            return
        case _ =>
    }
    val list = __pytra_as_list(container)
    if (list.nonEmpty) {
        val i = __pytra_index(__pytra_int(index), list.size.toLong)
        if (i >= 0L && i < list.size.toLong) list(i.toInt) = value
        return
    }
    val map = __pytra_as_dict(container)
    map(__pytra_str(index)) = value
}

def __pytra_ifexp(cond: Boolean, a: Any, b: Any): Any = {
    if (cond) a else b
}

def __pytra_bytearray(initValue: Any): mutable.ArrayBuffer[Any] = {
    initValue match {
        case n: Long =>
            val out = mutable.ArrayBuffer[Any]()
            var i = 0L
            while (i < n) {
                out.append(0L)
                i += 1L
            }
            out
        case n: Int =>
            val out = mutable.ArrayBuffer[Any]()
            var i = 0
            while (i < n) {
                out.append(0L)
                i += 1
            }
            out
        case _ => __pytra_as_list(initValue).clone()
    }
}

def __pytra_bytes(v: Any): mutable.ArrayBuffer[Any] = {
    __pytra_as_list(v).clone()
}

def __pytra_list_repeat(value: Any, count: Any): mutable.ArrayBuffer[Any] = {
    val out = mutable.ArrayBuffer[Any]()
    val n = __pytra_int(count)
    var i = 0L
    while (i < n) {
        out.append(value)
        i += 1L
    }
    out
}

def __pytra_as_list(v: Any): mutable.ArrayBuffer[Any] = {
    v match {
        case xs: mutable.ArrayBuffer[?] => xs.asInstanceOf[mutable.ArrayBuffer[Any]]
        case xs: scala.collection.Seq[?] =>
            val out = mutable.ArrayBuffer[Any]()
            for (item <- xs) out.append(item)
            out
        case _ => mutable.ArrayBuffer[Any]()
    }
}

def __pytra_as_dict(v: Any): mutable.LinkedHashMap[Any, Any] = {
    v match {
        case m: mutable.LinkedHashMap[?, ?] => m.asInstanceOf[mutable.LinkedHashMap[Any, Any]]
        case m: scala.collection.Map[?, ?] =>
            val out = mutable.LinkedHashMap[Any, Any]()
            for ((k, valueAny) <- m) {
                if (k != null) out(k) = valueAny
            }
            out
        case _ => mutable.LinkedHashMap[Any, Any]()
    }
}

def __pytra_pop_last(v: mutable.ArrayBuffer[Any]): mutable.ArrayBuffer[Any] = {
    if (v.nonEmpty) v.remove(v.size - 1)
    v
}

def __pytra_print(args: Any*): Unit = {
    if (args.isEmpty) {
        println()
        return
    }
    println(args.map(__pytra_str).mkString(" "))
}


// 13: Sample that outputs DFS maze-generation progress as a GIF.

def capture(grid: mutable.ArrayBuffer[Any], w: Long, h: Long, scale: Long): mutable.ArrayBuffer[Any] = {
    var width: Long = (w * scale)
    var height: Long = (h * scale)
    var frame: mutable.ArrayBuffer[Any] = __pytra_as_list(__pytra_bytearray((width * height)))
    var y: Long = __pytra_int(0L)
    boundary:
        given __breakLabel_0: boundary.Label[Unit] = summon[boundary.Label[Unit]]
        while (y < __pytra_int(h)) {
            boundary:
                given __continueLabel_1: boundary.Label[Unit] = summon[boundary.Label[Unit]]
                var x: Long = __pytra_int(0L)
                boundary:
                    given __breakLabel_3: boundary.Label[Unit] = summon[boundary.Label[Unit]]
                    while (x < __pytra_int(w)) {
                        boundary:
                            given __continueLabel_4: boundary.Label[Unit] = summon[boundary.Label[Unit]]
                            var v: Long = __pytra_int(__pytra_ifexp((__pytra_int(__pytra_get_index(__pytra_as_list(__pytra_get_index(grid, y)), x)) == 0L), 255L, 40L))
                            var yy: Long = __pytra_int(0L)
                            boundary:
                                given __breakLabel_6: boundary.Label[Unit] = summon[boundary.Label[Unit]]
                                while (yy < __pytra_int(scale)) {
                                    boundary:
                                        given __continueLabel_7: boundary.Label[Unit] = summon[boundary.Label[Unit]]
                                        var base: Long = ((((y * scale) + yy) * width) + (x * scale))
                                        var xx: Long = __pytra_int(0L)
                                        boundary:
                                            given __breakLabel_9: boundary.Label[Unit] = summon[boundary.Label[Unit]]
                                            while (xx < __pytra_int(scale)) {
                                                boundary:
                                                    given __continueLabel_10: boundary.Label[Unit] = summon[boundary.Label[Unit]]
                                                    __pytra_set_index(frame, (base + xx), v)
                                                xx += 1L
                                            }
                                    yy += 1L
                                }
                        x += 1L
                    }
            y += 1L
        }
    return __pytra_as_list(__pytra_bytes(frame))
}

def run_13_maze_generation_steps(): Unit = {
    var cell_w: Long = 89L
    var cell_h: Long = 67L
    var scale: Long = 5L
    var capture_every: Long = 20L
    var out_path: String = "sample/out/13_maze_generation_steps.gif"
    var start: Double = __pytra_perf_counter()
    var grid: mutable.ArrayBuffer[Any] = __pytra_as_list({ val __out = mutable.ArrayBuffer[Any](); val __step = __pytra_int(1L); var i = __pytra_int(0L); while ((__step >= 0L && i < __pytra_int(cell_h)) || (__step < 0L && i > __pytra_int(cell_h))) { __out.append(__pytra_list_repeat(1L, cell_w)); i += __step }; __out })
    var stack: mutable.ArrayBuffer[Any] = __pytra_as_list(mutable.ArrayBuffer[Any](mutable.ArrayBuffer[Any](1L, 1L)))
    __pytra_set_index(__pytra_as_list(__pytra_get_index(grid, 1L)), 1L, 0L)
    var dirs: mutable.ArrayBuffer[Any] = __pytra_as_list(mutable.ArrayBuffer[Any](mutable.ArrayBuffer[Any](2L, 0L), mutable.ArrayBuffer[Any]((-2L), 0L), mutable.ArrayBuffer[Any](0L, 2L), mutable.ArrayBuffer[Any](0L, (-2L))))
    var frames: mutable.ArrayBuffer[Any] = __pytra_as_list(mutable.ArrayBuffer[Any]())
    var step: Long = 0L
    boundary:
        given __breakLabel_0: boundary.Label[Unit] = summon[boundary.Label[Unit]]
        while ((__pytra_len(stack) != 0L)) {
            boundary:
                given __continueLabel_1: boundary.Label[Unit] = summon[boundary.Label[Unit]]
                val __tuple_2 = __pytra_as_list(__pytra_as_list(__pytra_get_index(stack, (-1L))))
                var x: Long = __pytra_int(__tuple_2(0))
                var y: Long = __pytra_int(__tuple_2(1))
                var candidates: mutable.ArrayBuffer[Any] = __pytra_as_list(mutable.ArrayBuffer[Any]())
                var k: Long = __pytra_int(0L)
                boundary:
                    given __breakLabel_3: boundary.Label[Unit] = summon[boundary.Label[Unit]]
                    while (k < __pytra_int(4L)) {
                        boundary:
                            given __continueLabel_4: boundary.Label[Unit] = summon[boundary.Label[Unit]]
                            val __tuple_6 = __pytra_as_list(__pytra_as_list(__pytra_get_index(dirs, k)))
                            var dx: Long = __pytra_int(__tuple_6(0))
                            var dy: Long = __pytra_int(__tuple_6(1))
                            var nx: Long = __pytra_int(x + dx)
                            var ny: Long = __pytra_int(y + dy)
                            if (((__pytra_int(nx) >= 1L) && (__pytra_int(nx) < (cell_w - 1L)) && (__pytra_int(ny) >= 1L) && (__pytra_int(ny) < (cell_h - 1L)) && (__pytra_int(__pytra_get_index(__pytra_as_list(__pytra_get_index(grid, ny)), nx)) == 1L))) {
                                if ((__pytra_int(dx) == 2L)) {
                                    candidates.append(mutable.ArrayBuffer[Any](nx, ny, (x + 1L), y))
                                } else {
                                    if ((__pytra_int(dx) == (-2L))) {
                                        candidates.append(mutable.ArrayBuffer[Any](nx, ny, (x - 1L), y))
                                    } else {
                                        if ((__pytra_int(dy) == 2L)) {
                                            candidates.append(mutable.ArrayBuffer[Any](nx, ny, x, (y + 1L)))
                                        } else {
                                            candidates.append(mutable.ArrayBuffer[Any](nx, ny, x, (y - 1L)))
                                        }
                                    }
                                }
                            }
                        k += 1L
                    }
                if ((__pytra_len(candidates) == 0L)) {
                    stack = __pytra_pop_last(__pytra_as_list(stack))
                } else {
                    var sel: mutable.ArrayBuffer[Any] = __pytra_as_list(__pytra_get_index(candidates, (__pytra_int(((x * 17L) + (y * 29L)) + (__pytra_len(stack) * 13L)) % __pytra_len(candidates))))
                    val __tuple_7 = __pytra_as_list(sel)
                    var nx: Long = __pytra_int(__tuple_7(0))
                    var ny: Long = __pytra_int(__tuple_7(1))
                    var wx: Long = __pytra_int(__tuple_7(2))
                    var wy: Long = __pytra_int(__tuple_7(3))
                    __pytra_set_index(__pytra_as_list(__pytra_get_index(grid, wy)), wx, 0L)
                    __pytra_set_index(__pytra_as_list(__pytra_get_index(grid, ny)), nx, 0L)
                    stack.append(mutable.ArrayBuffer[Any](nx, ny))
                }
                if (((step % capture_every) == 0L)) {
                    frames.append(capture(grid, cell_w, cell_h, scale))
                }
                step += 1L
        }
    frames.append(capture(grid, cell_w, cell_h, scale))
    __pytra_save_gif(out_path, (cell_w * scale), (cell_h * scale), frames, __pytra_grayscale_palette())
    var elapsed: Double = (__pytra_perf_counter() - start)
    __pytra_print("output:", out_path)
    __pytra_print("frames:", __pytra_len(frames))
    __pytra_print("elapsed_sec:", elapsed)
}

def main(args: Array[String]): Unit = {
    run_13_maze_generation_steps()
}
