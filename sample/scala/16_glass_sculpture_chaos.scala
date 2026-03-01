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

// 16: Sample that ray-traces chaotic rotation of glass sculptures and outputs a GIF.

def clamp01(v: Double): Double = {
    if ((v < 0.0)) {
        return 0.0
    }
    if ((v > 1.0)) {
        return 1.0
    }
    return v
}

def dot(ax: Double, ay: Double, az: Double, bx: Double, by: Double, bz: Double): Double = {
    return (((ax * bx) + (ay * by)) + (az * bz))
}

def length(x: Double, y: Double, z: Double): Double = {
    return __pytra_float(scala.math.sqrt(__pytra_float(((x * x) + (y * y)) + (z * z))))
}

def normalize(x: Double, y: Double, z: Double): mutable.ArrayBuffer[Any] = {
    var l: Double = __pytra_float(length(x, y, z))
    if ((l < 1e-09)) {
        return __pytra_as_list(mutable.ArrayBuffer[Any](0.0, 0.0, 0.0))
    }
    return __pytra_as_list(mutable.ArrayBuffer[Any]((x / l), (y / l), (z / l)))
}

def reflect(ix: Double, iy: Double, iz: Double, nx: Double, ny: Double, nz: Double): mutable.ArrayBuffer[Any] = {
    var d: Double = (dot(ix, iy, iz, nx, ny, nz) * 2.0)
    return __pytra_as_list(mutable.ArrayBuffer[Any]((ix - (d * nx)), (iy - (d * ny)), (iz - (d * nz))))
}

def refract(ix: Double, iy: Double, iz: Double, nx: Double, ny: Double, nz: Double, eta: Double): mutable.ArrayBuffer[Any] = {
    var cosi: Double = __pytra_float(-dot(ix, iy, iz, nx, ny, nz))
    var sint2: Double = ((eta * eta) * (1.0 - (cosi * cosi)))
    if ((sint2 > 1.0)) {
        return __pytra_as_list(reflect(ix, iy, iz, nx, ny, nz))
    }
    var cost: Double = __pytra_float(scala.math.sqrt(__pytra_float(1.0 - sint2)))
    var k: Double = __pytra_float((eta * cosi) - cost)
    return __pytra_as_list(mutable.ArrayBuffer[Any](((eta * ix) + (k * nx)), ((eta * iy) + (k * ny)), ((eta * iz) + (k * nz))))
}

def schlick(cos_theta: Double, f0: Double): Double = {
    var m: Double = (1.0 - cos_theta)
    return (f0 + ((1.0 - f0) * ((((m * m) * m) * m) * m)))
}

def sky_color(dx: Double, dy: Double, dz: Double, tphase: Double): mutable.ArrayBuffer[Any] = {
    var t: Double = (0.5 * (dy + 1.0))
    var r: Double = (0.06 + (0.2 * t))
    var g: Double = (0.1 + (0.25 * t))
    var b: Double = (0.16 + (0.45 * t))
    var band: Double = __pytra_float(0.5 + (0.5 * scala.math.sin(__pytra_float(((8.0 * dx) + (6.0 * dz)) + tphase))))
    r += (0.08 * band)
    g += (0.05 * band)
    b += (0.12 * band)
    return __pytra_as_list(mutable.ArrayBuffer[Any](clamp01(r), clamp01(g), clamp01(b)))
}

def sphere_intersect(ox: Double, oy: Double, oz: Double, dx: Double, dy: Double, dz: Double, cx: Double, cy: Double, cz: Double, radius: Double): Double = {
    var lx: Double = (ox - cx)
    var ly: Double = (oy - cy)
    var lz: Double = (oz - cz)
    var b: Double = (((lx * dx) + (ly * dy)) + (lz * dz))
    var c: Double = ((((lx * lx) + (ly * ly)) + (lz * lz)) - (radius * radius))
    var h: Double = ((b * b) - c)
    if ((h < 0.0)) {
        return __pytra_float(-1.0)
    }
    var s: Double = __pytra_float(scala.math.sqrt(__pytra_float(h)))
    var t0: Double = __pytra_float((-b) - s)
    if ((__pytra_float(t0) > 0.0001)) {
        return t0
    }
    var t1: Double = __pytra_float((-b) + s)
    if ((__pytra_float(t1) > 0.0001)) {
        return t1
    }
    return __pytra_float(-1.0)
}

def palette_332(): mutable.ArrayBuffer[Any] = {
    var p: mutable.ArrayBuffer[Any] = __pytra_as_list(__pytra_bytearray((256L * 3L)))
    var __hoisted_cast_1: Double = __pytra_float(7L)
    var __hoisted_cast_2: Double = __pytra_float(3L)
    var i: Long = __pytra_int(0L)
    boundary:
        given __breakLabel_0: boundary.Label[Unit] = summon[boundary.Label[Unit]]
        while (i < __pytra_int(256L)) {
            boundary:
                given __continueLabel_1: boundary.Label[Unit] = summon[boundary.Label[Unit]]
                var r: Long = ((i + 5L) + 7L)
                var g: Long = ((i + 2L) + 7L)
                var b: Long = (i + 3L)
                __pytra_set_index(p, ((i * 3L) + 0L), __pytra_int(__pytra_float(255L * r) / __hoisted_cast_1))
                __pytra_set_index(p, ((i * 3L) + 1L), __pytra_int(__pytra_float(255L * g) / __hoisted_cast_1))
                __pytra_set_index(p, ((i * 3L) + 2L), __pytra_int(__pytra_float(255L * b) / __hoisted_cast_2))
            i += 1L
        }
    return __pytra_as_list(__pytra_bytes(p))
}

def quantize_332(r: Double, g: Double, b: Double): Long = {
    var rr: Long = __pytra_int(clamp01(r) * 255.0)
    var gg: Long = __pytra_int(clamp01(g) * 255.0)
    var bb: Long = __pytra_int(clamp01(b) * 255.0)
    return ((((rr + 5L) + 5L) + ((gg + 5L) + 2L)) + (bb + 6L))
}

def render_frame(width: Long, height: Long, frame_id: Long, frames_n: Long): mutable.ArrayBuffer[Any] = {
    var t: Double = (__pytra_float(frame_id) / __pytra_float(frames_n))
    var tphase: Double = __pytra_float((2.0 * Math.PI) * t)
    var cam_r: Double = 3.0
    var cam_x: Double = __pytra_float(cam_r * scala.math.cos(__pytra_float(tphase * 0.9)))
    var cam_y: Double = __pytra_float(1.1 + (0.25 * scala.math.sin(__pytra_float(tphase * 0.6))))
    var cam_z: Double = __pytra_float(cam_r * scala.math.sin(__pytra_float(tphase * 0.9)))
    var look_x: Double = 0.0
    var look_y: Double = 0.35
    var look_z: Double = 0.0
    val __tuple_0 = __pytra_as_list(normalize((look_x - cam_x), (look_y - cam_y), (look_z - cam_z)))
    var fwd_x: Double = __pytra_float(__tuple_0(0))
    var fwd_y: Double = __pytra_float(__tuple_0(1))
    var fwd_z: Double = __pytra_float(__tuple_0(2))
    val __tuple_1 = __pytra_as_list(normalize(fwd_z, 0.0, (-fwd_x)))
    var right_x: Double = __pytra_float(__tuple_1(0))
    var right_y: Double = __pytra_float(__tuple_1(1))
    var right_z: Double = __pytra_float(__tuple_1(2))
    val __tuple_2 = __pytra_as_list(normalize(((right_y * fwd_z) - (right_z * fwd_y)), ((right_z * fwd_x) - (right_x * fwd_z)), ((right_x * fwd_y) - (right_y * fwd_x))))
    var up_x: Double = __pytra_float(__tuple_2(0))
    var up_y: Double = __pytra_float(__tuple_2(1))
    var up_z: Double = __pytra_float(__tuple_2(2))
    var s0x: Double = __pytra_float(0.9 * scala.math.cos(__pytra_float(1.3 * tphase)))
    var s0y: Double = __pytra_float(0.15 + (0.35 * scala.math.sin(__pytra_float(1.7 * tphase))))
    var s0z: Double = __pytra_float(0.9 * scala.math.sin(__pytra_float(1.3 * tphase)))
    var s1x: Double = __pytra_float(1.2 * scala.math.cos(__pytra_float((1.3 * tphase) + 2.094)))
    var s1y: Double = __pytra_float(0.1 + (0.4 * scala.math.sin(__pytra_float((1.1 * tphase) + 0.8))))
    var s1z: Double = __pytra_float(1.2 * scala.math.sin(__pytra_float((1.3 * tphase) + 2.094)))
    var s2x: Double = __pytra_float(1.0 * scala.math.cos(__pytra_float((1.3 * tphase) + 4.188)))
    var s2y: Double = __pytra_float(0.2 + (0.3 * scala.math.sin(__pytra_float((1.5 * tphase) + 1.9))))
    var s2z: Double = __pytra_float(1.0 * scala.math.sin(__pytra_float((1.3 * tphase) + 4.188)))
    var lr: Double = 0.35
    var lx: Double = __pytra_float(2.4 * scala.math.cos(__pytra_float(tphase * 1.8)))
    var ly: Double = __pytra_float(1.8 + (0.8 * scala.math.sin(__pytra_float(tphase * 1.2))))
    var lz: Double = __pytra_float(2.4 * scala.math.sin(__pytra_float(tphase * 1.8)))
    var frame: mutable.ArrayBuffer[Any] = __pytra_as_list(__pytra_bytearray((width * height)))
    var aspect: Double = (__pytra_float(width) / __pytra_float(height))
    var fov: Double = 1.25
    var __hoisted_cast_3: Double = __pytra_float(height)
    var __hoisted_cast_4: Double = __pytra_float(width)
    var py: Long = __pytra_int(0L)
    boundary:
        given __breakLabel_3: boundary.Label[Unit] = summon[boundary.Label[Unit]]
        while (py < __pytra_int(height)) {
            boundary:
                given __continueLabel_4: boundary.Label[Unit] = summon[boundary.Label[Unit]]
                var row_base: Long = (py * width)
                var sy: Double = (1.0 - ((2.0 * (__pytra_float(py) + 0.5)) / __hoisted_cast_3))
                var px: Long = __pytra_int(0L)
                boundary:
                    given __breakLabel_6: boundary.Label[Unit] = summon[boundary.Label[Unit]]
                    while (px < __pytra_int(width)) {
                        boundary:
                            given __continueLabel_7: boundary.Label[Unit] = summon[boundary.Label[Unit]]
                            var sx: Double = ((((2.0 * (__pytra_float(px) + 0.5)) / __hoisted_cast_4) - 1.0) * aspect)
                            var rx: Double = __pytra_float(fwd_x + (fov * ((sx * right_x) + (sy * up_x))))
                            var ry: Double = __pytra_float(fwd_y + (fov * ((sx * right_y) + (sy * up_y))))
                            var rz: Double = __pytra_float(fwd_z + (fov * ((sx * right_z) + (sy * up_z))))
                            val __tuple_9 = __pytra_as_list(normalize(rx, ry, rz))
                            var dx: Double = __pytra_float(__tuple_9(0))
                            var dy: Double = __pytra_float(__tuple_9(1))
                            var dz: Double = __pytra_float(__tuple_9(2))
                            var best_t: Double = 1000000000.0
                            var hit_kind: Long = 0L
                            var r: Double = 0.0
                            var g: Double = 0.0
                            var b: Double = 0.0
                            if ((__pytra_float(dy) < (-1e-06))) {
                                var tf: Double = __pytra_float(__pytra_float((-1.2) - cam_y) / __pytra_float(dy))
                                if (((__pytra_float(tf) > 0.0001) && (__pytra_float(tf) < best_t))) {
                                    best_t = __pytra_float(tf)
                                    hit_kind = 1L
                                }
                            }
                            var t0: Double = __pytra_float(sphere_intersect(cam_x, cam_y, cam_z, dx, dy, dz, s0x, s0y, s0z, 0.65))
                            if (((t0 > 0.0) && (t0 < best_t))) {
                                best_t = t0
                                hit_kind = 2L
                            }
                            var t1: Double = __pytra_float(sphere_intersect(cam_x, cam_y, cam_z, dx, dy, dz, s1x, s1y, s1z, 0.72))
                            if (((t1 > 0.0) && (t1 < best_t))) {
                                best_t = t1
                                hit_kind = 3L
                            }
                            var t2: Double = __pytra_float(sphere_intersect(cam_x, cam_y, cam_z, dx, dy, dz, s2x, s2y, s2z, 0.58))
                            if (((t2 > 0.0) && (t2 < best_t))) {
                                best_t = t2
                                hit_kind = 4L
                            }
                            if ((hit_kind == 0L)) {
                                val __tuple_10 = __pytra_as_list(sky_color(dx, dy, dz, tphase))
                                r = __pytra_float(__tuple_10(0))
                                g = __pytra_float(__tuple_10(1))
                                b = __pytra_float(__tuple_10(2))
                            } else {
                                if ((hit_kind == 1L)) {
                                    var hx: Double = __pytra_float(cam_x + (best_t * dx))
                                    var hz: Double = __pytra_float(cam_z + (best_t * dz))
                                    var cx: Long = __pytra_int(scala.math.floor(__pytra_float(hx * 2.0)))
                                    var cz: Long = __pytra_int(scala.math.floor(__pytra_float(hz * 2.0)))
                                    var checker: Long = __pytra_int(__pytra_ifexp((((cx + cz) % 2L) == 0L), 0L, 1L))
                                    var base_r: Double = __pytra_float(__pytra_ifexp((checker == 0L), 0.1, 0.04))
                                    var base_g: Double = __pytra_float(__pytra_ifexp((checker == 0L), 0.11, 0.05))
                                    var base_b: Double = __pytra_float(__pytra_ifexp((checker == 0L), 0.13, 0.08))
                                    var lxv: Double = __pytra_float(lx - hx)
                                    var lyv: Double = __pytra_float(ly - (-1.2))
                                    var lzv: Double = __pytra_float(lz - hz)
                                    val __tuple_11 = __pytra_as_list(normalize(lxv, lyv, lzv))
                                    var ldx: Double = __pytra_float(__tuple_11(0))
                                    var ldy: Double = __pytra_float(__tuple_11(1))
                                    var ldz: Double = __pytra_float(__tuple_11(2))
                                    var ndotl: Double = __pytra_float(__pytra_max(ldy, 0.0))
                                    var ldist2: Double = __pytra_float(((lxv * lxv) + (lyv * lyv)) + (lzv * lzv))
                                    var glow: Double = __pytra_float(8.0 / __pytra_float(1.0 + ldist2))
                                    r = __pytra_float((base_r + (0.8 * glow)) + (0.2 * ndotl))
                                    g = __pytra_float((base_g + (0.5 * glow)) + (0.18 * ndotl))
                                    b = __pytra_float((base_b + (1.0 * glow)) + (0.24 * ndotl))
                                } else {
                                    var cx: Double = 0.0
                                    var cy: Double = 0.0
                                    var cz: Double = 0.0
                                    var rad: Double = 1.0
                                    if ((hit_kind == 2L)) {
                                        cx = __pytra_float(s0x)
                                        cy = __pytra_float(s0y)
                                        cz = __pytra_float(s0z)
                                        rad = 0.65
                                    } else {
                                        if ((hit_kind == 3L)) {
                                            cx = __pytra_float(s1x)
                                            cy = __pytra_float(s1y)
                                            cz = __pytra_float(s1z)
                                            rad = 0.72
                                        } else {
                                            cx = __pytra_float(s2x)
                                            cy = __pytra_float(s2y)
                                            cz = __pytra_float(s2z)
                                            rad = 0.58
                                        }
                                    }
                                    var hx: Double = __pytra_float(cam_x + (best_t * dx))
                                    var hy: Double = __pytra_float(cam_y + (best_t * dy))
                                    var hz: Double = __pytra_float(cam_z + (best_t * dz))
                                    val __tuple_12 = __pytra_as_list(normalize((__pytra_float(hx - cx) / rad), (__pytra_float(hy - cy) / rad), (__pytra_float(hz - cz) / rad)))
                                    var nx: Double = __pytra_float(__tuple_12(0))
                                    var ny: Double = __pytra_float(__tuple_12(1))
                                    var nz: Double = __pytra_float(__tuple_12(2))
                                    val __tuple_13 = __pytra_as_list(reflect(dx, dy, dz, nx, ny, nz))
                                    var rdx: Double = __pytra_float(__tuple_13(0))
                                    var rdy: Double = __pytra_float(__tuple_13(1))
                                    var rdz: Double = __pytra_float(__tuple_13(2))
                                    val __tuple_14 = __pytra_as_list(refract(dx, dy, dz, nx, ny, nz, (1.0 / 1.45)))
                                    var tdx: Double = __pytra_float(__tuple_14(0))
                                    var tdy: Double = __pytra_float(__tuple_14(1))
                                    var tdz: Double = __pytra_float(__tuple_14(2))
                                    val __tuple_15 = __pytra_as_list(sky_color(rdx, rdy, rdz, tphase))
                                    var sr: Double = __pytra_float(__tuple_15(0))
                                    var sg: Double = __pytra_float(__tuple_15(1))
                                    var sb: Double = __pytra_float(__tuple_15(2))
                                    val __tuple_16 = __pytra_as_list(sky_color(tdx, tdy, tdz, (tphase + 0.8)))
                                    var tr: Double = __pytra_float(__tuple_16(0))
                                    var tg: Double = __pytra_float(__tuple_16(1))
                                    var tb: Double = __pytra_float(__tuple_16(2))
                                    var cosi: Double = __pytra_float(__pytra_max((-(((dx * nx) + (dy * ny)) + (dz * nz))), 0.0))
                                    var fr: Double = __pytra_float(schlick(cosi, 0.04))
                                    r = __pytra_float((tr * (1.0 - fr)) + (sr * fr))
                                    g = __pytra_float((tg * (1.0 - fr)) + (sg * fr))
                                    b = __pytra_float((tb * (1.0 - fr)) + (sb * fr))
                                    var lxv: Double = __pytra_float(lx - hx)
                                    var lyv: Double = __pytra_float(ly - hy)
                                    var lzv: Double = __pytra_float(lz - hz)
                                    val __tuple_17 = __pytra_as_list(normalize(lxv, lyv, lzv))
                                    var ldx: Double = __pytra_float(__tuple_17(0))
                                    var ldy: Double = __pytra_float(__tuple_17(1))
                                    var ldz: Double = __pytra_float(__tuple_17(2))
                                    var ndotl: Double = __pytra_float(__pytra_max((((nx * ldx) + (ny * ldy)) + (nz * ldz)), 0.0))
                                    val __tuple_18 = __pytra_as_list(normalize((ldx - dx), (ldy - dy), (ldz - dz)))
                                    var hvx: Double = __pytra_float(__tuple_18(0))
                                    var hvy: Double = __pytra_float(__tuple_18(1))
                                    var hvz: Double = __pytra_float(__tuple_18(2))
                                    var ndoth: Double = __pytra_float(__pytra_max((((nx * hvx) + (ny * hvy)) + (nz * hvz)), 0.0))
                                    var spec: Double = __pytra_float(ndoth * ndoth)
                                    spec = __pytra_float(spec * spec)
                                    spec = __pytra_float(spec * spec)
                                    spec = __pytra_float(spec * spec)
                                    var glow: Double = __pytra_float(10.0 / __pytra_float(((1.0 + (lxv * lxv)) + (lyv * lyv)) + (lzv * lzv)))
                                    r += (((0.2 * ndotl) + (0.8 * spec)) + (0.45 * glow))
                                    g += (((0.18 * ndotl) + (0.6 * spec)) + (0.35 * glow))
                                    b += (((0.26 * ndotl) + (1.0 * spec)) + (0.65 * glow))
                                    if ((hit_kind == 2L)) {
                                        r *= 0.95
                                        g *= 1.05
                                        b *= 1.1
                                    } else {
                                        if ((hit_kind == 3L)) {
                                            r *= 1.08
                                            g *= 0.98
                                            b *= 1.04
                                        } else {
                                            r *= 1.02
                                            g *= 1.1
                                            b *= 0.95
                                        }
                                    }
                                }
                            }
                            r = __pytra_float(scala.math.sqrt(__pytra_float(clamp01(r))))
                            g = __pytra_float(scala.math.sqrt(__pytra_float(clamp01(g))))
                            b = __pytra_float(scala.math.sqrt(__pytra_float(clamp01(b))))
                            __pytra_set_index(frame, (row_base + px), quantize_332(r, g, b))
                        px += 1L
                    }
            py += 1L
        }
    return __pytra_as_list(__pytra_bytes(frame))
}

def run_16_glass_sculpture_chaos(): Unit = {
    var width: Long = 320L
    var height: Long = 240L
    var frames_n: Long = 72L
    var out_path: String = "sample/out/16_glass_sculpture_chaos.gif"
    var start: Double = __pytra_perf_counter()
    var frames: mutable.ArrayBuffer[Any] = __pytra_as_list(mutable.ArrayBuffer[Any]())
    var i: Long = __pytra_int(0L)
    boundary:
        given __breakLabel_0: boundary.Label[Unit] = summon[boundary.Label[Unit]]
        while (i < __pytra_int(frames_n)) {
            boundary:
                given __continueLabel_1: boundary.Label[Unit] = summon[boundary.Label[Unit]]
                frames.append(render_frame(width, height, i, frames_n))
            i += 1L
        }
    __pytra_save_gif(out_path, width, height, frames, palette_332())
    var elapsed: Double = (__pytra_perf_counter() - start)
    __pytra_print("output:", out_path)
    __pytra_print("frames:", frames_n)
    __pytra_print("elapsed_sec:", elapsed)
}

def main(args: Array[String]): Unit = {
    run_16_glass_sculpture_chaos()
}
