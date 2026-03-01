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

def __pytra_print(args: Any*): Unit = {
    if (args.isEmpty) {
        println()
        return
    }
    println(args.map(__pytra_str).mkString(" "))
}


// 02: Sample that runs a mini sphere-only ray tracer and outputs a PNG image.
// Dependencies are kept minimal (time only) for transpilation compatibility.

def clamp01(v: Double): Double = {
    if ((v < 0.0)) {
        return 0.0
    }
    if ((v > 1.0)) {
        return 1.0
    }
    return v
}

def hit_sphere(ox: Double, oy: Double, oz: Double, dx: Double, dy: Double, dz: Double, cx: Double, cy: Double, cz: Double, r: Double): Double = {
    var lx: Double = (ox - cx)
    var ly: Double = (oy - cy)
    var lz: Double = (oz - cz)
    var a: Double = (((dx * dx) + (dy * dy)) + (dz * dz))
    var b: Double = (2.0 * (((lx * dx) + (ly * dy)) + (lz * dz)))
    var c: Double = ((((lx * lx) + (ly * ly)) + (lz * lz)) - (r * r))
    var d: Double = ((b * b) - ((4.0 * a) * c))
    if ((d < 0.0)) {
        return __pytra_float(-1.0)
    }
    var sd: Double = __pytra_float(scala.math.sqrt(__pytra_float(d)))
    var t0: Double = (((-b) - sd) / (2.0 * a))
    var t1: Double = (((-b) + sd) / (2.0 * a))
    if ((t0 > 0.001)) {
        return t0
    }
    if ((t1 > 0.001)) {
        return t1
    }
    return __pytra_float(-1.0)
}

def render(width: Long, height: Long, aa: Long): mutable.ArrayBuffer[Any] = {
    var pixels: mutable.ArrayBuffer[Any] = __pytra_as_list(mutable.ArrayBuffer[Any]())
    var ox: Double = 0.0
    var oy: Double = 0.0
    var oz: Double = __pytra_float(-3.0)
    var lx: Double = __pytra_float(-0.4)
    var ly: Double = 0.8
    var lz: Double = __pytra_float(-0.45)
    var __hoisted_cast_1: Double = __pytra_float(aa)
    var __hoisted_cast_2: Double = __pytra_float(height - 1L)
    var __hoisted_cast_3: Double = __pytra_float(width - 1L)
    var __hoisted_cast_4: Double = __pytra_float(height)
    var y: Long = __pytra_int(0L)
    boundary:
        given __breakLabel_0: boundary.Label[Unit] = summon[boundary.Label[Unit]]
        while (y < __pytra_int(height)) {
            boundary:
                given __continueLabel_1: boundary.Label[Unit] = summon[boundary.Label[Unit]]
                var x: Long = __pytra_int(0L)
                boundary:
                    given __breakLabel_3: boundary.Label[Unit] = summon[boundary.Label[Unit]]
                    while (x < __pytra_int(width)) {
                        boundary:
                            given __continueLabel_4: boundary.Label[Unit] = summon[boundary.Label[Unit]]
                            var ar: Long = 0L
                            var ag: Long = 0L
                            var ab: Long = 0L
                            var ay: Long = __pytra_int(0L)
                            boundary:
                                given __breakLabel_6: boundary.Label[Unit] = summon[boundary.Label[Unit]]
                                while (ay < __pytra_int(aa)) {
                                    boundary:
                                        given __continueLabel_7: boundary.Label[Unit] = summon[boundary.Label[Unit]]
                                        var ax: Long = __pytra_int(0L)
                                        boundary:
                                            given __breakLabel_9: boundary.Label[Unit] = summon[boundary.Label[Unit]]
                                            while (ax < __pytra_int(aa)) {
                                                boundary:
                                                    given __continueLabel_10: boundary.Label[Unit] = summon[boundary.Label[Unit]]
                                                    var fy: Double = ((__pytra_float(y) + ((__pytra_float(ay) + 0.5) / __hoisted_cast_1)) / __hoisted_cast_2)
                                                    var fx: Double = ((__pytra_float(x) + ((__pytra_float(ax) + 0.5) / __hoisted_cast_1)) / __hoisted_cast_3)
                                                    var sy: Double = (1.0 - (2.0 * fy))
                                                    var sx: Double = (((2.0 * fx) - 1.0) * (__pytra_float(width) / __hoisted_cast_4))
                                                    var dx: Double = sx
                                                    var dy: Double = sy
                                                    var dz: Double = 1.0
                                                    var inv_len: Double = __pytra_float(1.0 / __pytra_float(scala.math.sqrt(__pytra_float(((dx * dx) + (dy * dy)) + (dz * dz)))))
                                                    dx *= inv_len
                                                    dy *= inv_len
                                                    dz *= inv_len
                                                    var t_min: Double = 1e+30
                                                    var hit_id: Long = __pytra_int(-1L)
                                                    var t: Double = __pytra_float(hit_sphere(ox, oy, oz, dx, dy, dz, (-0.8), (-0.2), 2.2, 0.8))
                                                    if (((t > 0.0) && (t < t_min))) {
                                                        t_min = t
                                                        hit_id = 0L
                                                    }
                                                    t = __pytra_float(hit_sphere(ox, oy, oz, dx, dy, dz, 0.9, 0.1, 2.9, 0.95))
                                                    if (((t > 0.0) && (t < t_min))) {
                                                        t_min = t
                                                        hit_id = 1L
                                                    }
                                                    t = __pytra_float(hit_sphere(ox, oy, oz, dx, dy, dz, 0.0, (-1001.0), 3.0, 1000.0))
                                                    if (((t > 0.0) && (t < t_min))) {
                                                        t_min = t
                                                        hit_id = 2L
                                                    }
                                                    var r: Long = 0L
                                                    var g: Long = 0L
                                                    var b: Long = 0L
                                                    if ((hit_id >= 0L)) {
                                                        var px: Double = (ox + (dx * t_min))
                                                        var py: Double = (oy + (dy * t_min))
                                                        var pz: Double = (oz + (dz * t_min))
                                                        var nx: Double = 0.0
                                                        var ny: Double = 0.0
                                                        var nz: Double = 0.0
                                                        if ((hit_id == 0L)) {
                                                            nx = ((px + 0.8) / 0.8)
                                                            ny = ((py + 0.2) / 0.8)
                                                            nz = ((pz - 2.2) / 0.8)
                                                        } else {
                                                            if ((hit_id == 1L)) {
                                                                nx = ((px - 0.9) / 0.95)
                                                                ny = ((py - 0.1) / 0.95)
                                                                nz = ((pz - 2.9) / 0.95)
                                                            } else {
                                                                nx = 0.0
                                                                ny = 1.0
                                                                nz = 0.0
                                                            }
                                                        }
                                                        var diff: Double = (((nx * (-lx)) + (ny * (-ly))) + (nz * (-lz)))
                                                        diff = __pytra_float(clamp01(diff))
                                                        var base_r: Double = 0.0
                                                        var base_g: Double = 0.0
                                                        var base_b: Double = 0.0
                                                        if ((hit_id == 0L)) {
                                                            base_r = 0.95
                                                            base_g = 0.35
                                                            base_b = 0.25
                                                        } else {
                                                            if ((hit_id == 1L)) {
                                                                base_r = 0.25
                                                                base_g = 0.55
                                                                base_b = 0.95
                                                            } else {
                                                                var checker: Long = (__pytra_int((px + 50.0) * 0.8) + __pytra_int((pz + 50.0) * 0.8))
                                                                if (((checker % 2L) == 0L)) {
                                                                    base_r = 0.85
                                                                    base_g = 0.85
                                                                    base_b = 0.85
                                                                } else {
                                                                    base_r = 0.2
                                                                    base_g = 0.2
                                                                    base_b = 0.2
                                                                }
                                                            }
                                                        }
                                                        var shade: Double = (0.12 + (0.88 * diff))
                                                        r = __pytra_int(255.0 * clamp01((base_r * shade)))
                                                        g = __pytra_int(255.0 * clamp01((base_g * shade)))
                                                        b = __pytra_int(255.0 * clamp01((base_b * shade)))
                                                    } else {
                                                        var tsky: Double = (0.5 * (dy + 1.0))
                                                        r = __pytra_int(255.0 * (0.65 + (0.2 * tsky)))
                                                        g = __pytra_int(255.0 * (0.75 + (0.18 * tsky)))
                                                        b = __pytra_int(255.0 * (0.9 + (0.08 * tsky)))
                                                    }
                                                    ar += r
                                                    ag += g
                                                    ab += b
                                                ax += 1L
                                            }
                                    ay += 1L
                                }
                            var samples: Long = (aa * aa)
                            pixels.append((__pytra_int(ar / samples)))
                            pixels.append((__pytra_int(ag / samples)))
                            pixels.append((__pytra_int(ab / samples)))
                        x += 1L
                    }
            y += 1L
        }
    return pixels
}

def run_raytrace(): Unit = {
    var width: Long = 1600L
    var height: Long = 900L
    var aa: Long = 2L
    var out_path: String = "sample/out/02_raytrace_spheres.png"
    var start: Double = __pytra_perf_counter()
    var pixels: mutable.ArrayBuffer[Any] = __pytra_as_list(render(width, height, aa))
    __pytra_write_rgb_png(out_path, width, height, pixels)
    var elapsed: Double = (__pytra_perf_counter() - start)
    __pytra_print("output:", out_path)
    __pytra_print("size:", width, "x", height)
    __pytra_print("elapsed_sec:", elapsed)
}

def main(args: Array[String]): Unit = {
    run_raytrace()
}
