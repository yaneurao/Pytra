// Auto-generated Pytra Scala 3 native source from EAST3.
import scala.collection.mutable
import scala.util.boundary, boundary.break
import scala.math.*
import java.nio.file.{Files, Paths}

def __pytra_noop(args: Any*): Unit = { }

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

def __pytra_append_u32be(out: mutable.ArrayBuffer[Byte], value: Int): Unit = {
    out.append(((value >>> 24) & 0xFF).toByte)
    out.append(((value >>> 16) & 0xFF).toByte)
    out.append(((value >>> 8) & 0xFF).toByte)
    out.append((value & 0xFF).toByte)
}

def __pytra_crc32(data: mutable.ArrayBuffer[Byte]): Int = {
    var crc = 0xFFFFFFFFL
    val poly = 0xEDB88320L
    var i = 0
    while (i < data.size) {
        crc ^= (data(i) & 0xFF).toLong
        var j = 0
        while (j < 8) {
            if ((crc & 1L) != 0L) crc = (crc >>> 1) ^ poly
            else crc = crc >>> 1
            j += 1
        }
        i += 1
    }
    (crc ^ 0xFFFFFFFFL).toInt
}

def __pytra_adler32(data: mutable.ArrayBuffer[Byte]): Int = {
    val mod = 65521
    var s1 = 1
    var s2 = 0
    var i = 0
    while (i < data.size) {
        s1 += (data(i) & 0xFF)
        if (s1 >= mod) s1 -= mod
        s2 += s1
        s2 %= mod
        i += 1
    }
    ((s2 << 16) | s1) & 0xFFFFFFFF
}

def __pytra_zlib_deflate_store(data: mutable.ArrayBuffer[Byte]): mutable.ArrayBuffer[Byte] = {
    val out = mutable.ArrayBuffer[Byte](0x78.toByte, 0x01.toByte)
    val n = data.size
    var pos = 0
    while (pos < n) {
        val remain = n - pos
        val chunkLen = if (remain > 65535) 65535 else remain
        val finalFlag = if ((pos + chunkLen) >= n) 1 else 0
        out.append(finalFlag.toByte)
        __pytra_append_u16le(out, chunkLen)
        __pytra_append_u16le(out, 0xFFFF ^ chunkLen)
        var i = 0
        while (i < chunkLen) {
            out.append(data(pos + i))
            i += 1
        }
        pos += chunkLen
    }
    __pytra_append_u32be(out, __pytra_adler32(data))
    out
}

def __pytra_png_chunk(chunkType: String, data: mutable.ArrayBuffer[Byte]): mutable.ArrayBuffer[Byte] = {
    val out = mutable.ArrayBuffer[Byte]()
    __pytra_append_u32be(out, data.size)
    val ct = chunkType.getBytes("US-ASCII")
    val crcData = mutable.ArrayBuffer[Byte]()
    var i = 0
    while (i < ct.length) {
        out.append(ct(i))
        crcData.append(ct(i))
        i += 1
    }
    i = 0
    while (i < data.size) {
        out.append(data(i))
        crcData.append(data(i))
        i += 1
    }
    __pytra_append_u32be(out, __pytra_crc32(crcData))
    out
}

def __pytra_write_file_bytes(path: Any, data: mutable.ArrayBuffer[Byte]): Unit = {
    val p = Paths.get(__pytra_str(path))
    val parent = p.getParent
    if (parent != null) Files.createDirectories(parent)
    Files.write(p, data.toArray)
}

def __pytra_path_new(path: Any): String = {
    Paths.get(__pytra_str(path)).toString
}

def __pytra_path_join(base: Any, child: Any): String = {
    Paths.get(__pytra_str(base)).resolve(__pytra_str(child)).toString
}

def __pytra_path_parent(path: Any): String = {
    val parent = Paths.get(__pytra_str(path)).getParent
    if (parent == null) "" else parent.toString
}

def __pytra_path_name(path: Any): String = {
    val name = Paths.get(__pytra_str(path)).getFileName
    if (name == null) "" else name.toString
}

def __pytra_path_stem(path: Any): String = {
    val name = __pytra_path_name(path)
    val idx = name.lastIndexOf('.')
    if (idx <= 0) name else name.substring(0, idx)
}

def __pytra_path_exists(path: Any): Boolean = {
    Files.exists(Paths.get(__pytra_str(path)))
}

def __pytra_path_mkdir(path: Any): Unit = {
    Files.createDirectories(Paths.get(__pytra_str(path)))
}

def __pytra_path_write_text(path: Any, text: Any): Unit = {
    val p = Paths.get(__pytra_str(path))
    val parent = p.getParent
    if (parent != null) Files.createDirectories(parent)
    Files.writeString(p, __pytra_str(text))
}

def __pytra_path_read_text(path: Any): String = {
    Files.readString(Paths.get(__pytra_str(path)))
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

def __pytra_write_rgb_png(path: Any, width: Any, height: Any, pixels: Any): Unit = {
    val w = __pytra_int(width).toInt
    val h = __pytra_int(height).toInt
    val raw = __pytra_to_byte_buffer(pixels)
    val expected = w * h * 3
    if (raw.size != expected) {
        throw new RuntimeException("pixels length mismatch")
    }
    val scanlines = mutable.ArrayBuffer[Byte]()
    val rowBytes = w * 3
    var y = 0
    while (y < h) {
        scanlines.append(0.toByte)
        val start = y * rowBytes
        var x = 0
        while (x < rowBytes) {
            scanlines.append(raw(start + x))
            x += 1
        }
        y += 1
    }
    val ihdr = mutable.ArrayBuffer[Byte]()
    __pytra_append_u32be(ihdr, w)
    __pytra_append_u32be(ihdr, h)
    ihdr.append(8.toByte)
    ihdr.append(2.toByte)
    ihdr.append(0.toByte)
    ihdr.append(0.toByte)
    ihdr.append(0.toByte)
    val idat = __pytra_zlib_deflate_store(scanlines)
    val png = mutable.ArrayBuffer[Byte](0x89.toByte, 'P'.toByte, 'N'.toByte, 'G'.toByte, 0x0D.toByte, 0x0A.toByte, 0x1A.toByte, 0x0A.toByte)
    png ++= __pytra_png_chunk("IHDR", ihdr)
    png ++= __pytra_png_chunk("IDAT", idat)
    png ++= __pytra_png_chunk("IEND", mutable.ArrayBuffer[Byte]())
    __pytra_write_file_bytes(path, png)
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

def __pytra_assert(args: Any*): String = {
    "True"
}

def __pytra_perf_counter(): Double = {
    System.nanoTime().toDouble / 1_000_000_000.0
}

def __pytra_truthy(v: Any): Boolean = {
    if (v == null) return false
    v match {
        case b: Boolean => b
        case l: Long => l != 0L
        case i: Int => i != 0
        case d: Double => d != 0.0
        case f: Float => f != 0.0f
        case s: String => s.nonEmpty
        case xs: scala.collection.Seq[?] => xs.nonEmpty
        case m: scala.collection.Map[?, ?] => m.nonEmpty
        case _ => true
    }
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

def __pytra_slice(container: Any, lower: Any, upper: Any): Any = {
    container match {
        case s: String =>
            val n = s.length.toLong
            var lo = __pytra_index(__pytra_int(lower), n)
            var hi = __pytra_index(__pytra_int(upper), n)
            if (lo < 0L) lo = 0L
            if (hi < 0L) hi = 0L
            if (lo > n) lo = n
            if (hi > n) hi = n
            if (hi < lo) hi = lo
            s.substring(lo.toInt, hi.toInt)
        case _ =>
            val list = __pytra_as_list(container)
            val n = list.size.toLong
            var lo = __pytra_index(__pytra_int(lower), n)
            var hi = __pytra_index(__pytra_int(upper), n)
            if (lo < 0L) lo = 0L
            if (hi < 0L) hi = 0L
            if (lo > n) lo = n
            if (hi > n) hi = n
            if (hi < lo) hi = lo
            val out = mutable.ArrayBuffer[Any]()
            var i = lo
            while (i < hi) {
                out.append(list(i.toInt))
                i += 1L
            }
            out
    }
}

def __pytra_isdigit(v: Any): Boolean = {
    val s = __pytra_str(v)
    if (s.isEmpty) return false
    s.forall(_.isDigit)
}

def __pytra_isalpha(v: Any): Boolean = {
    val s = __pytra_str(v)
    if (s.isEmpty) return false
    s.forall(_.isLetter)
}

def __pytra_contains(container: Any, value: Any): Boolean = {
    val needle = __pytra_str(value)
    container match {
        case s: String => s.contains(needle)
        case m: scala.collection.Map[?, ?] => m.asInstanceOf[scala.collection.Map[Any, Any]].contains(needle)
        case _ =>
            val list = __pytra_as_list(container)
            var i = 0
            while (i < list.size) {
                if (__pytra_str(list(i)) == needle) return true
                i += 1
            }
            false
    }
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

def __pytra_enumerate(v: Any): mutable.ArrayBuffer[Any] = {
    val items = __pytra_as_list(v)
    val out = mutable.ArrayBuffer[Any]()
    var i = 0L
    while (i < items.size.toLong) {
        out.append(mutable.ArrayBuffer[Any](i, items(i.toInt)))
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

def __pytra_min(a: Any, b: Any): Any = {
    val af = __pytra_float(a)
    val bf = __pytra_float(b)
    if (af < bf) {
        if (__pytra_is_float(a) || __pytra_is_float(b)) return af
        return __pytra_int(a)
    }
    if (__pytra_is_float(a) || __pytra_is_float(b)) return bf
    __pytra_int(b)
}

def __pytra_max(a: Any, b: Any): Any = {
    val af = __pytra_float(a)
    val bf = __pytra_float(b)
    if (af > bf) {
        if (__pytra_is_float(a) || __pytra_is_float(b)) return af
        return __pytra_int(a)
    }
    if (__pytra_is_float(a) || __pytra_is_float(b)) return bf
    __pytra_int(b)
}

def __pytra_is_int(v: Any): Boolean = v.isInstanceOf[Long] || v.isInstanceOf[Int]

def __pytra_is_float(v: Any): Boolean = v.isInstanceOf[Double] || v.isInstanceOf[Float]

def __pytra_is_bool(v: Any): Boolean = v.isInstanceOf[Boolean]

def __pytra_is_str(v: Any): Boolean = v.isInstanceOf[String]

def __pytra_is_list(v: Any): Boolean = v.isInstanceOf[scala.collection.Seq[?]]

// 09: Sample that outputs a simple fire effect as a GIF.

def fire_palette(): mutable.ArrayBuffer[Any] = {
    var p: mutable.ArrayBuffer[Any] = __pytra_as_list(mutable.ArrayBuffer[Any]())
    var i: Long = __pytra_int(0L)
    boundary:
        given __breakLabel_0: boundary.Label[Unit] = summon[boundary.Label[Unit]]
        val __step_2 = __pytra_int(1L)
        while ((__step_2 >= 0L && i < __pytra_int(256L)) || (__step_2 < 0L && i > __pytra_int(256L))) {
            boundary:
                given __continueLabel_1: boundary.Label[Unit] = summon[boundary.Label[Unit]]
                var r: Long = __pytra_int(0L)
                var g: Long = __pytra_int(0L)
                var b: Long = __pytra_int(0L)
                if ((__pytra_int(i) < __pytra_int(85L))) {
                    r = __pytra_int((__pytra_int(i) * __pytra_int(3L)))
                    g = __pytra_int(0L)
                    b = __pytra_int(0L)
                } else {
                    if ((__pytra_int(i) < __pytra_int(170L))) {
                        r = __pytra_int(255L)
                        g = __pytra_int((__pytra_int((__pytra_int(i) - __pytra_int(85L))) * __pytra_int(3L)))
                        b = __pytra_int(0L)
                    } else {
                        r = __pytra_int(255L)
                        g = __pytra_int(255L)
                        b = __pytra_int((__pytra_int((__pytra_int(i) - __pytra_int(170L))) * __pytra_int(3L)))
                    }
                }
                p = __pytra_as_list(p); p.append(r)
                p = __pytra_as_list(p); p.append(g)
                p = __pytra_as_list(p); p.append(b)
            i += __step_2
        }
    return __pytra_as_list(__pytra_bytes(p))
}

def run_09_fire_simulation(): Unit = {
    var w: Long = __pytra_int(380L)
    var h: Long = __pytra_int(260L)
    var steps: Long = __pytra_int(420L)
    var out_path: String = __pytra_str("sample/out/09_fire_simulation.gif")
    var start: Double = __pytra_float(__pytra_perf_counter())
    var heat: mutable.ArrayBuffer[Any] = __pytra_as_list(({ val __out = mutable.ArrayBuffer[Any](); val __step = __pytra_int(1L); var i = __pytra_int(0L); while ((__step >= 0L && i < __pytra_int(h)) || (__step < 0L && i > __pytra_int(h))) { __out.append(__pytra_list_repeat(0L, w)); i += __step }; __out }))
    var frames: mutable.ArrayBuffer[Any] = __pytra_as_list(mutable.ArrayBuffer[Any]())
    var t: Long = __pytra_int(0L)
    boundary:
        given __breakLabel_0: boundary.Label[Unit] = summon[boundary.Label[Unit]]
        val __step_2 = __pytra_int(1L)
        while ((__step_2 >= 0L && t < __pytra_int(steps)) || (__step_2 < 0L && t > __pytra_int(steps))) {
            boundary:
                given __continueLabel_1: boundary.Label[Unit] = summon[boundary.Label[Unit]]
                var x: Long = __pytra_int(0L)
                boundary:
                    given __breakLabel_3: boundary.Label[Unit] = summon[boundary.Label[Unit]]
                    val __step_5 = __pytra_int(1L)
                    while ((__step_5 >= 0L && x < __pytra_int(w)) || (__step_5 < 0L && x > __pytra_int(w))) {
                        boundary:
                            given __continueLabel_4: boundary.Label[Unit] = summon[boundary.Label[Unit]]
                            var py_val: Long = __pytra_int((__pytra_int(170L) + __pytra_int((__pytra_int((__pytra_int((__pytra_int(x) * __pytra_int(13L))) + __pytra_int((__pytra_int(t) * __pytra_int(17L))))) % __pytra_int(86L)))))
                            __pytra_set_index(__pytra_as_list(__pytra_get_index(heat, (__pytra_int(h) - __pytra_int(1L)))), x, py_val)
                        x += __step_5
                    }
                var y: Long = __pytra_int(1L)
                boundary:
                    given __breakLabel_6: boundary.Label[Unit] = summon[boundary.Label[Unit]]
                    val __step_8 = __pytra_int(1L)
                    while ((__step_8 >= 0L && y < __pytra_int(h)) || (__step_8 < 0L && y > __pytra_int(h))) {
                        boundary:
                            given __continueLabel_7: boundary.Label[Unit] = summon[boundary.Label[Unit]]
                            x = __pytra_int(0L)
                            boundary:
                                given __breakLabel_9: boundary.Label[Unit] = summon[boundary.Label[Unit]]
                                val __step_11 = __pytra_int(1L)
                                while ((__step_11 >= 0L && x < __pytra_int(w)) || (__step_11 < 0L && x > __pytra_int(w))) {
                                    boundary:
                                        given __continueLabel_10: boundary.Label[Unit] = summon[boundary.Label[Unit]]
                                        var a: Long = __pytra_int(__pytra_int(__pytra_get_index(__pytra_as_list(__pytra_get_index(heat, y)), x)))
                                        var b: Long = __pytra_int(__pytra_int(__pytra_get_index(__pytra_as_list(__pytra_get_index(heat, y)), (__pytra_int((__pytra_int((__pytra_int(x) - __pytra_int(1L))) + __pytra_int(w))) % __pytra_int(w)))))
                                        var c: Long = __pytra_int(__pytra_int(__pytra_get_index(__pytra_as_list(__pytra_get_index(heat, y)), (__pytra_int((__pytra_int(x) + __pytra_int(1L))) % __pytra_int(w)))))
                                        var d: Long = __pytra_int(__pytra_int(__pytra_get_index(__pytra_as_list(__pytra_get_index(heat, (__pytra_int((__pytra_int(y) + __pytra_int(1L))) % __pytra_int(h)))), x)))
                                        var v: Long = __pytra_int((__pytra_int(__pytra_int((__pytra_int((__pytra_int((__pytra_int(a) + __pytra_int(b))) + __pytra_int(c))) + __pytra_int(d))) / __pytra_int(4L))))
                                        var cool: Long = __pytra_int((__pytra_int(1L) + __pytra_int((__pytra_int((__pytra_int((__pytra_int(x) + __pytra_int(y))) + __pytra_int(t))) % __pytra_int(3L)))))
                                        var nv: Long = __pytra_int((__pytra_int(v) - __pytra_int(cool)))
                                        __pytra_set_index(__pytra_as_list(__pytra_get_index(heat, (__pytra_int(y) - __pytra_int(1L)))), x, __pytra_ifexp((__pytra_int(nv) > __pytra_int(0L)), nv, 0L))
                                    x += __step_11
                                }
                        y += __step_8
                    }
                var frame: mutable.ArrayBuffer[Any] = __pytra_as_list(__pytra_bytearray((__pytra_int(w) * __pytra_int(h))))
                var yy: Long = __pytra_int(0L)
                boundary:
                    given __breakLabel_12: boundary.Label[Unit] = summon[boundary.Label[Unit]]
                    val __step_14 = __pytra_int(1L)
                    while ((__step_14 >= 0L && yy < __pytra_int(h)) || (__step_14 < 0L && yy > __pytra_int(h))) {
                        boundary:
                            given __continueLabel_13: boundary.Label[Unit] = summon[boundary.Label[Unit]]
                            var row_base: Long = __pytra_int((__pytra_int(yy) * __pytra_int(w)))
                            var xx: Long = __pytra_int(0L)
                            boundary:
                                given __breakLabel_15: boundary.Label[Unit] = summon[boundary.Label[Unit]]
                                val __step_17 = __pytra_int(1L)
                                while ((__step_17 >= 0L && xx < __pytra_int(w)) || (__step_17 < 0L && xx > __pytra_int(w))) {
                                    boundary:
                                        given __continueLabel_16: boundary.Label[Unit] = summon[boundary.Label[Unit]]
                                        __pytra_set_index(frame, (__pytra_int(row_base) + __pytra_int(xx)), __pytra_int(__pytra_get_index(__pytra_as_list(__pytra_get_index(heat, yy)), xx)))
                                    xx += __step_17
                                }
                        yy += __step_14
                    }
                frames = __pytra_as_list(frames); frames.append(__pytra_bytes(frame))
            t += __step_2
        }
    __pytra_save_gif(out_path, w, h, frames, fire_palette())
    var elapsed: Double = __pytra_float((__pytra_float(__pytra_perf_counter()) - __pytra_float(start)))
    __pytra_print("output:", out_path)
    __pytra_print("frames:", steps)
    __pytra_print("elapsed_sec:", elapsed)
}

def main(args: Array[String]): Unit = {
    run_09_fire_simulation()
}
