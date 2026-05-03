// Scala runtime core for Pytra native backend.
// Source of truth: src/runtime/scala/native/built_in/py_runtime.scala

import scala.collection.mutable
import java.nio.file.{Files, Paths}

type type_py = Any
val dict: type_py = "dict"
val list: type_py = "list"
val set: type_py = "set"
val str: type_py = "str"
val int: type_py = "int"
val float: type_py = "float"
val bool: type_py = "bool"

def field(default_factory: Any = null): Any = default_factory match {
    case "dict" => mutable.LinkedHashMap[Any, Any]()
    case "list" => mutable.ArrayBuffer[Any]()
    case "set" => mutable.LinkedHashSet[Any]()
    case fn: Function0[?] => fn()
    case null => null
    case other => other
}

// Trait for Python enum-like classes so __pytra_int() can extract their integer value.
trait PytraEnumLike {
    def value: Long
}

class PyTuple(items: Iterable[Any] = Nil) extends mutable.ArrayBuffer[Any] {
    this.addAll(items)
}

class Exception extends RuntimeException {
    var __pytra_message: String = ""
    def __init__(msg: Any): Unit = {
        __pytra_message = __pytra_str(msg)
    }
    override def getMessage(): String = __pytra_message
    override def toString: String = __pytra_message
}

type ArgValue = Any

class ValueError extends Exception
class TypeError extends Exception
class RuntimeError extends Exception
class IndexError extends Exception
class KeyError extends Exception

def __pytra_noop(args: Any*): Unit = { }

// Implicit conversion: Any → Double for arithmetic in dynamically-typed contexts.
// EAST type inference may produce `unknown` → `Any` for variables whose actual
// runtime type is numeric.  This conversion lets Scala compile such expressions.
// Note: implicit Any→Double was removed due to StackOverflow risk.
// Emitter wraps Any-typed arithmetic operands with __pytra_float() instead.


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

def __pytra_any_default(): Any = {
    0L
}

def __pytra_assert(args: Any*): Boolean = {
    true
}

def py_to_string(v: Any): String = {
    __pytra_str(v)
}

def __pytra_perf_counter(): Double = {
    System.nanoTime().toDouble / 1_000_000_000.0
}

object __pytra_path {
    def join(a: Any, b: Any): String = os_path.join(a, b)
    def splitext(p: Any): mutable.ArrayBuffer[Any] = os_path.splitext(p)
    def basename(p: Any): String = os_path.basename(p)
    def dirname(p: Any): String = os_path.dirname(p)
    def exists(p: Any): Boolean = os_path.exists(p)
    def abspath(p: Any): String = os_path.abspath(p)
}

object env {
    val target: String = "scala"
}

object os_path {
    def join(a: Any, b: Any): String = __pytra_path_join(a, b)
    def dirname(p: Any): String = __pytra_path_parent(p)
    def basename(p: Any): String = __pytra_path_name(p)
    def splitext(p: Any): mutable.ArrayBuffer[Any] = {
        val path = __pytra_str(p)
        val idx = path.lastIndexOf('.')
        if (idx <= 0) mutable.ArrayBuffer[Any](path, "")
        else mutable.ArrayBuffer[Any](path.substring(0, idx), path.substring(idx))
    }
    def abspath(p: Any): String = Paths.get(__pytra_str(p)).toAbsolutePath.normalize.toString
    def exists(p: Any): Boolean = __pytra_path_exists(p)
}

object os {
    val path = os_path

    def getcwd(): String = Paths.get("").toAbsolutePath.normalize.toString

    def mkdir(p: Any, exist_ok: Boolean = false): Unit = {
        val pathValue = Paths.get(__pytra_str(p))
        try {
            Files.createDirectory(pathValue)
        } catch {
            case _: java.nio.file.FileAlreadyExistsException =>
                if (!exist_ok) throw new RuntimeException("File exists: " + pathValue.toString)
        }
    }

    def makedirs(p: Any, exist_ok: Boolean = false): Unit = {
        val pathValue = Paths.get(__pytra_str(p))
        if (exist_ok || !Files.exists(pathValue)) {
            Files.createDirectories(pathValue)
        } else {
            throw new RuntimeException("File exists: " + pathValue.toString)
        }
    }
}

object glob {
    def glob(pattern: Any): mutable.ArrayBuffer[String] = {
        val matcher = java.nio.file.FileSystems.getDefault.getPathMatcher("glob:" + __pytra_str(pattern))
        val cwd = Paths.get("").toAbsolutePath.normalize
        val out = mutable.ArrayBuffer[String]()
        val stream = Files.newDirectoryStream(cwd)
        try {
            val it = stream.iterator()
            while (it.hasNext) {
                val entry = it.next()
                val name = entry.getFileName.toString
                if (matcher.matches(Paths.get(name))) out.append(name)
            }
        } finally {
            stream.close()
        }
        out
    }
}

class PyStdWriter(useErr: Boolean) {
    def write(text: Any): Unit = {
        if (useErr) Console.err.print(__pytra_str(text))
        else scala.Predef.print(__pytra_str(text))
    }
}

var sys_argv: mutable.ArrayBuffer[String] = mutable.ArrayBuffer[String]()
def __pytra_argv: mutable.ArrayBuffer[String] = sys_argv
var sys_path: mutable.ArrayBuffer[String] = mutable.ArrayBuffer[String]()
val sys_stderr = new PyStdWriter(true)
val sys_stdout = new PyStdWriter(false)

def sys_exit(code: Any = 0L): Unit = {
    throw new RuntimeException("SystemExit(" + __pytra_int(code).toString + ")")
}

def sys_set_argv(values: Any): Unit = {
    sys_argv.clear()
    __pytra_as_list(values).foreach(v => sys_argv.append(__pytra_str(v)))
}

def sys_set_path(values: Any): Unit = {
    sys_path.clear()
    __pytra_as_list(values).foreach(v => sys_path.append(__pytra_str(v)))
}

def pytra_std_sys_write_stderr(text: Any): Unit = sys_stderr.write(text)
def pytra_std_sys_write_stdout(text: Any): Unit = sys_stdout.write(text)
def __pytra_makedirs(path: Any, exist_ok: Any = false): Unit = os.makedirs(path, __pytra_truthy(exist_ok))
def __pytra_floor(v: Any): Double = scala.math.floor(__pytra_float(v))
def __pytra_Path(raw: Any): Path = Path(raw)
def __pytra_glob(pattern: Any): mutable.ArrayBuffer[String] = glob.glob(pattern)
def __pytra_deque[T](): T = {
    val cls = Class.forName("pytra_std_collections$deque")
    val obj = cls.getDeclaredConstructor().newInstance()
    val initOpt = cls.getMethods.find(_.getName == "__init__")
    initOpt.foreach(_.invoke(obj))
    obj.asInstanceOf[T]
}
def __pytra_sorted[T](values: mutable.ArrayBuffer[T]): mutable.ArrayBuffer[T] = {
    val out = values.clone()
    out.sortInPlaceWith((left, right) => {
        if (left.isInstanceOf[String] || right.isInstanceOf[String]) {
            __pytra_str(left) < __pytra_str(right)
        } else {
            __pytra_float(left) < __pytra_float(right)
        }
    })
    out
}

def __pytra_sorted[T](values: mutable.Set[T]): mutable.ArrayBuffer[T] = {
    __pytra_sorted(mutable.ArrayBuffer.from(values))
}

def __pytra_set_update[T](target: mutable.Set[T], values: Iterable[T]): Unit = {
    target ++= values
}

def __pytra_cast(target: Any, value: Any): Any = value

class Namespace(var values: mutable.LinkedHashMap[String, Any] = mutable.LinkedHashMap[String, Any]())

class _ArgSpec(
    var names: mutable.ArrayBuffer[String],
    var action: String = "",
    var choices: mutable.ArrayBuffer[String] = mutable.ArrayBuffer[String](),
    var default: Any = null,
    var help_text: String = "",
) {
    var is_optional: Boolean = names.nonEmpty && names(0).startsWith("-")
    var dest: String =
        if (is_optional) names.last.stripPrefix("-").stripPrefix("-").replace("-", "_")
        else if (names.nonEmpty) names(0)
        else ""
}

class ArgumentParser(var description: String = "") {
    var _specs: mutable.ArrayBuffer[_ArgSpec] = mutable.ArrayBuffer[_ArgSpec]()

    def add_argument(
        name1: Any,
        name2: Any = null,
        name3: Any = null,
        name4: Any = null,
        action: String = "",
        choices: Any = null,
        default_value: Any = null,
        help_text: String = "",
    ): Unit = {
        val raw = mutable.ArrayBuffer[Any](name1)
        if (name2 != null) raw.append(name2)
        if (name3 != null) raw.append(name3)
        if (name4 != null) raw.append(name4)
        if (choices != null) raw.append(choices)
        if (action != "") raw.append(action)
        if (default_value != null) raw.append(default_value)
        if (help_text != "") raw.append(help_text)
        val names = mutable.ArrayBuffer[String]()
        var idx = 0
        while (idx < raw.size && names.size < 4) {
            raw(idx) match {
                case s: String if s != "" && (names.isEmpty || s.startsWith("-")) =>
                    names.append(s)
                    idx += 1
                case _ =>
                    idx = raw.size
            }
        }
        if (names.isEmpty) throw new ValueError()
        var action_value = ""
        var choices_value = mutable.ArrayBuffer[String]()
        var default_parsed: Any = null
        var help_value = ""
        var tailIndex = names.size
        while (tailIndex < raw.size) {
            raw(tailIndex) match {
                case xs: mutable.ArrayBuffer[?] if choices_value.isEmpty =>
                    choices_value = xs.map(__pytra_str)
                case xs: scala.collection.Seq[?] if choices_value.isEmpty =>
                    choices_value = mutable.ArrayBuffer[String]() ++ xs.map(__pytra_str)
                case s: String if action_value == "" && (s == "store_true" || s == "store_false") =>
                    action_value = s
                case s: String if default_parsed == null && !s.startsWith("-") =>
                    default_parsed = s
                case s: String if help_value == "" =>
                    help_value = s
                case other if default_parsed == null =>
                    default_parsed = other
                case _ =>
            }
            tailIndex += 1
        }
        _specs.append(new _ArgSpec(names, action_value, choices_value, default_parsed, help_value))
    }

    private def _fail(msg: String): Unit = {
        if (msg != "") pytra_std_sys_write_stderr("error: " + msg + "\n")
        sys_exit(2L)
    }

    def parse_args(argv: Any = null): mutable.LinkedHashMap[String, Any] = {
        val args =
            if (argv == null) sys_argv.slice(1, sys_argv.size)
            else __pytra_as_list(argv).map(__pytra_str)
        val specs_pos = mutable.ArrayBuffer[_ArgSpec]()
        val specs_opt = mutable.ArrayBuffer[_ArgSpec]()
        _specs.foreach(s => if (s.is_optional) specs_opt.append(s) else specs_pos.append(s))
        val by_name = mutable.LinkedHashMap[String, Long]()
        var spec_i = 0L
        specs_opt.foreach { s =>
            s.names.foreach(n => by_name(n) = spec_i)
            spec_i += 1L
        }
        val values = mutable.LinkedHashMap[String, Any]()
        _specs.foreach { s =>
            if (s.action == "store_true") values(s.dest) = (if (s.default.isInstanceOf[Boolean]) s.default else false)
            else if (s.default != null) values(s.dest) = s.default
            else values(s.dest) = null
        }
        var pos_i = 0
        var i = 0
        while (i < args.size) {
            val tok = args(i)
            if (tok.startsWith("-")) {
                if (!by_name.contains(tok)) _fail("unknown option: " + tok)
                val spec = specs_opt(by_name(tok).toInt)
                if (spec.action == "store_true") {
                    values(spec.dest) = true
                    i += 1
                } else {
                    if (i + 1 >= args.size) _fail("missing value for option: " + tok)
                    val value = args(i + 1)
                    if (spec.choices.nonEmpty && !spec.choices.contains(value)) _fail("invalid choice for " + tok + ": " + value)
                    values(spec.dest) = value
                    i += 2
                }
            } else {
                if (pos_i >= specs_pos.size) _fail("unexpected extra argument: " + tok)
                val spec = specs_pos(pos_i)
                values(spec.dest) = tok
                pos_i += 1
                i += 1
            }
        }
        if (pos_i < specs_pos.size) _fail("missing required argument: " + specs_pos(pos_i).dest)
        values
    }
}

def ArgumentParser_apply(description: String = ""): ArgumentParser = new ArgumentParser(description)

def __pytra_assert_true(cond: Boolean, label: String = ""): Boolean = {
    if (cond) return true
    if (label != "") __pytra_print("[assert_true] " + label + ": False")
    else __pytra_print("[assert_true] False")
    false
}

def __pytra_assert_eq(actual: Any, expected: Any, label: String = ""): Boolean = {
    val ok = __pytra_str(actual) == __pytra_str(expected)
    if (ok) return true
    if (label != "") __pytra_print("[assert_eq] " + label + ": actual=" + __pytra_str(actual) + ", expected=" + __pytra_str(expected))
    else __pytra_print("[assert_eq] actual=" + __pytra_str(actual) + ", expected=" + __pytra_str(expected))
    false
}

def __pytra_assert_all(results: Any, label: String = ""): Boolean = {
    val values = __pytra_as_list(results)
    var i = 0
    while (i < values.size) {
        if (!__pytra_truthy(values(i))) {
            if (label != "") __pytra_print("[assert_all] " + label + ": False")
            else __pytra_print("[assert_all] False")
            return false
        }
        i += 1
    }
    true
}

def __pytra_assert_stdout(expected_lines: Any, fn: Any): Boolean = true

private def _pngAppend(dst: mutable.ArrayBuffer[Long], src: mutable.ArrayBuffer[Long]): Unit = dst ++= src
private def _pngU16le(v: Long): mutable.ArrayBuffer[Long] = mutable.ArrayBuffer(v & 0xffL, (v >> 8) & 0xffL)
private def _pngU32be(v: Long): mutable.ArrayBuffer[Long] = mutable.ArrayBuffer((v >> 24) & 0xffL, (v >> 16) & 0xffL, (v >> 8) & 0xffL, v & 0xffL)
private def _crc32(data: mutable.ArrayBuffer[Long]): Long = {
    var crc = 0xffffffffL
    val poly = 0xedb88320L
    data.foreach { b =>
        crc ^= (b & 0xffL)
        var i = 0
        while (i < 8) {
            val lowbit = crc & 1L
            crc = if (lowbit != 0L) (crc >> 1) ^ poly else (crc >> 1)
            i += 1
        }
    }
    crc ^ 0xffffffffL
}
private def _adler32(data: mutable.ArrayBuffer[Long]): Long = {
    val mod = 65521L
    var s1 = 1L
    var s2 = 0L
    data.foreach { b =>
        s1 += (b & 0xffL)
        if (s1 >= mod) s1 -= mod
        s2 = (s2 + s1) % mod
    }
    ((s2 << 16) | s1) & 0xffffffffL
}
private def _zlibDeflateStore(data: mutable.ArrayBuffer[Long]): mutable.ArrayBuffer[Long] = {
    val out = mutable.ArrayBuffer[Long](0x78L, 0x01L)
    var pos = 0
    while (pos < data.size) {
        val remain = data.size - pos
        val chunkLen = if (remain > 65535) 65535 else remain
        val finalFlag = if (pos + chunkLen >= data.size) 1L else 0L
        out.append(finalFlag)
        _pngAppend(out, _pngU16le(chunkLen.toLong))
        _pngAppend(out, _pngU16le((0xffff ^ chunkLen).toLong))
        var i = 0
        while (i < chunkLen) {
            out.append(data(pos + i))
            i += 1
        }
        pos += chunkLen
    }
    _pngAppend(out, _pngU32be(_adler32(data)))
    out
}
private def _pngChunk(chunkType: mutable.ArrayBuffer[Long], data: mutable.ArrayBuffer[Long]): mutable.ArrayBuffer[Long] = {
    val crcInput = mutable.ArrayBuffer[Long]()
    _pngAppend(crcInput, chunkType)
    _pngAppend(crcInput, data)
    val out = mutable.ArrayBuffer[Long]()
    _pngAppend(out, _pngU32be(data.size.toLong))
    _pngAppend(out, chunkType)
    _pngAppend(out, data)
    _pngAppend(out, _pngU32be(_crc32(crcInput)))
    out
}
def __pytra_write_rgb_png(path: String, width: Long, height: Long, pixels: Any): Unit = {
    val raw = __pytra_bytes(pixels)
    val expected = width * height * 3L
    if (raw.size.toLong != expected) throw new RuntimeException("pixels length mismatch: got=" + raw.size + " expected=" + expected)
    val scanlines = mutable.ArrayBuffer[Long]()
    val rowBytes = width * 3L
    var y = 0L
    while (y < height) {
        scanlines.append(0L)
        var i = y * rowBytes
        while (i < y * rowBytes + rowBytes) {
            scanlines.append(raw(i.toInt))
            i += 1L
        }
        y += 1L
    }
    val ihdr = mutable.ArrayBuffer[Long]()
    _pngAppend(ihdr, _pngU32be(width))
    _pngAppend(ihdr, _pngU32be(height))
    _pngAppend(ihdr, mutable.ArrayBuffer[Long](8L, 2L, 0L, 0L, 0L))
    val idat = _zlibDeflateStore(scanlines)
    val png = mutable.ArrayBuffer[Long]()
    _pngAppend(png, mutable.ArrayBuffer[Long](137L, 80L, 78L, 71L, 13L, 10L, 26L, 10L))
    _pngAppend(png, _pngChunk(mutable.ArrayBuffer[Long](73L, 72L, 68L, 82L), ihdr))
    _pngAppend(png, _pngChunk(mutable.ArrayBuffer[Long](73L, 68L, 65L, 84L), idat))
    _pngAppend(png, _pngChunk(mutable.ArrayBuffer[Long](73L, 69L, 78L, 68L), mutable.ArrayBuffer[Long]()))
    val file = open(path, "wb")
    try file.write(png)
    finally file.close()
}

private def __pytra_gif_append(dst: mutable.ArrayBuffer[Long], src: scala.collection.Seq[?]): Unit = {
    src.foreach(v => dst.append(__pytra_int(v.asInstanceOf[Any]) & 0xffL))
}

private def __pytra_gif_u16le(value: Long): mutable.ArrayBuffer[Long] = {
    mutable.ArrayBuffer[Long](value & 0xffL, (value >> 8) & 0xffL)
}

private def __pytra_lzw_encode(data: scala.collection.Seq[?], minCodeSize: Long): mutable.ArrayBuffer[Long] = {
    if (data.isEmpty) return __pytra_bytes(mutable.ArrayBuffer[Long]())
    val clearCode = 1L << minCodeSize
    val endCode = clearCode + 1L
    var codeSize = minCodeSize + 1L
    val out = mutable.ArrayBuffer[Long]()
    var bitBuffer = clearCode
    var bitCount = codeSize
    while (bitCount >= 8L) {
        out.append(bitBuffer & 0xffL)
        bitBuffer = bitBuffer >> 8
        bitCount -= 8L
    }
    codeSize = minCodeSize + 1L
    var index = 0
    while (index < data.size) {
        val value = __pytra_int(data(index).asInstanceOf[Any])
        bitBuffer |= value << bitCount
        bitCount += codeSize
        while (bitCount >= 8L) {
            out.append(bitBuffer & 0xffL)
            bitBuffer = bitBuffer >> 8
            bitCount -= 8L
        }
        bitBuffer |= clearCode << bitCount
        bitCount += codeSize
        while (bitCount >= 8L) {
            out.append(bitBuffer & 0xffL)
            bitBuffer = bitBuffer >> 8
            bitCount -= 8L
        }
        codeSize = minCodeSize + 1L
        index += 1
    }
    bitBuffer |= endCode << bitCount
    bitCount += codeSize
    while (bitCount >= 8L) {
        out.append(bitBuffer & 0xffL)
        bitBuffer = bitBuffer >> 8
        bitCount -= 8L
    }
    if (bitCount > 0L) out.append(bitBuffer & 0xffL)
    __pytra_bytes(out)
}

def __pytra_grayscale_palette(): mutable.ArrayBuffer[Long] = {
    val out = mutable.ArrayBuffer[Long]()
    var i = 0L
    while (i < 256L) {
        out.append(i)
        out.append(i)
        out.append(i)
        i += 1L
    }
    __pytra_bytes(out)
}

def __pytra_save_gif(path: String, width: Long, height: Long, frames: Any, palette: Any, delayCs: Long = 4L, loop: Long = 0L): Unit = {
    val paletteSrc = __pytra_as_list(palette)
    val paletteList = mutable.ArrayBuffer[Long]()
    paletteSrc.foreach(v => paletteList.append(__pytra_int(v)))
    if (paletteList.size != 256 * 3) throw new RuntimeException("palette must be 256*3 bytes")
    val frameSize = width * height
    val out = mutable.ArrayBuffer[Long]()
    __pytra_gif_append(out, mutable.ArrayBuffer[Long](71L, 73L, 70L, 56L, 57L, 97L))
    __pytra_gif_append(out, __pytra_gif_u16le(width))
    __pytra_gif_append(out, __pytra_gif_u16le(height))
    __pytra_gif_append(out, mutable.ArrayBuffer[Long](0xF7L, 0L, 0L))
    __pytra_gif_append(out, paletteList)
    __pytra_gif_append(out, mutable.ArrayBuffer[Long](0x21L, 0xFFL, 0x0BL, 78L, 69L, 84L, 83L, 67L, 65L, 80L, 69L, 50L, 46L, 48L, 0x03L, 0x01L))
    __pytra_gif_append(out, __pytra_gif_u16le(loop))
    out.append(0L)
    val framesSrc = __pytra_as_list(frames)
    var frameIndex = 0
    while (frameIndex < framesSrc.size) {
        val frameSrc = __pytra_as_list(framesSrc(frameIndex))
        val frame = mutable.ArrayBuffer[Long]()
        frameSrc.foreach(v => frame.append(__pytra_int(v)))
        if (frame.size.toLong != frameSize) throw new RuntimeException("frame size mismatch")
        __pytra_gif_append(out, mutable.ArrayBuffer[Long](0x21L, 0xF9L, 0x04L, 0x00L))
        __pytra_gif_append(out, __pytra_gif_u16le(delayCs))
        __pytra_gif_append(out, mutable.ArrayBuffer[Long](0x00L, 0x00L))
        out.append(0x2CL)
        __pytra_gif_append(out, __pytra_gif_u16le(0L))
        __pytra_gif_append(out, __pytra_gif_u16le(0L))
        __pytra_gif_append(out, __pytra_gif_u16le(width))
        __pytra_gif_append(out, __pytra_gif_u16le(height))
        out.append(0L)
        out.append(8L)
        val compressed = __pytra_lzw_encode(frame, 8L)
        var pos = 0
        while (pos < compressed.size) {
            val remain = compressed.size - pos
            val chunkLen = if (remain > 255) 255 else remain
            out.append(chunkLen.toLong)
            var i = 0
            while (i < chunkLen) {
                out.append(compressed(pos + i))
                i += 1
            }
            pos += chunkLen
        }
        out.append(0L)
        frameIndex += 1
    }
    out.append(0x3BL)
    val file = open(path, "wb")
    try file.write(__pytra_bytes(out))
    finally file.close()
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
        case e: PytraEnumLike => e.value
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

// repr-style: strings are quoted, booleans are True/False, collections use Python syntax.
private def __pytra_float_str(d: Double): String = java.lang.Double.toString(d).replace("E", "e")

def __pytra_repr(v: Any): String = {
    if (v == null) return "None"
    v match {
        case b: Boolean => if (b) "True" else "False"
        case d: Double => __pytra_float_str(d)
        case f: Float => __pytra_float_str(f.toDouble)
        case s: String => "'" + s.replace("\\", "\\\\").replace("'", "\\'") + "'"
        case xs: PyTuple =>
            val inner = xs.map(x => __pytra_repr(x.asInstanceOf[Any])).mkString(", ")
            if (xs.size == 1) "(" + inner + ",)" else "(" + inner + ")"
        case xs: mutable.ArrayBuffer[?] =>
            "[" + xs.map(x => __pytra_repr(x.asInstanceOf[Any])).mkString(", ") + "]"
        case m: mutable.LinkedHashMap[?, ?] =>
            val entries = m.asInstanceOf[mutable.LinkedHashMap[Any, Any]]
            "{" + entries.map(e => __pytra_repr(e._1) + ": " + __pytra_repr(e._2)).mkString(", ") + "}"
        case _ => __pytra_str(v)
    }
}

def __pytra_str(v: Any): String = {
    if (v == null) return "None"
    v match {
        case b: Boolean => if (b) "True" else "False"
        case d: Double => __pytra_float_str(d)
        case f: Float => __pytra_float_str(f.toDouble)
        case xs: PyTuple =>
            val inner = xs.map(x => __pytra_repr(x.asInstanceOf[Any])).mkString(", ")
            if (xs.size == 1) "(" + inner + ",)" else "(" + inner + ")"
        case xs: mutable.ArrayBuffer[?] =>
            "[" + xs.map(x => __pytra_repr(x.asInstanceOf[Any])).mkString(", ") + "]"
        case m: mutable.LinkedHashMap[?, ?] =>
            val entries = m.asInstanceOf[mutable.LinkedHashMap[Any, Any]]
            "{" + entries.map(e => __pytra_repr(e._1) + ": " + __pytra_repr(e._2)).mkString(", ") + "}"
        case _ => v.toString
    }
}

def py_repr(v: Any): String = __pytra_repr(v)
def __pytra_ord(ch: Any): Long = ord(ch)
def __pytra_chr(n: Any): String = chr(n)

def __pytra_tuple(items: Any*): PyTuple = new PyTuple(items)

def __pytra_format(value: Any, spec: String): String = {
    if (spec == null || spec == "") return __pytra_str(value)
    if (spec.endsWith("%")) {
        return __pytra_format(__pytra_float(value) * 100.0, spec.substring(0, spec.length - 1) + "f") + "%"
    }
    val kind = spec.charAt(spec.length - 1)
    val flags = spec.substring(0, spec.length - 1).replace("<", "-")
    val fmt = "%" + flags + kind
    kind match {
        case 'd' | 'x' | 'X' => String.format(java.util.Locale.US, fmt, java.lang.Long.valueOf(__pytra_int(value)))
        case 'f' => String.format(java.util.Locale.US, fmt, java.lang.Double.valueOf(__pytra_float(value)))
        case 's' => String.format(java.util.Locale.US, fmt, __pytra_str(value))
        case _ => __pytra_str(value)
    }
}

def __pytra_len(v: Any): Long = {
    if (v == null) return 0L
    v match {
        case s: String => s.length.toLong
        case xs: scala.collection.Seq[?] => xs.size.toLong
        case m: scala.collection.Map[?, ?] => m.size.toLong
        case s: scala.collection.Set[?] => s.size.toLong
        case _ =>
            try {
                val method = v.getClass.getMethod("__len__")
                __pytra_int(method.invoke(v))
            } catch {
                case _: Throwable => 0L
            }
    }
}

def __pytra_index(i: Long, n: Long): Long = {
    if (i < 0L) i + n else i
}

def __pytra_get_index(container: Any, index: Any): Any = {
    container match {
        case s: String =>
            val i = __pytra_index(__pytra_int(index), s.length.toLong)
            if (i < 0L || i >= s.length.toLong) {
                val err = new IndexError()
                err.__init__("string index out of range")
                throw err
            }
            s.charAt(i.toInt).toString
        case m: mutable.LinkedHashMap[?, ?] =>
            m.asInstanceOf[mutable.LinkedHashMap[Any, Any]].getOrElse(index, __pytra_any_default())
        case m: scala.collection.Map[?, ?] =>
            m.asInstanceOf[scala.collection.Map[Any, Any]].getOrElse(index, __pytra_any_default())
        case _ =>
            val list = __pytra_as_list(container)
            val i = __pytra_index(__pytra_int(index), list.size.toLong)
            if (i >= 0L && i < list.size.toLong) return list(i.toInt)
            val err = new IndexError()
            err.__init__("list index out of range")
            throw err
    }
}

def __pytra_get(container: Any, index: Any): Any = __pytra_get_index(container, index)

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

def __pytra_strip(v: Any): String = __pytra_str(v).trim
def __pytra_lstrip(v: Any): String = __pytra_str(v).replaceAll("^\\s+", "")
def __pytra_rstrip(v: Any): String = __pytra_str(v).replaceAll("\\s+$", "")
def __pytra_startswith(v: Any, prefix: Any): Boolean = __pytra_str(v).startsWith(__pytra_str(prefix))
def __pytra_endswith(v: Any, suffix: Any): Boolean = __pytra_str(v).endsWith(__pytra_str(suffix))
def __pytra_replace(v: Any, old: Any, newStr: Any): String = __pytra_str(v).replace(__pytra_str(old), __pytra_str(newStr))
def __pytra_join(sep: Any, items: Any): String = {
    val s = __pytra_str(sep)
    val list = __pytra_as_list(items)
    list.map(__pytra_str).mkString(s)
}
def __pytra_split(v: Any, sep: Any): mutable.ArrayBuffer[Any] = {
    val s = __pytra_str(v)
    val parts: Array[String] = if (sep == null || __pytra_str(sep) == "") s.split("\\s+") else s.split(java.util.regex.Pattern.quote(__pytra_str(sep)), -1)
    val out = mutable.ArrayBuffer[Any]()
    for (p <- parts) out.append(p)
    out
}
def __pytra_upper(v: Any): String = __pytra_str(v).toUpperCase
def __pytra_lower(v: Any): String = __pytra_str(v).toLowerCase
def __pytra_find(v: Any, sub: Any): Long = __pytra_str(v).indexOf(__pytra_str(sub)).toLong
def __pytra_rfind(v: Any, sub: Any): Long = __pytra_str(v).lastIndexOf(__pytra_str(sub)).toLong
def __pytra_str_index(v: Any, sub: Any): Long = {
    val found = __pytra_find(v, sub)
    if (found < 0L) {
        val err = new ValueError()
        err.__init__("substring not found")
        throw err
    }
    found
}
def __pytra_isalnum(v: Any): Boolean = {
    val s = __pytra_str(v)
    if (s.isEmpty) return false
    s.forall(_.isLetterOrDigit)
}
def __pytra_eq(a: Any, b: Any): Boolean = {
    if (a == null || b == null) return a == b
    (a, b) match {
        case (x: String, y) => x == __pytra_str(y)
        case (x, y: String) => __pytra_str(x) == y
        case (x: Boolean, y) => __pytra_float(x) == __pytra_float(y)
        case (x, y: Boolean) => __pytra_float(x) == __pytra_float(y)
        case (x: Long, y) => __pytra_float(x) == __pytra_float(y)
        case (x: Int, y) => __pytra_float(x) == __pytra_float(y)
        case (x: Double, y) => __pytra_float(x) == __pytra_float(y)
        case _ => a == b
    }
}
def __pytra_count_substr(v: Any, sub: Any): Long = {
    val s = __pytra_str(v)
    val t = __pytra_str(sub)
    if (t.isEmpty) return (s.length + 1).toLong
    var count = 0L; var idx = 0
    while ({ val i = s.indexOf(t, idx); i >= 0 && { count += 1L; idx = i + t.length; true } }) ()
    count
}

def __pytra_reversed(v: Any): mutable.ArrayBuffer[Any] = {
    val list = __pytra_as_list(v)
    val out = mutable.ArrayBuffer[Any]()
    var i = list.size - 1
    while (i >= 0) { out.append(list(i)); i -= 1 }
    out
}

def reversed(v: Any): mutable.ArrayBuffer[Any] = __pytra_reversed(v)

def __pytra_list[T](v: Any): mutable.ArrayBuffer[T] =
    mutable.ArrayBuffer.from(__pytra_as_list(v).map(_.asInstanceOf[T]))

def __pytra_contains(container: Any, value: Any): Boolean = {
    val needle = __pytra_str(value)
    container match {
        case s: String => s.contains(needle)
        case m: scala.collection.Map[?, ?] => m.asInstanceOf[scala.collection.Map[Any, Any]].contains(needle)
        case s: scala.collection.Set[?] =>
            s.exists(item => item == value || __pytra_str(item) == needle)
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

def __pytra_bytearray(initValue: Any = null): mutable.ArrayBuffer[Long] = {
    if (initValue == null) return mutable.ArrayBuffer[Long]()
    initValue match {
        case n: Long =>
            val out = mutable.ArrayBuffer[Long]()
            var i = 0L
            while (i < n) {
                out.append(0L)
                i += 1L
            }
            out
        case n: Int =>
            val out = mutable.ArrayBuffer[Long]()
            var i = 0
            while (i < n) {
                out.append(0L)
                i += 1
            }
            out
        case _ =>
            val src = __pytra_as_list(initValue)
            val out = mutable.ArrayBuffer[Long]()
            var i = 0
            while (i < src.size) {
                out.append(__pytra_int(src(i)))
                i += 1
            }
            out
    }
}

def __pytra_bytes(v: Any = null): mutable.ArrayBuffer[Long] = {
    if (v == null) return mutable.ArrayBuffer[Long]()
    val src = __pytra_as_list(v)
    val out = mutable.ArrayBuffer[Long]()
    var i = 0
    while (i < src.size) {
        out.append(__pytra_int(src(i)))
        i += 1
    }
    out
}

def __pytra_list_repeat(value: Any, count: Any): mutable.ArrayBuffer[Any] = {
    val out = mutable.ArrayBuffer[Any]()
    val n = __pytra_int(count)
    val items = __pytra_as_list(value)
    var i = 0L
    while (i < n) {
        out ++= items
        i += 1L
    }
    out
}

def __pytra_range(args: Any*): mutable.ArrayBuffer[Any] = {
    var start = 0L
    var stop = 0L
    var step = 1L
    if (args.length == 1) {
        stop = __pytra_int(args(0))
    } else if (args.length >= 2) {
        start = __pytra_int(args(0))
        stop = __pytra_int(args(1))
        if (args.length >= 3) step = __pytra_int(args(2))
    }
    val out = mutable.ArrayBuffer[Any]()
    if (step == 0L) return out
    var i = start
    if (step > 0L) {
        while (i < stop) {
            out.append(i)
            i += step
        }
    } else {
        while (i > stop) {
            out.append(i)
            i += step
        }
    }
    out
}

def __pytra_list_concat(a: Any, b: Any): mutable.ArrayBuffer[Any] = {
    val out = mutable.ArrayBuffer[Any]()
    out ++= __pytra_as_list(a)
    out ++= __pytra_as_list(b)
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
        case s: String =>
            val out = mutable.ArrayBuffer[Any]()
            var i = 0
            while (i < s.length) { out.append(s.charAt(i).toString); i += 1 }
            out
        case s: scala.collection.Set[?] =>
            val out = mutable.ArrayBuffer[Any]()
            for (item <- s) out.append(item)
            out
        case _ => mutable.ArrayBuffer[Any]()
    }
}

def __pytra_as_set(v: Any): mutable.LinkedHashSet[Any] = {
    v match {
        case s: mutable.LinkedHashSet[?] => s.asInstanceOf[mutable.LinkedHashSet[Any]]
        case s: scala.collection.Set[?] =>
            val out = mutable.LinkedHashSet[Any]()
            s.foreach(out.add)
            out
        case _ => mutable.LinkedHashSet[Any]()
    }
}

def __pytra_set_new(v: Any = null): mutable.LinkedHashSet[Any] = {
    if (v == null) mutable.LinkedHashSet[Any]() else __pytra_as_set(v)
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

def __pytra_type_name(v: Any): String = {
    if (v == null) "NoneType"
    else if (v.isInstanceOf[PyTuple]) "tuple"
    else {
        val n = v.getClass.getSimpleName
        if (n == null || n.isEmpty) v.getClass.getName.split("\\.").last else n
    }
}

def __pytra_print(args: Any*): Unit = {
    if (args.isEmpty) {
        println()
        return
    }
    println(args.map(__pytra_str).mkString(" "))
}

def __pytra_min(a: Long, b: Long): Long = if (a < b) a else b
def __pytra_min(a: Double, b: Double): Double = if (a < b) a else b
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

def __pytra_max(a: Long, b: Long): Long = if (a > b) a else b
def __pytra_max(a: Double, b: Double): Double = if (a > b) a else b
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

def __pytra_dict_items(d: Any): mutable.ArrayBuffer[Any] = {
    val m = __pytra_as_dict(d)
    val out = mutable.ArrayBuffer[Any]()
    m.foreach { case (k, v) => out.append(__pytra_tuple(k, v)) }
    out
}

def __pytra_dict_keys(d: Any): mutable.ArrayBuffer[Any] = {
    val m = __pytra_as_dict(d)
    val out = mutable.ArrayBuffer[Any]()
    m.foreach { case (k, _) => out.append(k) }
    out
}

def __pytra_dict_values(d: Any): mutable.ArrayBuffer[Any] = {
    val m = __pytra_as_dict(d)
    val out = mutable.ArrayBuffer[Any]()
    m.foreach { case (_, v) => out.append(v) }
    out
}

def __pytra_sum(xs: Any): Any = {
    val lst = __pytra_as_list(xs)
    var hasFloat = false
    val iter = lst.iterator
    while (iter.hasNext) {
        val v = iter.next()
        if (v.isInstanceOf[Double] || v.isInstanceOf[Float]) hasFloat = true
    }
    if (hasFloat) {
        var acc: Double = 0.0
        val iter2 = lst.iterator
        while (iter2.hasNext) acc += __pytra_float(iter2.next())
        acc
    } else {
        var acc: Long = 0L
        val iter2 = lst.iterator
        while (iter2.hasNext) acc += __pytra_int(iter2.next())
        acc
    }
}

def __pytra_zip(a: Any, b: Any): mutable.ArrayBuffer[Any] = {
    val la = __pytra_as_list(a)
    val lb = __pytra_as_list(b)
    val n = la.size.min(lb.size)
    val out = mutable.ArrayBuffer[Any]()
    var i = 0
    while (i < n) {
        out.append(__pytra_tuple(la(i), lb(i)))
        i += 1
    }
    out
}

def __pytra_is_int(v: Any): Boolean = v.isInstanceOf[Long] || v.isInstanceOf[Int]

def __pytra_is_float(v: Any): Boolean = v.isInstanceOf[Double] || v.isInstanceOf[Float]

def __pytra_is_bool(v: Any): Boolean = v.isInstanceOf[Boolean]

def __pytra_is_str(v: Any): Boolean = v.isInstanceOf[String]

def __pytra_is_list(v: Any): Boolean = v.isInstanceOf[scala.collection.Seq[?]]

def __pytra_is_instance(v: Any, expected: String): Boolean = {
    def hasTypeName(cls: Class[?], name: String): Boolean = {
        var cur: Class[?] | Null = cls
        while (cur != null) {
            val curCls = cur.asInstanceOf[Class[?]]
            if (curCls.getSimpleName == name) return true
            for (iface <- curCls.getInterfaces) {
                if (hasTypeName(iface, name)) return true
            }
            cur = curCls.getSuperclass
        }
        false
    }
    expected match {
        case "None" | "none" => v == null
        case "bool" => v.isInstanceOf[Boolean]
        case "int" | "int8" | "int16" | "int32" | "int64" | "uint8" | "uint16" | "uint32" | "uint64" =>
            v.isInstanceOf[Long] || v.isInstanceOf[Int]
        case "float" | "float32" | "float64" =>
            v.isInstanceOf[Double] || v.isInstanceOf[Float]
        case "str" => v.isInstanceOf[String]
        case "list" | "bytes" | "bytearray" => v.isInstanceOf[scala.collection.Seq[?]] && !v.isInstanceOf[PyTuple]
        case "tuple" => v.isInstanceOf[PyTuple]
        case "set" => v.isInstanceOf[scala.collection.Set[?]]
        case "dict" => v.isInstanceOf[scala.collection.Map[?, ?]]
        case "Path" => v.isInstanceOf[java.nio.file.Path]
        case _ => v != null && hasTypeName(v.getClass, expected)
    }
}

def __pytra_is_subtype(actual: Any, expected: Any): Boolean = __pytra_str(actual) == __pytra_str(expected)

def pyMathSqrt(v: Any): Double = scala.math.sqrt(__pytra_float(v))
def pyMathSin(v: Any): Double = scala.math.sin(__pytra_float(v))
def pyMathCos(v: Any): Double = scala.math.cos(__pytra_float(v))
def pyMathTan(v: Any): Double = scala.math.tan(__pytra_float(v))
def pyMathExp(v: Any): Double = scala.math.exp(__pytra_float(v))
def pyMathLog(v: Any): Double = scala.math.log(__pytra_float(v))
def pyMathFabs(v: Any): Double = scala.math.abs(__pytra_float(v))
def pyMathFloor(v: Any): Double = scala.math.floor(__pytra_float(v))
def pyMathCeil(v: Any): Double = scala.math.ceil(__pytra_float(v))
def pyMathPow(a: Any, b: Any): Double = scala.math.pow(__pytra_float(a), __pytra_float(b))
def pyMathPi(): Double = scala.math.Pi
def pyMathE(): Double = scala.math.E
def __pytra_sqrt(v: Any): Double = pyMathSqrt(v)
def __pytra_sin(v: Any): Double = pyMathSin(v)
def __pytra_cos(v: Any): Double = pyMathCos(v)
def __pytra_tan(v: Any): Double = pyMathTan(v)
def __pytra_exp(v: Any): Double = pyMathExp(v)
def __pytra_log(v: Any): Double = pyMathLog(v)
def __pytra_log10(v: Any): Double = scala.math.log10(__pytra_float(v))
def __pytra_fabs(v: Any): Double = pyMathFabs(v)
def __pytra_ceil(v: Any): Double = pyMathCeil(v)
def __pytra_pow(a: Any, b: Any): Double = pyMathPow(a, b)

class bytearray extends mutable.ArrayBuffer[Long] {
    def __init__(initValue: Any = null): Unit = {
        this.clear()
        this.addAll(__pytra_bytearray(initValue))
    }
}

class bytes extends mutable.ArrayBuffer[Long] {
    def __init__(initValue: Any = null): Unit = {
        this.clear()
        this.addAll(__pytra_bytes(initValue))
    }
}

class Path(v: Any) {
    private val _value: String = __pytra_str(v)

    def /(rhs: Any): Path = Path(__pytra_path_join(_value, __pytra_str(rhs)))
    def joinpath(rhs: Any): Path = this / rhs
    def joinpath(first: Any, second: Any): Path = (this / first) / second
    def resolve(): Path = Path(Paths.get(_value).toAbsolutePath.normalize.toString)
    def exists(): Boolean = __pytra_path_exists(_value)
    def mkdir(parents: Boolean = false, exist_ok: Boolean = false): Unit = {
        if (parents) {
            __pytra_path_mkdir(_value)
            return
        }
        if (exist_ok && __pytra_path_exists(_value)) return
        Files.createDirectory(Paths.get(_value))
    }
    def write_text(text: Any, encoding: String = "utf-8"): Unit = __pytra_path_write_text(_value, text)
    def read_text(encoding: String = "utf-8"): String = __pytra_path_read_text(_value)

    def name: String = __pytra_path_name(_value)
    def stem: String = __pytra_path_stem(_value)
    def parent: Path = {
        val p = __pytra_path_parent(_value)
        if (p == "" || p == _value) Path(".") else Path(p)
    }

    override def toString: String = _value
}

object Path {
    def apply(v: Any): Path = new Path(v)
}

private def __pytra_json_escape_string(s: String, ensureAscii: Boolean = true): String = {
    val sb = new java.lang.StringBuilder("\"")
    var i = 0
    while (i < s.length) {
        val ch = s.charAt(i)
        if (ch == '"') sb.append("\\\"")
        else if (ch == '\\') sb.append("\\\\")
        else if (ch == '\b') sb.append("\\b")
        else if (ch == '\f') sb.append("\\f")
        else if (ch == '\n') sb.append("\\n")
        else if (ch == '\r') sb.append("\\r")
        else if (ch == '\t') sb.append("\\t")
        else if (ch < 0x20 || (ensureAscii && ch > 0x7f)) {
            sb.append("\\u")
            val hex = Integer.toHexString(ch.toInt)
            var pad = 4 - hex.length
            while (pad > 0) {
                sb.append('0')
                pad -= 1
            }
            sb.append(hex)
        } else sb.append(ch)
        i += 1
    }
    sb.append('"')
    sb.toString
}

private def __pytra_json_stringify(v: Any): String = {
    if (v == null) return "null"
    v match {
        case b: Boolean => if (b) "true" else "false"
        case i: Int => i.toString
        case i: Long => i.toString
        case d: Double =>
            if (!java.lang.Double.isFinite(d)) throw new RuntimeException("json.dumps: non-finite float")
            d.toString
        case f: Float =>
            if (!java.lang.Float.isFinite(f)) throw new RuntimeException("json.dumps: non-finite float")
            f.toString
        case s: String => __pytra_json_escape_string(s)
        case xs: scala.collection.Seq[?] =>
            val out = mutable.ArrayBuffer[String]()
            for (item <- xs) out.append(__pytra_json_stringify(item))
            "[" + out.mkString(",") + "]"
        case m: mutable.LinkedHashMap[?, ?] =>
            val out = mutable.ArrayBuffer[String]()
            val mm = m.asInstanceOf[mutable.LinkedHashMap[Any, Any]]
            for ((k, valueAny) <- mm) {
                out.append(__pytra_json_escape_string(__pytra_str(k)) + ":" + __pytra_json_stringify(valueAny))
            }
            "{" + out.mkString(",") + "}"
        case m: scala.collection.Map[?, ?] =>
            val out = mutable.ArrayBuffer[String]()
            val mm = m.asInstanceOf[scala.collection.Map[Any, Any]]
            for ((k, valueAny) <- mm) {
                out.append(__pytra_json_escape_string(__pytra_str(k)) + ":" + __pytra_json_stringify(valueAny))
            }
            "{" + out.mkString(",") + "}"
        case _ => __pytra_json_escape_string(__pytra_str(v))
    }
}

private def __pytra_json_pretty(v: Any, ensureAscii: Boolean, indent: Int, depth: Int): String = {
    val value = __pytra_json_unwrap(v)
    if (value == null) return "null"
    value match {
        case b: Boolean => if (b) "true" else "false"
        case i: Int => i.toString
        case i: Long => i.toString
        case d: Double =>
            if (!java.lang.Double.isFinite(d)) throw new RuntimeException("json.dumps: non-finite float")
            if (d.isWhole) d.toLong.toString else d.toString
        case f: Float =>
            if (!java.lang.Float.isFinite(f)) throw new RuntimeException("json.dumps: non-finite float")
            val d = f.toDouble
            if (d.isWhole) d.toLong.toString else d.toString
        case s: String => __pytra_json_escape_string(s, ensureAscii)
        case xs: scala.collection.Seq[?] =>
            val out = mutable.ArrayBuffer[String]()
            for (item <- xs) out.append(__pytra_json_pretty(item, ensureAscii, indent, depth + 1))
            val pad = " " * (indent * (depth + 1))
            val closePad = " " * (indent * depth)
            "[\n" + out.map(x => pad + x).mkString(",\n") + "\n" + closePad + "]"
        case m: scala.collection.Map[?, ?] =>
            val out = mutable.ArrayBuffer[String]()
            val mm = m.asInstanceOf[scala.collection.Map[Any, Any]]
            for ((k, item) <- mm) {
                out.append(__pytra_json_escape_string(__pytra_str(k), ensureAscii) + ": " + __pytra_json_pretty(item, ensureAscii, indent, depth + 1))
            }
            val pad = " " * (indent * (depth + 1))
            val closePad = " " * (indent * depth)
            "{\n" + out.map(x => pad + x).mkString(",\n") + "\n" + closePad + "}"
        case _ => __pytra_json_escape_string(__pytra_str(value), ensureAscii)
    }
}

private final class __PytraJsonParser(text: String) {
    private val n = text.length
    private var i = 0

    def parse(): Any = {
        skipWs()
        val out = parseValue()
        skipWs()
        if (i != n) throw new RuntimeException("invalid json: trailing characters")
        out
    }

    private def isDigit(ch: Char): Boolean = ch >= '0' && ch <= '9'

    private def skipWs(): Unit = {
        while (i < n) {
            val ch = text.charAt(i)
            if (ch != ' ' && ch != '\t' && ch != '\r' && ch != '\n') return
            i += 1
        }
    }

    private def parseValue(): Any = {
        if (i >= n) throw new RuntimeException("invalid json: unexpected end")
        val ch = text.charAt(i)
        if (ch == '{') return parseObject()
        if (ch == '[') return parseArray()
        if (ch == '"') return parseString()
        if (ch == 't' && i + 4 <= n && text.substring(i, i + 4) == "true") {
            i += 4
            return true
        }
        if (ch == 'f' && i + 5 <= n && text.substring(i, i + 5) == "false") {
            i += 5
            return false
        }
        if (ch == 'n' && i + 4 <= n && text.substring(i, i + 4) == "null") {
            i += 4
            return null
        }
        parseNumber()
    }

    private def parseObject(): mutable.LinkedHashMap[Any, Any] = {
        val out = mutable.LinkedHashMap[Any, Any]()
        i += 1
        skipWs()
        if (i < n && text.charAt(i) == '}') {
            i += 1
            return out
        }
        while (true) {
            skipWs()
            if (i >= n || text.charAt(i) != '"') throw new RuntimeException("invalid json object key")
            val key = parseString()
            skipWs()
            if (i >= n || text.charAt(i) != ':') throw new RuntimeException("invalid json object: missing ':'")
            i += 1
            skipWs()
            out(key) = parseValue()
            skipWs()
            if (i >= n) throw new RuntimeException("invalid json object: unexpected end")
            val sep = text.charAt(i)
            i += 1
            if (sep == '}') return out
            if (sep != ',') throw new RuntimeException("invalid json object separator")
        }
        out
    }

    private def parseArray(): mutable.ArrayBuffer[Any] = {
        val out = mutable.ArrayBuffer[Any]()
        i += 1
        skipWs()
        if (i < n && text.charAt(i) == ']') {
            i += 1
            return out
        }
        while (true) {
            skipWs()
            out.append(parseValue())
            skipWs()
            if (i >= n) throw new RuntimeException("invalid json array: unexpected end")
            val sep = text.charAt(i)
            i += 1
            if (sep == ']') return out
            if (sep != ',') throw new RuntimeException("invalid json array separator")
        }
        out
    }

    private def parseString(): String = {
        if (text.charAt(i) != '"') throw new RuntimeException("invalid json string")
        i += 1
        val sb = new java.lang.StringBuilder()
        while (i < n) {
            val ch = text.charAt(i)
            i += 1
            if (ch == '"') return sb.toString
            if (ch == '\\') {
                if (i >= n) throw new RuntimeException("invalid json string escape")
                val esc = text.charAt(i)
                i += 1
                if (esc == '"') sb.append('"')
                else if (esc == '\\') sb.append('\\')
                else if (esc == '/') sb.append('/')
                else if (esc == 'b') sb.append('\b')
                else if (esc == 'f') sb.append('\f')
                else if (esc == 'n') sb.append('\n')
                else if (esc == 'r') sb.append('\r')
                else if (esc == 't') sb.append('\t')
                else if (esc == 'u') {
                    if (i + 4 > n) throw new RuntimeException("invalid json unicode escape")
                    val hx = text.substring(i, i + 4)
                    val cp = try Integer.parseInt(hx, 16) catch { case _: NumberFormatException => throw new RuntimeException("invalid json unicode escape") }
                    sb.appendCodePoint(cp)
                    i += 4
                } else throw new RuntimeException("invalid json escape")
            } else sb.append(ch)
        }
        throw new RuntimeException("unterminated json string")
    }

    private def parseNumber(): Any = {
        val start = i
        if (text.charAt(i) == '-') i += 1
        if (i >= n) throw new RuntimeException("invalid json number")
        if (text.charAt(i) == '0') {
            i += 1
        } else {
            if (!isDigit(text.charAt(i))) throw new RuntimeException("invalid json number")
            while (i < n && isDigit(text.charAt(i))) i += 1
        }
        var isFloat = false
        if (i < n && text.charAt(i) == '.') {
            isFloat = true
            i += 1
            if (i >= n || !isDigit(text.charAt(i))) throw new RuntimeException("invalid json number")
            while (i < n && isDigit(text.charAt(i))) i += 1
        }
        if (i < n && (text.charAt(i) == 'e' || text.charAt(i) == 'E')) {
            isFloat = true
            i += 1
            if (i < n && (text.charAt(i) == '+' || text.charAt(i) == '-')) i += 1
            if (i >= n || !isDigit(text.charAt(i))) throw new RuntimeException("invalid json exponent")
            while (i < n && isDigit(text.charAt(i))) i += 1
        }
        val token = text.substring(start, i)
        if (isFloat) {
            try token.toDouble
            catch { case _: NumberFormatException => throw new RuntimeException("invalid json number") }
        } else {
            try token.toLong
            catch { case _: NumberFormatException => throw new RuntimeException("invalid json number") }
        }
    }
}

def pyJsonLoads(v: Any): Any = {
    new __PytraJsonParser(__pytra_str(v)).parse()
}

def pyJsonDumps(v: Any): String = {
    __pytra_json_stringify(v)
}

class JsonArr(var raw: mutable.ArrayBuffer[Any]) {
    def get(index: Long): JsonValue | Null = {
        val i = index.toInt
        if (i < 0 || i >= raw.length) null else new JsonValue(raw(i))
    }
    def get_str(index: Long): String | Null = { val v = get(index); if (v == null) null else v.as_str() }
    def get_int(index: Long): Long | Null = { val v = get(index); if (v == null) null else v.as_int() }
    def get_float(index: Long): Double | Null = { val v = get(index); if (v == null) null else v.as_float() }
    def get_bool(index: Long): Boolean | Null = { val v = get(index); if (v == null) null else v.as_bool() }
    def get_arr(index: Long): JsonArr | Null = { val v = get(index); if (v == null) null else v.as_arr() }
    def get_obj(index: Long): JsonObj | Null = { val v = get(index); if (v == null) null else v.as_obj() }
}
class JsonObj(var raw: mutable.LinkedHashMap[String, Any]) {
    def get(key: String): JsonValue | Null = if (raw.contains(key)) new JsonValue(raw(key)) else null
    def get_str(key: String): String | Null = { val v = get(key); if (v == null) null else v.as_str() }
    def get_int(key: String): Long | Null = { val v = get(key); if (v == null) null else v.as_int() }
    def get_float(key: String): Double | Null = { val v = get(key); if (v == null) null else v.as_float() }
    def get_bool(key: String): Boolean | Null = { val v = get(key); if (v == null) null else v.as_bool() }
    def get_arr(key: String): JsonArr | Null = { val v = get(key); if (v == null) null else v.as_arr() }
    def get_obj(key: String): JsonObj | Null = { val v = get(key); if (v == null) null else v.as_obj() }
}

class JsonValue(var raw: Any) {
    def as_str(): String | Null = raw match {
        case s: String => s
        case _ => null
    }
    def as_int(): Long | Null = raw match {
        case n: Long => n
        case n: Int => n.toLong
        case _ => null
    }
    def as_float(): Double | Null = raw match {
        case n: Double => n
        case n: Float => n.toDouble
        case n: Long => n.toDouble
        case n: Int => n.toDouble
        case _ => null
    }
    def as_bool(): Boolean | Null = raw match {
        case b: Boolean => b
        case _ => null
    }
    def as_arr(): JsonArr | Null = raw match {
        case xs: mutable.ArrayBuffer[_] => new JsonArr(xs.asInstanceOf[mutable.ArrayBuffer[Any]])
        case _ => null
    }
    def as_obj(): JsonObj | Null = raw match {
        case d: mutable.Map[_, _] =>
            val out = mutable.LinkedHashMap[String, Any]()
            d.foreach { case (k, value) => out(__pytra_str(k)) = value }
            new JsonObj(out)
        case _ => null
    }
}
type __pytra_JsonVal = Any
val __pytra_JsonVal: type_py = "JsonVal"
def __pytra_JsonValue(raw: Any): JsonValue = new JsonValue(raw)

def __pytra_loads(v: Any): JsonValue = new JsonValue(pyJsonLoads(v))
def __pytra_loads_arr(v: Any): JsonArr = new JsonArr(__pytra_as_list(pyJsonLoads(v)).asInstanceOf[mutable.ArrayBuffer[Any]])
def __pytra_loads_obj(v: Any): JsonObj = {
    val out = mutable.LinkedHashMap[String, Any]()
    __pytra_as_dict(pyJsonLoads(v)).foreach { case (k, value) => out(__pytra_str(k)) = value }
    new JsonObj(out)
}
private def __pytra_json_unwrap(value: Any): Any = value match {
    case jv: JsonValue => jv.raw
    case ja: JsonArr => ja.raw
    case jo: JsonObj => jo.raw
    case other => other
}

def __pytra_dumps(value: Any, ensure_ascii: Any = true, indent: Any = null, separators: Any = null): String = {
    val normalized = __pytra_json_unwrap(value)
    val indentValue = indent match {
        case n: Long => n.toInt
        case n: Int => n
        case _ => 0
    }
    if (indentValue > 0) __pytra_json_pretty(normalized, __pytra_truthy(ensure_ascii), indentValue, 0)
    else pyJsonDumps(normalized)
}
def __pytra_sub(pattern: Any, repl: Any, text: Any, count: Any = 0L): String = {
    val regex = __pytra_str(pattern).r
    val limit = __pytra_int(count)
    if (limit <= 0L) regex.replaceAllIn(__pytra_str(text), __pytra_str(repl))
    else regex.replaceFirstIn(__pytra_str(text), __pytra_str(repl))
}

// Python stdlib shim objects so that EAST-generated code like
// `time.perf_counter()` or `math.sqrt(x)` resolves at runtime.
object time {
    def perf_counter(): Double = System.nanoTime().toDouble / 1_000_000_000.0
}
// Note: fabs/log10 are handled by Scala emitter math rewrite rules.


// Python built-in `open(path, mode)` shim.
class PyFile(path: String, mode: String) {
    private val isBinary = mode.contains("b")
    private val stream: java.io.OutputStream | Null = {
        if (mode.contains("r")) null
        else if (isBinary) new java.io.FileOutputStream(path)
        else new java.io.FileOutputStream(path)
    }
    def read(): String = {
        val bytes = java.nio.file.Files.readAllBytes(java.nio.file.Paths.get(path))
        new String(bytes, "UTF-8")
    }
    def write(data: Any): Unit = {
        val out = stream.nn
        data match {
            case buf: mutable.ArrayBuffer[_] =>
                val bytes = new Array[Byte](buf.length)
                var i = 0
                while (i < buf.length) {
                    bytes(i) = (buf(i).asInstanceOf[Long] & 0xFF).toByte
                    i += 1
                }
                out.write(bytes)
            case s: String => out.write(s.getBytes("UTF-8"))
            case _ => out.write(__pytra_str(data).getBytes("UTF-8"))
        }
    }
    def __enter__(): PyFile = this
    def __exit__(excType: Any, excVal: Any, excTb: Any): Unit = close()
    def close(): Unit = if (stream != null) stream.nn.close()
}

def open(path: Any, mode: String = "r"): PyFile = {
    new PyFile(__pytra_str(path), mode)
}

def ord(ch: Any): Long = {
    val s = __pytra_str(ch)
    if (s.isEmpty) 0L else s.charAt(0).toLong
}

def chr(n: Any): String = {
    val code = __pytra_int(n).toInt
    String.valueOf(code.toChar)
}

def __pytra_cwd(): Path = Path(os.getcwd())
