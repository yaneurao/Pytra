// AUTO-GENERATED FILE. DO NOT EDIT.
// source: src/pytra/std/pathlib.py
// generated-by: tools/gen_runtime_from_manifest.py

import scala.collection.mutable
import scala.util.boundary, boundary.break
import java.nio.file.{Files, Paths}


def __pytra_is_Path(v: Any): Boolean = {
    v.isInstanceOf[Path]
}

def __pytra_as_Path(v: Any): Path = {
    v match {
        case obj: Path => obj
        case _ => new Path()
    }
}

class Path() {
    var _value: String = ""

    def this(value: String) = {
        this()
        this._value = value
    }

    def __str__(): String = {
        return __pytra_str(this._value)
    }

    def __repr__(): String = {
        return (__pytra_str(__pytra_str("Path(") + __pytra_str(this._value)) + __pytra_str(")"))
    }

    def __fspath__(): String = {
        return __pytra_str(this._value)
    }

    def __truediv__(rhs: String): String = {
        return new Path(path.join(this._value, rhs))
    }

    def parent(): String = {
        var parent_txt: Any = path.dirname(this._value)
        if (__pytra_str(parent_txt) == __pytra_str("")) {
            parent_txt = "."
        }
        return new Path(parent_txt)
    }

    def parents(): mutable.ArrayBuffer[String] = {
        var out: mutable.ArrayBuffer[String] = __pytra_as_list(mutable.ArrayBuffer[Any]()).asInstanceOf[mutable.ArrayBuffer[String]]
        var current: String = __pytra_str(path.dirname(this._value))
        boundary:
            given __breakLabel_0: boundary.Label[Unit] = summon[boundary.Label[Unit]]
            while (true) {
                boundary:
                    given __continueLabel_1: boundary.Label[Unit] = summon[boundary.Label[Unit]]
                    if (__pytra_str(current) == __pytra_str("")) {
                        current = "."
                    }
                    out.append(new Path(current))
                    var next_current: String = __pytra_str(path.dirname(current))
                    if (__pytra_str(next_current) == __pytra_str("")) {
                        next_current = "."
                    }
                    if (__pytra_str(next_current) == __pytra_str(current)) {
                        break(())(using __breakLabel_0)
                    }
                    current = next_current
            }
        return out
    }

    def name(): String = {
        return __pytra_str(path.basename(this._value))
    }

    def suffix(): String = {
        val __tuple_0 = __pytra_as_list(path.splitext(path.basename(this._value)))
        var tmp_0: Any = __tuple_0(0)
        var ext: Any = __tuple_0(1)
        return __pytra_str(ext)
    }

    def stem(): String = {
        val __tuple_0 = __pytra_as_list(path.splitext(path.basename(this._value)))
        var root: Any = __tuple_0(0)
        var tmp_1: Any = __tuple_0(1)
        return __pytra_str(root)
    }

    def resolve(): String = {
        return new Path(path.abspath(this._value))
    }

    def exists(): Boolean = {
        return __pytra_truthy(path.exists(this._value))
    }

    def mkdir(parents: Boolean, exist_ok: Boolean): Unit = {
        if (parents) {
            os.makedirs(this._value, exist_ok)
            return
        }
        if (exist_ok && __pytra_truthy(path.exists(this._value))) {
            return
        }
        os.mkdir(this._value)
    }

    def read_text(encoding: String): String = {
        var f: PyFile = open(this._value, "r", encoding)
        try {
            return __pytra_str(f.read())
        } finally {
            f.close()
        }
        return ""
    }

    def write_text(text: String, encoding: String): Long = {
        var f: PyFile = open(this._value, "w", encoding)
        try {
            return __pytra_int(f.write(text))
        } finally {
            f.close()
        }
        return 0L
    }

    def glob(pattern: String): mutable.ArrayBuffer[String] = {
        var paths: mutable.ArrayBuffer[String] = __pytra_as_list(py_glob.glob(path.join(this._value, pattern))).asInstanceOf[mutable.ArrayBuffer[String]]
        var out: mutable.ArrayBuffer[String] = __pytra_as_list(mutable.ArrayBuffer[Any]()).asInstanceOf[mutable.ArrayBuffer[String]]
        val __iter_0 = __pytra_as_list(paths)
        var __i_1: Long = 0L
        while (__i_1 < __iter_0.size.toLong) {
            val p: String = __pytra_str(__iter_0(__i_1.toInt))
            out.append(new Path(p))
            __i_1 += 1L
        }
        return out
    }

    def cwd(): String = {
        return new Path(os.getcwd())
    }
}
