// AUTO-GENERATED FILE. DO NOT EDIT.
// source: src/pytra/std/argparse.py
// generated-by: tools/gen_runtime_from_manifest.py

import scala.collection.mutable
import scala.util.boundary, boundary.break
import java.nio.file.{Files, Paths}


def __pytra_is_Namespace(v: Any): Boolean = {
    v.isInstanceOf[Namespace]
}

def __pytra_as_Namespace(v: Any): Namespace = {
    v match {
        case obj: Namespace => obj
        case _ => new Namespace()
    }
}

def __pytra_is__ArgSpec(v: Any): Boolean = {
    v.isInstanceOf[_ArgSpec]
}

def __pytra_as__ArgSpec(v: Any): _ArgSpec = {
    v match {
        case obj: _ArgSpec => obj
        case _ => new _ArgSpec()
    }
}

def __pytra_is_ArgumentParser(v: Any): Boolean = {
    v.isInstanceOf[ArgumentParser]
}

def __pytra_as_ArgumentParser(v: Any): ArgumentParser = {
    v match {
        case obj: ArgumentParser => obj
        case _ => new ArgumentParser()
    }
}

class Namespace() {
    var values: mutable.LinkedHashMap[Any, Any] = mutable.LinkedHashMap[Any, Any]()

    def this(values: Any) = {
        this()
        if (__pytra_float(values) == __pytra_float(__pytra_any_default())) {
            this.values = mutable.LinkedHashMap[Any, Any]()
            return
        }
        this.values = values
    }
}

class _ArgSpec() {
    var names: mutable.ArrayBuffer[String] = mutable.ArrayBuffer[String]()
    var action: String = ""
    var choices: mutable.ArrayBuffer[String] = mutable.ArrayBuffer[String]()
    var default: Any = null
    var help_text: String = ""
    var is_optional: Boolean = false
    var dest: String = ""

    def this(names: mutable.ArrayBuffer[String], action: String, choices: mutable.ArrayBuffer[String], default: Any, help_text: String) = {
        this()
        this.names = names
        this.action = action
        this.choices = choices
        this.default = default
        this.help_text = help_text
        this.is_optional = ((__pytra_len(names) > 0L) && __pytra_truthy(__pytra_startswith(__pytra_str(__pytra_get_index(names, 0L)), "-")))
        if (this.is_optional) {
            var base: Any = __pytra_replace(__pytra_lstrip(__pytra_str(__pytra_get_index(names, (-1L))), "-"), "-", "_")
            this.dest = base
        } else {
            this.dest = __pytra_str(__pytra_get_index(names, 0L))
        }
    }
}

class ArgumentParser() {
    var description: String = ""
    var _specs: mutable.ArrayBuffer[Any] = mutable.ArrayBuffer[Any]()

    def this(description: String) = {
        this()
        this.description = description
        this._specs = mutable.ArrayBuffer[Any]()
    }

    def add_argument(name0: String, name1: String, name2: String, name3: String, help: String, action: String, choices: mutable.ArrayBuffer[String], default: Any): Unit = {
        var names: mutable.ArrayBuffer[String] = __pytra_as_list(mutable.ArrayBuffer[Any]()).asInstanceOf[mutable.ArrayBuffer[String]]
        if (__pytra_str(name0) != __pytra_str("")) {
            names.append(name0)
        }
        if (__pytra_str(name1) != __pytra_str("")) {
            names.append(name1)
        }
        if (__pytra_str(name2) != __pytra_str("")) {
            names.append(name2)
        }
        if (__pytra_str(name3) != __pytra_str("")) {
            names.append(name3)
        }
        if (__pytra_len(names) == 0L) {
            throw new RuntimeException(__pytra_str("add_argument requires at least one name"))
        }
        var spec: _ArgSpec = new _ArgSpec(names, action, choices, default, help)
        this._specs = __pytra_as_list(this._specs); this._specs.append(spec)
    }

    def _fail(msg: String): Unit = {
        if (__pytra_str(msg) != __pytra_str("")) {
            sys.write_stderr(__pytra_any_default())
        }
        throw new RuntimeException(__pytra_str(SystemExit(2L)))
    }

    def parse_args(argv: Any): mutable.LinkedHashMap[Any, Any] = {
        var args: mutable.ArrayBuffer[String] = mutable.ArrayBuffer[String]()
        if (__pytra_float(argv) == __pytra_float(__pytra_any_default())) {
            args = __pytra_as_list(__pytra_slice(sys.argv, 1L, __pytra_len(sys.argv))).asInstanceOf[mutable.ArrayBuffer[String]]
        } else {
            args = __pytra_as_list(list(argv)).asInstanceOf[mutable.ArrayBuffer[String]]
        }
        var specs_pos: mutable.ArrayBuffer[Any] = __pytra_as_list(mutable.ArrayBuffer[Any]())
        var specs_opt: mutable.ArrayBuffer[Any] = __pytra_as_list(mutable.ArrayBuffer[Any]())
        val __iter_0 = __pytra_as_list(this._specs)
        var __i_1: Long = 0L
        while (__i_1 < __iter_0.size.toLong) {
            val s: _ArgSpec = __pytra_as__ArgSpec(__iter_0(__i_1.toInt))
            if (__pytra_truthy(s.is_optional)) {
                specs_opt.append(s)
            } else {
                specs_pos.append(s)
            }
            __i_1 += 1L
        }
        var by_name: mutable.LinkedHashMap[Any, Any] = __pytra_as_dict(mutable.LinkedHashMap[Any, Any]())
        var spec_i: Long = 0L
        val __iter_2 = __pytra_as_list(specs_opt)
        var __i_3: Long = 0L
        while (__i_3 < __iter_2.size.toLong) {
            val s: _ArgSpec = __pytra_as__ArgSpec(__iter_2(__i_3.toInt))
            val __iter_4 = __pytra_as_list(s.names)
            var __i_5: Long = 0L
            while (__i_5 < __iter_4.size.toLong) {
                val n = __iter_4(__i_5.toInt)
                __pytra_set_index(by_name, n, spec_i)
                __i_5 += 1L
            }
            spec_i += 1L
            __i_3 += 1L
        }
        var values: mutable.LinkedHashMap[Any, Any] = __pytra_as_dict(mutable.LinkedHashMap[Any, Any]())
        val __iter_6 = __pytra_as_list(this._specs)
        var __i_7: Long = 0L
        while (__i_7 < __iter_6.size.toLong) {
            val s: _ArgSpec = __pytra_as__ArgSpec(__iter_6(__i_7.toInt))
            if (__pytra_str(s.action) == __pytra_str("store_true")) {
                __pytra_set_index(values, s.dest, __pytra_ifexp((__pytra_float(s.default) == __pytra_float(__pytra_any_default())), __pytra_truthy(s.default), false))
            } else {
                if (__pytra_float(s.default) == __pytra_float(__pytra_any_default())) {
                    __pytra_set_index(values, s.dest, s.default)
                } else {
                    __pytra_set_index(values, s.dest, __pytra_any_default())
                }
            }
            __i_7 += 1L
        }
        var pos_i: Long = 0L
        var i: Long = 0L
        boundary:
            given __breakLabel_8: boundary.Label[Unit] = summon[boundary.Label[Unit]]
            while (i < __pytra_len(args)) {
                boundary:
                    given __continueLabel_9: boundary.Label[Unit] = summon[boundary.Label[Unit]]
                    var tok: String = __pytra_str(__pytra_get_index(args, i))
                    if (__pytra_truthy(__pytra_startswith(tok, "-"))) {
                        if (!__pytra_contains(by_name, tok)) {
                            this._fail(__pytra_any_default())
                        }
                        var spec: _ArgSpec = __pytra_as__ArgSpec(__pytra_as__ArgSpec(__pytra_get_index(specs_opt, __pytra_int(__pytra_get_index(by_name, tok)))))
                        if (__pytra_str(spec.action) == __pytra_str("store_true")) {
                            __pytra_set_index(values, spec.dest, true)
                            i += 1L
                            break(())(using __continueLabel_9)
                        }
                        if (i + 1L >= __pytra_len(args)) {
                            this._fail(__pytra_any_default())
                        }
                        var py_val: String = __pytra_str(__pytra_get_index(args, i + 1L))
                        if ((__pytra_len(spec.choices) > 0L) && ((!__pytra_contains(spec.choices, py_val)))) {
                            this._fail(__pytra_any_default())
                        }
                        __pytra_set_index(values, spec.dest, py_val)
                        i += 2L
                        break(())(using __continueLabel_9)
                    }
                    if (pos_i >= __pytra_len(specs_pos)) {
                        this._fail(__pytra_any_default())
                    }
                    var spec: _ArgSpec = __pytra_as__ArgSpec(__pytra_as__ArgSpec(__pytra_get_index(specs_pos, pos_i)))
                    __pytra_set_index(values, spec.dest, tok)
                    pos_i += 1L
                    i += 1L
            }
        if (pos_i < __pytra_len(specs_pos)) {
            this._fail(__pytra_any_default())
        }
        return values
    }
}
