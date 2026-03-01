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

def __pytra_float(v: Any): Double = {
    if (v == null) return 0.0
    v match {
        case d: Double => d
        case f: Float => f.toDouble
        case l: Long => l.toDouble
        case i: Int => i.toDouble
        case b: Boolean => if (b) 1.0 else 0.0
        case s: String =>
            try s.toDouble
            catch { case _: NumberFormatException => 0.0 }
        case _ => 0.0
    }
}

def __pytra_str(v: Any): String = {
    if (v == null) return "None"
    v match {
        case b: Boolean => if (b) "True" else "False"
        case _ => v.toString
    }
}

def __pytra_index(i: Long, n: Long): Long = {
    if (i < 0L) i + n else i
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


// 06: Sample that sweeps Julia-set parameters and outputs a GIF.

def julia_palette(): mutable.ArrayBuffer[Any] = {
    var palette: mutable.ArrayBuffer[Any] = __pytra_as_list(__pytra_bytearray((256L * 3L)))
    __pytra_set_index(palette, 0L, 0L)
    __pytra_set_index(palette, 1L, 0L)
    __pytra_set_index(palette, 2L, 0L)
    var i: Long = __pytra_int(1L)
    boundary:
        given __breakLabel_0: boundary.Label[Unit] = summon[boundary.Label[Unit]]
        while (i < __pytra_int(256L)) {
            boundary:
                given __continueLabel_1: boundary.Label[Unit] = summon[boundary.Label[Unit]]
                var t: Double = (__pytra_float(i - 1L) / 254.0)
                var r: Long = __pytra_int(255.0 * ((((9.0 * (1.0 - t)) * t) * t) * t))
                var g: Long = __pytra_int(255.0 * ((((15.0 * (1.0 - t)) * (1.0 - t)) * t) * t))
                var b: Long = __pytra_int(255.0 * ((((8.5 * (1.0 - t)) * (1.0 - t)) * (1.0 - t)) * t))
                __pytra_set_index(palette, ((i * 3L) + 0L), r)
                __pytra_set_index(palette, ((i * 3L) + 1L), g)
                __pytra_set_index(palette, ((i * 3L) + 2L), b)
            i += 1L
        }
    return __pytra_as_list(__pytra_bytes(palette))
}

def render_frame(width: Long, height: Long, cr: Double, ci: Double, max_iter: Long, phase: Long): mutable.ArrayBuffer[Any] = {
    var frame: mutable.ArrayBuffer[Any] = __pytra_as_list(__pytra_bytearray((width * height)))
    var __hoisted_cast_1: Double = __pytra_float(height - 1L)
    var __hoisted_cast_2: Double = __pytra_float(width - 1L)
    var y: Long = __pytra_int(0L)
    boundary:
        given __breakLabel_0: boundary.Label[Unit] = summon[boundary.Label[Unit]]
        while (y < __pytra_int(height)) {
            boundary:
                given __continueLabel_1: boundary.Label[Unit] = summon[boundary.Label[Unit]]
                var row_base: Long = (y * width)
                var zy0: Double = ((-1.2) + (2.4 * (__pytra_float(y) / __hoisted_cast_1)))
                var x: Long = __pytra_int(0L)
                boundary:
                    given __breakLabel_3: boundary.Label[Unit] = summon[boundary.Label[Unit]]
                    while (x < __pytra_int(width)) {
                        boundary:
                            given __continueLabel_4: boundary.Label[Unit] = summon[boundary.Label[Unit]]
                            var zx: Double = ((-1.8) + (3.6 * (__pytra_float(x) / __hoisted_cast_2)))
                            var zy: Double = zy0
                            var i: Long = 0L
                            boundary:
                                given __breakLabel_6: boundary.Label[Unit] = summon[boundary.Label[Unit]]
                                while ((i < max_iter)) {
                                    boundary:
                                        given __continueLabel_7: boundary.Label[Unit] = summon[boundary.Label[Unit]]
                                        var zx2: Double = (zx * zx)
                                        var zy2: Double = (zy * zy)
                                        if (((zx2 + zy2) > 4.0)) {
                                            break(())(using __breakLabel_6)
                                        }
                                        zy = (((2.0 * zx) * zy) + ci)
                                        zx = ((zx2 - zy2) + cr)
                                        i += 1L
                                }
                            if ((i >= max_iter)) {
                                __pytra_set_index(frame, (row_base + x), 0L)
                            } else {
                                var color_index: Long = (1L + (((__pytra_int((i * 224L) / max_iter)) + phase) % 255L))
                                __pytra_set_index(frame, (row_base + x), color_index)
                            }
                        x += 1L
                    }
            y += 1L
        }
    return __pytra_as_list(__pytra_bytes(frame))
}

def run_06_julia_parameter_sweep(): Unit = {
    var width: Long = 320L
    var height: Long = 240L
    var frames_n: Long = 72L
    var max_iter: Long = 180L
    var out_path: String = "sample/out/06_julia_parameter_sweep.gif"
    var start: Double = __pytra_perf_counter()
    var frames: mutable.ArrayBuffer[Any] = __pytra_as_list(mutable.ArrayBuffer[Any]())
    var center_cr: Double = __pytra_float(-0.745)
    var center_ci: Double = 0.186
    var radius_cr: Double = 0.12
    var radius_ci: Double = 0.1
    var start_offset: Long = 20L
    var phase_offset: Long = 180L
    var __hoisted_cast_3: Double = __pytra_float(frames_n)
    var i: Long = __pytra_int(0L)
    boundary:
        given __breakLabel_0: boundary.Label[Unit] = summon[boundary.Label[Unit]]
        while (i < __pytra_int(frames_n)) {
            boundary:
                given __continueLabel_1: boundary.Label[Unit] = summon[boundary.Label[Unit]]
                var t: Double = (__pytra_float((i + start_offset) % frames_n) / __hoisted_cast_3)
                var angle: Double = __pytra_float((2.0 * Math.PI) * t)
                var cr: Double = __pytra_float(center_cr + (radius_cr * scala.math.cos(__pytra_float(angle))))
                var ci: Double = __pytra_float(center_ci + (radius_ci * scala.math.sin(__pytra_float(angle))))
                var phase: Long = ((phase_offset + (i * 5L)) % 255L)
                frames.append(render_frame(width, height, cr, ci, max_iter, phase))
            i += 1L
        }
    __pytra_save_gif(out_path, width, height, frames, julia_palette())
    var elapsed: Double = (__pytra_perf_counter() - start)
    __pytra_print("output:", out_path)
    __pytra_print("frames:", frames_n)
    __pytra_print("elapsed_sec:", elapsed)
}

def main(args: Array[String]): Unit = {
    run_06_julia_parameter_sweep()
}
