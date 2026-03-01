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

def __pytra_is_Token(v: Any): Boolean = {
    v.isInstanceOf[Token]
}

def __pytra_as_Token(v: Any): Token = {
    v match {
        case obj: Token => obj
        case _ => new Token()
    }
}

def __pytra_is_ExprNode(v: Any): Boolean = {
    v.isInstanceOf[ExprNode]
}

def __pytra_as_ExprNode(v: Any): ExprNode = {
    v match {
        case obj: ExprNode => obj
        case _ => new ExprNode()
    }
}

def __pytra_is_StmtNode(v: Any): Boolean = {
    v.isInstanceOf[StmtNode]
}

def __pytra_as_StmtNode(v: Any): StmtNode = {
    v match {
        case obj: StmtNode => obj
        case _ => new StmtNode()
    }
}

def __pytra_is_Parser(v: Any): Boolean = {
    v.isInstanceOf[Parser]
}

def __pytra_as_Parser(v: Any): Parser = {
    v match {
        case obj: Parser => obj
        case _ => new Parser()
    }
}

class Token() {
    var kind: String = ""
    var text: String = ""
    var pos: Long = 0L
    var number_value: Long = 0L

    def this(kind: String, text: String, pos: Long, number_value: Long) = {
        this()
        this.kind = kind
        this.text = text
        this.pos = pos
        this.number_value = number_value
    }
}

class ExprNode() {
    var kind: String = ""
    var value: Long = 0L
    var name: String = ""
    var op: String = ""
    var left: Long = 0L
    var right: Long = 0L
    var kind_tag: Long = 0L
    var op_tag: Long = 0L

    def this(kind: String, value: Long, name: String, op: String, left: Long, right: Long, kind_tag: Long, op_tag: Long) = {
        this()
        this.kind = kind
        this.value = value
        this.name = name
        this.op = op
        this.left = left
        this.right = right
        this.kind_tag = kind_tag
        this.op_tag = op_tag
    }
}

class StmtNode() {
    var kind: String = ""
    var name: String = ""
    var expr_index: Long = 0L
    var kind_tag: Long = 0L

    def this(kind: String, name: String, expr_index: Long, kind_tag: Long) = {
        this()
        this.kind = kind
        this.name = name
        this.expr_index = expr_index
        this.kind_tag = kind_tag
    }
}

class Parser() {
    var tokens: mutable.ArrayBuffer[Any] = mutable.ArrayBuffer[Any]()
    var pos: Long = 0L
    var expr_nodes: mutable.ArrayBuffer[Any] = mutable.ArrayBuffer[Any]()

    def new_expr_nodes(): mutable.ArrayBuffer[Any] = {
        return __pytra_as_list(mutable.ArrayBuffer[Any]())
    }

    def this(tokens: mutable.ArrayBuffer[Any]) = {
        this()
        this.tokens = tokens
        this.pos = 0L
        this.expr_nodes = this.new_expr_nodes()
    }

    def current_token(): Token = {
        return __pytra_as_Token(__pytra_as_Token(__pytra_get_index(this.tokens, this.pos)))
    }

    def previous_token(): Token = {
        return __pytra_as_Token(__pytra_as_Token(__pytra_get_index(this.tokens, (this.pos - 1L))))
    }

    def peek_kind(): String = {
        return __pytra_str(this.current_token().kind)
    }

    def py_match(kind: String): Boolean = {
        if ((__pytra_str(this.peek_kind()) == __pytra_str(kind))) {
            this.pos += 1L
            return true
        }
        return false
    }

    def expect(kind: String): Token = {
        var token: Token = __pytra_as_Token(this.current_token())
        if ((__pytra_str(token.kind) != __pytra_str(kind))) {
            throw new RuntimeException(__pytra_str(((__pytra_str(__pytra_str(__pytra_str(__pytra_str("parse error at pos=") + __pytra_str(token.pos)) + __pytra_str(", expected=")) + __pytra_str(kind)) + __pytra_str(", got=")) + token.kind)))
        }
        this.pos += 1L
        return token
    }

    def skip_newlines(): Unit = {
        boundary:
            given __breakLabel_0: boundary.Label[Unit] = summon[boundary.Label[Unit]]
            while (this.py_match("NEWLINE")) {
                boundary:
                    given __continueLabel_1: boundary.Label[Unit] = summon[boundary.Label[Unit]]
                    // pass
            }
    }

    def add_expr(node: ExprNode): Long = {
        this.expr_nodes = __pytra_as_list(this.expr_nodes); this.expr_nodes.append(node)
        return (__pytra_len(this.expr_nodes) - 1L)
    }

    def parse_program(): mutable.ArrayBuffer[Any] = {
        var stmts: mutable.ArrayBuffer[Any] = __pytra_as_list(mutable.ArrayBuffer[Any]())
        this.skip_newlines()
        boundary:
            given __breakLabel_0: boundary.Label[Unit] = summon[boundary.Label[Unit]]
            while ((__pytra_str(this.peek_kind()) != __pytra_str("EOF"))) {
                boundary:
                    given __continueLabel_1: boundary.Label[Unit] = summon[boundary.Label[Unit]]
                    var stmt: StmtNode = __pytra_as_StmtNode(this.parse_stmt())
                    stmts.append(stmt)
                    this.skip_newlines()
            }
        return stmts
    }

    def parse_stmt(): StmtNode = {
        if (this.py_match("LET")) {
            var let_name: String = __pytra_str(this.expect("IDENT").text)
            this.expect("EQUAL")
            var let_expr_index: Long = __pytra_int(this.parse_expr())
            return __pytra_as_StmtNode(new StmtNode("let", let_name, let_expr_index, 1L))
        }
        if (this.py_match("PRINT")) {
            var print_expr_index: Long = __pytra_int(this.parse_expr())
            return __pytra_as_StmtNode(new StmtNode("print", "", print_expr_index, 3L))
        }
        var assign_name: String = __pytra_str(this.expect("IDENT").text)
        this.expect("EQUAL")
        var assign_expr_index: Long = __pytra_int(this.parse_expr())
        return __pytra_as_StmtNode(new StmtNode("assign", assign_name, assign_expr_index, 2L))
    }

    def parse_expr(): Long = {
        return __pytra_int(this.parse_add())
    }

    def parse_add(): Long = {
        var left: Long = __pytra_int(this.parse_mul())
        boundary:
            given __breakLabel_0: boundary.Label[Unit] = summon[boundary.Label[Unit]]
            while (true) {
                boundary:
                    given __continueLabel_1: boundary.Label[Unit] = summon[boundary.Label[Unit]]
                    if (this.py_match("PLUS")) {
                        var right: Long = __pytra_int(this.parse_mul())
                        left = __pytra_int(this.add_expr(new ExprNode("bin", 0L, "", "+", left, right, 3L, 1L)))
                        break(())(using __continueLabel_1)
                    }
                    if (this.py_match("MINUS")) {
                        var right: Long = __pytra_int(this.parse_mul())
                        left = __pytra_int(this.add_expr(new ExprNode("bin", 0L, "", "-", left, right, 3L, 2L)))
                        break(())(using __continueLabel_1)
                    }
                    break(())(using __breakLabel_0)
            }
        return left
    }

    def parse_mul(): Long = {
        var left: Long = __pytra_int(this.parse_unary())
        boundary:
            given __breakLabel_0: boundary.Label[Unit] = summon[boundary.Label[Unit]]
            while (true) {
                boundary:
                    given __continueLabel_1: boundary.Label[Unit] = summon[boundary.Label[Unit]]
                    if (this.py_match("STAR")) {
                        var right: Long = __pytra_int(this.parse_unary())
                        left = __pytra_int(this.add_expr(new ExprNode("bin", 0L, "", "*", left, right, 3L, 3L)))
                        break(())(using __continueLabel_1)
                    }
                    if (this.py_match("SLASH")) {
                        var right: Long = __pytra_int(this.parse_unary())
                        left = __pytra_int(this.add_expr(new ExprNode("bin", 0L, "", "/", left, right, 3L, 4L)))
                        break(())(using __continueLabel_1)
                    }
                    break(())(using __breakLabel_0)
            }
        return left
    }

    def parse_unary(): Long = {
        if (this.py_match("MINUS")) {
            var child: Long = __pytra_int(this.parse_unary())
            return __pytra_int(this.add_expr(new ExprNode("neg", 0L, "", "", child, (-1L), 4L, 0L)))
        }
        return __pytra_int(this.parse_primary())
    }

    def parse_primary(): Long = {
        if (this.py_match("NUMBER")) {
            var token_num: Token = __pytra_as_Token(this.previous_token())
            return __pytra_int(this.add_expr(new ExprNode("lit", token_num.number_value, "", "", (-1L), (-1L), 1L, 0L)))
        }
        if (this.py_match("IDENT")) {
            var token_ident: Token = __pytra_as_Token(this.previous_token())
            return __pytra_int(this.add_expr(new ExprNode("var", 0L, token_ident.text, "", (-1L), (-1L), 2L, 0L)))
        }
        if (this.py_match("LPAREN")) {
            var expr_index: Long = __pytra_int(this.parse_expr())
            this.expect("RPAREN")
            return expr_index
        }
        var t: Token = __pytra_as_Token(this.current_token())
        throw new RuntimeException(__pytra_str(((__pytra_str(__pytra_str("primary parse error at pos=") + __pytra_str(t.pos)) + __pytra_str(" got=")) + t.kind)))
        return 0L
    }
}

def tokenize(lines: mutable.ArrayBuffer[Any]): mutable.ArrayBuffer[Any] = {
    var single_char_token_tags: mutable.LinkedHashMap[Any, Any] = __pytra_as_dict(mutable.LinkedHashMap[Any, Any]((__pytra_str("+"), 1L), (__pytra_str("-"), 2L), (__pytra_str("*"), 3L), (__pytra_str("/"), 4L), (__pytra_str("("), 5L), (__pytra_str(")"), 6L), (__pytra_str("="), 7L)))
    var single_char_token_kinds: mutable.ArrayBuffer[Any] = __pytra_as_list(mutable.ArrayBuffer[Any]("PLUS", "MINUS", "STAR", "SLASH", "LPAREN", "RPAREN", "EQUAL"))
    var tokens: mutable.ArrayBuffer[Any] = __pytra_as_list(mutable.ArrayBuffer[Any]())
    boundary:
        given __breakLabel_2: boundary.Label[Unit] = summon[boundary.Label[Unit]]
        val __iter_0 = __pytra_as_list(__pytra_enumerate(lines))
        var __i_1: Long = 0L
        while (__i_1 < __iter_0.size.toLong) {
            boundary:
                given __continueLabel_3: boundary.Label[Unit] = summon[boundary.Label[Unit]]
                val __it_4 = __iter_0(__i_1.toInt)
                val __tuple_5 = __pytra_as_list(__it_4)
                var line_index: Long = __pytra_int(__tuple_5(0))
                var source: String = __pytra_str(__tuple_5(1))
                var i: Long = 0L
                var n: Long = __pytra_len(source)
                boundary:
                    given __breakLabel_6: boundary.Label[Unit] = summon[boundary.Label[Unit]]
                    while ((i < n)) {
                        boundary:
                            given __continueLabel_7: boundary.Label[Unit] = summon[boundary.Label[Unit]]
                            var ch: String = __pytra_str(__pytra_get_index(source, i))
                            if ((__pytra_str(ch) == __pytra_str(" "))) {
                                i += 1L
                                break(())(using __continueLabel_7)
                            }
                            var single_tag: Long = __pytra_int(__pytra_as_dict(single_char_token_tags).getOrElse(__pytra_str(ch), 0L))
                            if ((single_tag > 0L)) {
                                tokens.append(new Token(__pytra_str(__pytra_get_index(single_char_token_kinds, (single_tag - 1L))), ch, i, 0L))
                                i += 1L
                                break(())(using __continueLabel_7)
                            }
                            if (__pytra_truthy(__pytra_isdigit(ch))) {
                                var start: Long = i
                                boundary:
                                    given __breakLabel_8: boundary.Label[Unit] = summon[boundary.Label[Unit]]
                                    while (((i < n) && __pytra_truthy(__pytra_isdigit(__pytra_str(__pytra_get_index(source, i)))))) {
                                        boundary:
                                            given __continueLabel_9: boundary.Label[Unit] = summon[boundary.Label[Unit]]
                                            i += 1L
                                    }
                                var text: String = __pytra_str(__pytra_slice(source, start, i))
                                tokens.append(new Token("NUMBER", text, start, __pytra_int(text)))
                                break(())(using __continueLabel_7)
                            }
                            if ((__pytra_truthy(__pytra_isalpha(ch)) || (__pytra_str(ch) == __pytra_str("_")))) {
                                var start: Long = i
                                boundary:
                                    given __breakLabel_10: boundary.Label[Unit] = summon[boundary.Label[Unit]]
                                    while (((i < n) && ((__pytra_truthy(__pytra_isalpha(__pytra_str(__pytra_get_index(source, i)))) || (__pytra_str(__pytra_get_index(source, i)) == __pytra_str("_"))) || __pytra_truthy(__pytra_isdigit(__pytra_str(__pytra_get_index(source, i))))))) {
                                        boundary:
                                            given __continueLabel_11: boundary.Label[Unit] = summon[boundary.Label[Unit]]
                                            i += 1L
                                    }
                                var text: String = __pytra_str(__pytra_slice(source, start, i))
                                if ((__pytra_str(text) == __pytra_str("let"))) {
                                    tokens.append(new Token("LET", text, start, 0L))
                                } else {
                                    if ((__pytra_str(text) == __pytra_str("print"))) {
                                        tokens.append(new Token("PRINT", text, start, 0L))
                                    } else {
                                        tokens.append(new Token("IDENT", text, start, 0L))
                                    }
                                }
                                break(())(using __continueLabel_7)
                            }
                            throw new RuntimeException(__pytra_str((__pytra_str(__pytra_str(__pytra_str(__pytra_str(__pytra_str("tokenize error at line=") + __pytra_str(line_index)) + __pytra_str(" pos=")) + __pytra_str(i)) + __pytra_str(" ch=")) + __pytra_str(ch))))
                    }
                tokens.append(new Token("NEWLINE", "", n, 0L))
            __i_1 += 1L
        }
    tokens.append(new Token("EOF", "", __pytra_len(lines), 0L))
    return tokens
}

def eval_expr(expr_index: Long, expr_nodes: mutable.ArrayBuffer[Any], env: mutable.LinkedHashMap[Any, Any]): Long = {
    var node: ExprNode = __pytra_as_ExprNode(__pytra_as_ExprNode(__pytra_get_index(expr_nodes, expr_index)))
    if ((__pytra_int(node.kind_tag) == 1L)) {
        return __pytra_int(node.value)
    }
    if ((__pytra_int(node.kind_tag) == 2L)) {
        if ((!(__pytra_contains(env, node.name)))) {
            throw new RuntimeException(__pytra_str(("undefined variable: " + node.name)))
        }
        return __pytra_int(__pytra_get_index(env, node.name))
    }
    if ((__pytra_int(node.kind_tag) == 4L)) {
        return __pytra_int(-eval_expr(node.left, expr_nodes, env))
    }
    if ((__pytra_int(node.kind_tag) == 3L)) {
        var lhs: Long = __pytra_int(eval_expr(node.left, expr_nodes, env))
        var rhs: Long = __pytra_int(eval_expr(node.right, expr_nodes, env))
        if ((__pytra_int(node.op_tag) == 1L)) {
            return (lhs + rhs)
        }
        if ((__pytra_int(node.op_tag) == 2L)) {
            return (lhs - rhs)
        }
        if ((__pytra_int(node.op_tag) == 3L)) {
            return (lhs * rhs)
        }
        if ((__pytra_int(node.op_tag) == 4L)) {
            if ((rhs == 0L)) {
                throw new RuntimeException(__pytra_str("division by zero"))
            }
            return (__pytra_int(lhs / rhs))
        }
        throw new RuntimeException(__pytra_str(("unknown operator: " + node.op)))
    }
    throw new RuntimeException(__pytra_str(("unknown node kind: " + node.kind)))
    return 0L
}

def execute(stmts: mutable.ArrayBuffer[Any], expr_nodes: mutable.ArrayBuffer[Any], trace: Boolean): Long = {
    var env: mutable.LinkedHashMap[Any, Any] = __pytra_as_dict(mutable.LinkedHashMap[Any, Any]())
    var checksum: Long = 0L
    var printed: Long = 0L
    boundary:
        given __breakLabel_2: boundary.Label[Unit] = summon[boundary.Label[Unit]]
        val __iter_0 = __pytra_as_list(stmts)
        var __i_1: Long = 0L
        while (__i_1 < __iter_0.size.toLong) {
            boundary:
                given __continueLabel_3: boundary.Label[Unit] = summon[boundary.Label[Unit]]
                val stmt: StmtNode = __pytra_as_StmtNode(__iter_0(__i_1.toInt))
                if ((__pytra_int(stmt.kind_tag) == 1L)) {
                    __pytra_set_index(env, stmt.name, eval_expr(stmt.expr_index, expr_nodes, env))
                    break(())(using __continueLabel_3)
                }
                if ((__pytra_int(stmt.kind_tag) == 2L)) {
                    if ((!(__pytra_contains(env, stmt.name)))) {
                        throw new RuntimeException(__pytra_str(("assign to undefined variable: " + stmt.name)))
                    }
                    __pytra_set_index(env, stmt.name, eval_expr(stmt.expr_index, expr_nodes, env))
                    break(())(using __continueLabel_3)
                }
                var value: Long = __pytra_int(eval_expr(stmt.expr_index, expr_nodes, env))
                if (trace) {
                    __pytra_print(value)
                }
                var norm: Long = (value % 1000000007L)
                if ((norm < 0L)) {
                    norm += 1000000007L
                }
                checksum = (((checksum * 131L) + norm) % 1000000007L)
                printed += 1L
            __i_1 += 1L
        }
    if (trace) {
        __pytra_print("printed:", printed)
    }
    return checksum
}

def build_benchmark_source(var_count: Long, loops: Long): mutable.ArrayBuffer[Any] = {
    var lines: mutable.ArrayBuffer[Any] = __pytra_as_list(mutable.ArrayBuffer[Any]())
    var i: Long = __pytra_int(0L)
    boundary:
        given __breakLabel_0: boundary.Label[Unit] = summon[boundary.Label[Unit]]
        while (i < __pytra_int(var_count)) {
            boundary:
                given __continueLabel_1: boundary.Label[Unit] = summon[boundary.Label[Unit]]
                lines.append((__pytra_str(__pytra_str(__pytra_str("let v") + __pytra_str(i)) + __pytra_str(" = ")) + __pytra_str(i + 1L)))
            i += 1L
        }
    i = __pytra_int(0L)
    boundary:
        given __breakLabel_3: boundary.Label[Unit] = summon[boundary.Label[Unit]]
        while (i < __pytra_int(loops)) {
            boundary:
                given __continueLabel_4: boundary.Label[Unit] = summon[boundary.Label[Unit]]
                var x: Long = (i % var_count)
                var y: Long = ((i + 3L) % var_count)
                var c1: Long = ((i % 7L) + 1L)
                var c2: Long = ((i % 11L) + 2L)
                lines.append((__pytra_str((__pytra_str((__pytra_str((__pytra_str((__pytra_str((__pytra_str((__pytra_str(__pytra_str("v") + __pytra_str(x)) + __pytra_str(" = (v"))) + __pytra_str(x))) + __pytra_str(" * "))) + __pytra_str(c1))) + __pytra_str(" + v"))) + __pytra_str(y))) + __pytra_str(" + 10000) / ") + __pytra_str(c2)))
                if (((i % 97L) == 0L)) {
                    lines.append((__pytra_str("print v") + __pytra_str(x)))
                }
            i += 1L
        }
    lines.append("print (v0 + v1 + v2 + v3)")
    return lines
}

def run_demo(): Unit = {
    var demo_lines: mutable.ArrayBuffer[Any] = __pytra_as_list(mutable.ArrayBuffer[Any]())
    demo_lines.append("let a = 10")
    demo_lines.append("let b = 3")
    demo_lines.append("a = (a + b) * 2")
    demo_lines.append("print a")
    demo_lines.append("print a / b")
    var tokens: mutable.ArrayBuffer[Any] = __pytra_as_list(tokenize(demo_lines))
    var parser: Parser = __pytra_as_Parser(new Parser(tokens))
    var stmts: mutable.ArrayBuffer[Any] = __pytra_as_list(parser.parse_program())
    var checksum: Long = __pytra_int(execute(stmts, parser.expr_nodes, true))
    __pytra_print("demo_checksum:", checksum)
}

def run_benchmark(): Unit = {
    var source_lines: mutable.ArrayBuffer[Any] = __pytra_as_list(build_benchmark_source(32L, 120000L))
    var start: Double = __pytra_perf_counter()
    var tokens: mutable.ArrayBuffer[Any] = __pytra_as_list(tokenize(source_lines))
    var parser: Parser = __pytra_as_Parser(new Parser(tokens))
    var stmts: mutable.ArrayBuffer[Any] = __pytra_as_list(parser.parse_program())
    var checksum: Long = __pytra_int(execute(stmts, parser.expr_nodes, false))
    var elapsed: Double = (__pytra_perf_counter() - start)
    __pytra_print("token_count:", __pytra_len(tokens))
    __pytra_print("expr_count:", __pytra_len(parser.expr_nodes))
    __pytra_print("stmt_count:", __pytra_len(stmts))
    __pytra_print("checksum:", checksum)
    __pytra_print("elapsed_sec:", elapsed)
}

def __pytra_main(): Unit = {
    run_demo()
    run_benchmark()
}

def main(args: Array[String]): Unit = {
    __pytra_main()
}
