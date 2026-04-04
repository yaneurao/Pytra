// Scala runtime core for Pytra native backend.
// Source of truth: src/runtime/scala/native/built_in/py_runtime.scala

import scala.collection.mutable
import java.nio.file.{Files, Paths}

// Trait for Python enum-like classes so __pytra_int() can extract their integer value.
trait PytraEnumLike {
    def value: Long
}

class Exception extends RuntimeException {
    var __pytra_message: String = ""
    def __init__(msg: Any): Unit = {
        __pytra_message = __pytra_str(msg)
    }
    override def getMessage(): String = __pytra_message
    override def toString: String = __pytra_message
}

class ValueError extends Exception
class TypeError extends Exception

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
def __pytra_repr(v: Any): String = {
    if (v == null) return "None"
    v match {
        case b: Boolean => if (b) "True" else "False"
        case s: String => "'" + s.replace("\\", "\\\\").replace("'", "\\'") + "'"
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
        case xs: mutable.ArrayBuffer[?] =>
            "[" + xs.map(x => __pytra_repr(x.asInstanceOf[Any])).mkString(", ") + "]"
        case m: mutable.LinkedHashMap[?, ?] =>
            val entries = m.asInstanceOf[mutable.LinkedHashMap[Any, Any]]
            "{" + entries.map(e => __pytra_repr(e._1) + ": " + __pytra_repr(e._2)).mkString(", ") + "}"
        case _ => v.toString
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
            if (i < 0L || i >= s.length.toLong) throw new RuntimeException("string index out of range")
            s.charAt(i.toInt).toString
        case m: mutable.LinkedHashMap[?, ?] =>
            m.asInstanceOf[mutable.LinkedHashMap[Any, Any]].getOrElse(index, __pytra_any_default())
        case m: scala.collection.Map[?, ?] =>
            m.asInstanceOf[scala.collection.Map[Any, Any]].getOrElse(index, __pytra_any_default())
        case _ =>
            val list = __pytra_as_list(container)
            val i = __pytra_index(__pytra_int(index), list.size.toLong)
            if (i >= 0L && i < list.size.toLong) return list(i.toInt)
            throw new RuntimeException("list index out of range")
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
    m.foreach { case (k, v) => out.append(mutable.ArrayBuffer[Any](k, v)) }
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
        out.append(mutable.ArrayBuffer[Any](la(i), lb(i)))
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
        case "list" | "tuple" | "bytes" | "bytearray" => v.isInstanceOf[scala.collection.Seq[?]]
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

class Path(v: Any) {
    private val _value: String = __pytra_str(v)

    def /(rhs: Any): Path = Path(__pytra_path_join(_value, __pytra_str(rhs)))
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

private def __pytra_json_escape_string(s: String): String = {
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
        else if (ch < 0x20) {
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

// Python stdlib shim objects so that EAST-generated code like
// `time.perf_counter()` or `math.sqrt(x)` resolves at runtime.
object time {
    def perf_counter(): Double = System.nanoTime().toDouble / 1_000_000_000.0
}
// Note: fabs/log10 are handled by Scala emitter math rewrite rules.


// Python built-in `open(path, mode)` shim.
class PyFile(path: String, mode: String) {
    private val stream: java.io.OutputStream = {
        if (mode.contains("b")) new java.io.FileOutputStream(path)
        else new java.io.FileOutputStream(path)
    }
    def write(data: Any): Unit = {
        data match {
            case buf: mutable.ArrayBuffer[_] =>
                val bytes = new Array[Byte](buf.length)
                var i = 0
                while (i < buf.length) {
                    bytes(i) = (buf(i).asInstanceOf[Long] & 0xFF).toByte
                    i += 1
                }
                stream.write(bytes)
            case s: String => stream.write(s.getBytes("UTF-8"))
            case _ => stream.write(__pytra_str(data).getBytes("UTF-8"))
        }
    }
    def close(): Unit = stream.close()
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
