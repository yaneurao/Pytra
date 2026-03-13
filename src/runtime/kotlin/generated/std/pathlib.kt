// AUTO-GENERATED FILE. DO NOT EDIT.
// source: src/pytra/std/pathlib.py
// generated-by: tools/gen_runtime_from_manifest.py



fun __pytra_is_Path(v: Any?): Boolean {
    return v is Path
}

fun __pytra_as_Path(v: Any?): Path {
    return if (v is Path) v else Path()
}

open class Path() {
    var _value: String = ""

    constructor(value: String) : this() {
        this._value = value
    }

    open fun __str__(): String {
        return __pytra_str(this._value)
    }

    open fun __repr__(): String {
        return (__pytra_str((__pytra_str("Path(") + __pytra_str(this._value))) + __pytra_str(")"))
    }

    open fun __fspath__(): String {
        return __pytra_str(this._value)
    }

    open fun __truediv__(rhs: String): Path {
        return Path(path.join(this._value, rhs))
    }

    open fun parent(): Path {
        var parent_txt: Any? = path.dirname(this._value)
        if ((__pytra_str(parent_txt) == __pytra_str(""))) {
            parent_txt = "."
        }
        return Path(parent_txt)
    }

    open fun parents(): MutableList<Any?> {
        var out: MutableList<Any?> = __pytra_as_list(mutableListOf<Any?>())
        var current: String = __pytra_str(path.dirname(this._value))
        while (true) {
            if ((__pytra_str(current) == __pytra_str(""))) {
                current = "."
            }
            out.add(Path(current))
            var next_current: String = __pytra_str(path.dirname(current))
            if ((__pytra_str(next_current) == __pytra_str(""))) {
                next_current = "."
            }
            if ((__pytra_str(next_current) == __pytra_str(current))) {
                break
            }
            current = next_current
        }
        return out
    }

    open fun name(): String {
        return __pytra_str(path.basename(this._value))
    }

    open fun suffix(): String {
        val __tuple_0 = __pytra_as_list(path.splitext(path.basename(this._value)))
        var _: Any? = __tuple_0[0]
        var ext: Any? = __tuple_0[1]
        return __pytra_str(ext)
    }

    open fun stem(): String {
        val __tuple_0 = __pytra_as_list(path.splitext(path.basename(this._value)))
        var root: Any? = __tuple_0[0]
        var _: Any? = __tuple_0[1]
        return __pytra_str(root)
    }

    open fun resolve(): Path {
        return Path(path.abspath(this._value))
    }

    open fun exists(): Boolean {
        return __pytra_truthy(path.exists(this._value))
    }

    open fun mkdir(parents: Boolean, exist_ok: Boolean) {
        if (parents) {
            os.makedirs(this._value, exist_ok)
            return
        }
        if ((exist_ok && __pytra_truthy(path.exists(this._value)))) {
            return
        }
        os.mkdir(this._value)
    }

    open fun read_text(encoding: String): String {
        var f: PyFile = open(this._value, "r", encoding)
        return __pytra_str(f.read())
        f.close()
        return ""
    }

    open fun write_text(text: String, encoding: String): Long {
        var f: PyFile = open(this._value, "w", encoding)
        return __pytra_int(f.write(text))
        f.close()
        return 0L
    }

    open fun glob(pattern: String): MutableList<Any?> {
        var paths: MutableList<Any?> = __pytra_as_list(py_glob.glob(path.join(this._value, pattern)))
        var out: MutableList<Any?> = __pytra_as_list(mutableListOf<Any?>())
        val __iter_0 = __pytra_as_list(paths)
        var __i_1: Long = 0L
        while (__i_1 < __iter_0.size.toLong()) {
            val p: String = __pytra_str(__iter_0[__i_1.toInt()])
            out.add(Path(p))
            __i_1 += 1L
        }
        return out
    }

    open fun cwd(): Path {
        return Path(os.getcwd())
    }
}
