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

def __pytra_print(args: Any*): Unit = {
    if (args.isEmpty) {
        println()
        return
    }
    println(args.map(__pytra_str).mkString(" "))
}


// 07: Sample that outputs Game of Life evolution as a GIF.

def next_state(grid: mutable.ArrayBuffer[Any], w: Long, h: Long): mutable.ArrayBuffer[Any] = {
    var nxt: mutable.ArrayBuffer[Any] = __pytra_as_list(mutable.ArrayBuffer[Any]())
    var y: Long = __pytra_int(0L)
    boundary:
        given __breakLabel_0: boundary.Label[Unit] = summon[boundary.Label[Unit]]
        while (y < __pytra_int(h)) {
            boundary:
                given __continueLabel_1: boundary.Label[Unit] = summon[boundary.Label[Unit]]
                var row: mutable.ArrayBuffer[Any] = __pytra_as_list(mutable.ArrayBuffer[Any]())
                var x: Long = __pytra_int(0L)
                boundary:
                    given __breakLabel_3: boundary.Label[Unit] = summon[boundary.Label[Unit]]
                    while (x < __pytra_int(w)) {
                        boundary:
                            given __continueLabel_4: boundary.Label[Unit] = summon[boundary.Label[Unit]]
                            var cnt: Long = 0L
                            var dy: Long = __pytra_int(-1L)
                            boundary:
                                given __breakLabel_6: boundary.Label[Unit] = summon[boundary.Label[Unit]]
                                while (dy < __pytra_int(2L)) {
                                    boundary:
                                        given __continueLabel_7: boundary.Label[Unit] = summon[boundary.Label[Unit]]
                                        var dx: Long = __pytra_int(-1L)
                                        boundary:
                                            given __breakLabel_9: boundary.Label[Unit] = summon[boundary.Label[Unit]]
                                            while (dx < __pytra_int(2L)) {
                                                boundary:
                                                    given __continueLabel_10: boundary.Label[Unit] = summon[boundary.Label[Unit]]
                                                    if (((dx != 0L) || (dy != 0L))) {
                                                        var nx: Long = (((x + dx) + w) % w)
                                                        var ny: Long = (((y + dy) + h) % h)
                                                        cnt += __pytra_int(__pytra_get_index(__pytra_as_list(__pytra_get_index(grid, ny)), nx))
                                                    }
                                                dx += 1L
                                            }
                                    dy += 1L
                                }
                            var alive: Long = __pytra_int(__pytra_get_index(__pytra_as_list(__pytra_get_index(grid, y)), x))
                            if (((alive == 1L) && ((cnt == 2L) || (cnt == 3L)))) {
                                row.append(1L)
                            } else {
                                if (((alive == 0L) && (cnt == 3L))) {
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

def render(grid: mutable.ArrayBuffer[Any], w: Long, h: Long, cell: Long): mutable.ArrayBuffer[Any] = {
    var width: Long = (w * cell)
    var height: Long = (h * cell)
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
                            var v: Long = __pytra_int(__pytra_ifexp((__pytra_int(__pytra_get_index(__pytra_as_list(__pytra_get_index(grid, y)), x)) != 0L), 255L, 0L))
                            var yy: Long = __pytra_int(0L)
                            boundary:
                                given __breakLabel_6: boundary.Label[Unit] = summon[boundary.Label[Unit]]
                                while (yy < __pytra_int(cell)) {
                                    boundary:
                                        given __continueLabel_7: boundary.Label[Unit] = summon[boundary.Label[Unit]]
                                        var base: Long = ((((y * cell) + yy) * width) + (x * cell))
                                        var xx: Long = __pytra_int(0L)
                                        boundary:
                                            given __breakLabel_9: boundary.Label[Unit] = summon[boundary.Label[Unit]]
                                            while (xx < __pytra_int(cell)) {
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

def run_07_game_of_life_loop(): Unit = {
    var w: Long = 144L
    var h: Long = 108L
    var cell: Long = 4L
    var steps: Long = 105L
    var out_path: String = "sample/out/07_game_of_life_loop.gif"
    var start: Double = __pytra_perf_counter()
    var grid: mutable.ArrayBuffer[Any] = __pytra_as_list({ val __out = mutable.ArrayBuffer[Any](); val __step = __pytra_int(1L); var i = __pytra_int(0L); while ((__step >= 0L && i < __pytra_int(h)) || (__step < 0L && i > __pytra_int(h))) { __out.append(__pytra_list_repeat(0L, w)); i += __step }; __out })
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
                            var noise: Long = (((((x * 37L) + (y * 73L)) + ((x * y) % 19L)) + ((x + y) % 11L)) % 97L)
                            if ((noise < 3L)) {
                                __pytra_set_index(__pytra_as_list(__pytra_get_index(grid, y)), x, 1L)
                            }
                        x += 1L
                    }
            y += 1L
        }
    var glider: mutable.ArrayBuffer[Any] = __pytra_as_list(mutable.ArrayBuffer[Any](mutable.ArrayBuffer[Any](0L, 1L, 0L), mutable.ArrayBuffer[Any](0L, 0L, 1L), mutable.ArrayBuffer[Any](1L, 1L, 1L)))
    var r_pentomino: mutable.ArrayBuffer[Any] = __pytra_as_list(mutable.ArrayBuffer[Any](mutable.ArrayBuffer[Any](0L, 1L, 1L), mutable.ArrayBuffer[Any](1L, 1L, 0L), mutable.ArrayBuffer[Any](0L, 1L, 0L)))
    var lwss: mutable.ArrayBuffer[Any] = __pytra_as_list(mutable.ArrayBuffer[Any](mutable.ArrayBuffer[Any](0L, 1L, 1L, 1L, 1L), mutable.ArrayBuffer[Any](1L, 0L, 0L, 0L, 1L), mutable.ArrayBuffer[Any](0L, 0L, 0L, 0L, 1L), mutable.ArrayBuffer[Any](1L, 0L, 0L, 1L, 0L)))
    var gy: Long = __pytra_int(8L)
    boundary:
        given __breakLabel_6: boundary.Label[Unit] = summon[boundary.Label[Unit]]
        val __step_8 = __pytra_int(18L)
        while ((__step_8 >= 0L && gy < __pytra_int(h - 8L)) || (__step_8 < 0L && gy > __pytra_int(h - 8L))) {
            boundary:
                given __continueLabel_7: boundary.Label[Unit] = summon[boundary.Label[Unit]]
                var gx: Long = __pytra_int(8L)
                boundary:
                    given __breakLabel_9: boundary.Label[Unit] = summon[boundary.Label[Unit]]
                    val __step_11 = __pytra_int(22L)
                    while ((__step_11 >= 0L && gx < __pytra_int(w - 8L)) || (__step_11 < 0L && gx > __pytra_int(w - 8L))) {
                        boundary:
                            given __continueLabel_10: boundary.Label[Unit] = summon[boundary.Label[Unit]]
                            var kind: Long = (((gx * 7L) + (gy * 11L)) % 3L)
                            if ((kind == 0L)) {
                                var ph: Long = __pytra_len(glider)
                                var py: Long = __pytra_int(0L)
                                boundary:
                                    given __breakLabel_12: boundary.Label[Unit] = summon[boundary.Label[Unit]]
                                    while (py < __pytra_int(ph)) {
                                        boundary:
                                            given __continueLabel_13: boundary.Label[Unit] = summon[boundary.Label[Unit]]
                                            var pw: Long = __pytra_len(__pytra_as_list(__pytra_get_index(glider, py)))
                                            var px: Long = __pytra_int(0L)
                                            boundary:
                                                given __breakLabel_15: boundary.Label[Unit] = summon[boundary.Label[Unit]]
                                                while (px < __pytra_int(pw)) {
                                                    boundary:
                                                        given __continueLabel_16: boundary.Label[Unit] = summon[boundary.Label[Unit]]
                                                        if ((__pytra_int(__pytra_get_index(__pytra_as_list(__pytra_get_index(glider, py)), px)) == 1L)) {
                                                            __pytra_set_index(__pytra_as_list(__pytra_get_index(grid, ((gy + py) % h))), ((gx + px) % w), 1L)
                                                        }
                                                    px += 1L
                                                }
                                        py += 1L
                                    }
                            } else {
                                if ((kind == 1L)) {
                                    var ph: Long = __pytra_len(r_pentomino)
                                    var py: Long = __pytra_int(0L)
                                    boundary:
                                        given __breakLabel_18: boundary.Label[Unit] = summon[boundary.Label[Unit]]
                                        while (py < __pytra_int(ph)) {
                                            boundary:
                                                given __continueLabel_19: boundary.Label[Unit] = summon[boundary.Label[Unit]]
                                                var pw: Long = __pytra_len(__pytra_as_list(__pytra_get_index(r_pentomino, py)))
                                                var px: Long = __pytra_int(0L)
                                                boundary:
                                                    given __breakLabel_21: boundary.Label[Unit] = summon[boundary.Label[Unit]]
                                                    while (px < __pytra_int(pw)) {
                                                        boundary:
                                                            given __continueLabel_22: boundary.Label[Unit] = summon[boundary.Label[Unit]]
                                                            if ((__pytra_int(__pytra_get_index(__pytra_as_list(__pytra_get_index(r_pentomino, py)), px)) == 1L)) {
                                                                __pytra_set_index(__pytra_as_list(__pytra_get_index(grid, ((gy + py) % h))), ((gx + px) % w), 1L)
                                                            }
                                                        px += 1L
                                                    }
                                            py += 1L
                                        }
                                } else {
                                    var ph: Long = __pytra_len(lwss)
                                    var py: Long = __pytra_int(0L)
                                    boundary:
                                        given __breakLabel_24: boundary.Label[Unit] = summon[boundary.Label[Unit]]
                                        while (py < __pytra_int(ph)) {
                                            boundary:
                                                given __continueLabel_25: boundary.Label[Unit] = summon[boundary.Label[Unit]]
                                                var pw: Long = __pytra_len(__pytra_as_list(__pytra_get_index(lwss, py)))
                                                var px: Long = __pytra_int(0L)
                                                boundary:
                                                    given __breakLabel_27: boundary.Label[Unit] = summon[boundary.Label[Unit]]
                                                    while (px < __pytra_int(pw)) {
                                                        boundary:
                                                            given __continueLabel_28: boundary.Label[Unit] = summon[boundary.Label[Unit]]
                                                            if ((__pytra_int(__pytra_get_index(__pytra_as_list(__pytra_get_index(lwss, py)), px)) == 1L)) {
                                                                __pytra_set_index(__pytra_as_list(__pytra_get_index(grid, ((gy + py) % h))), ((gx + px) % w), 1L)
                                                            }
                                                        px += 1L
                                                    }
                                            py += 1L
                                        }
                                }
                            }
                        gx += __step_11
                    }
            gy += __step_8
        }
    var frames: mutable.ArrayBuffer[Any] = __pytra_as_list(mutable.ArrayBuffer[Any]())
    var i: Long = __pytra_int(0L)
    boundary:
        given __breakLabel_30: boundary.Label[Unit] = summon[boundary.Label[Unit]]
        while (i < __pytra_int(steps)) {
            boundary:
                given __continueLabel_31: boundary.Label[Unit] = summon[boundary.Label[Unit]]
                frames.append(render(grid, w, h, cell))
                grid = __pytra_as_list(next_state(grid, w, h))
            i += 1L
        }
    __pytra_save_gif(out_path, (w * cell), (h * cell), frames, __pytra_grayscale_palette())
    var elapsed: Double = (__pytra_perf_counter() - start)
    __pytra_print("output:", out_path)
    __pytra_print("frames:", steps)
    __pytra_print("elapsed_sec:", elapsed)
}

def main(args: Array[String]): Unit = {
    run_07_game_of_life_loop()
}
