// AUTO-GENERATED FILE. DO NOT EDIT.
// source: src/pytra/std/argparse.py
// generated-by: tools/gen_runtime_from_manifest.py



fun __pytra_is_Namespace(v: Any?): Boolean {
    return v is Namespace
}

fun __pytra_as_Namespace(v: Any?): Namespace {
    return if (v is Namespace) v else Namespace()
}

fun __pytra_is__ArgSpec(v: Any?): Boolean {
    return v is _ArgSpec
}

fun __pytra_as__ArgSpec(v: Any?): _ArgSpec {
    return if (v is _ArgSpec) v else _ArgSpec()
}

fun __pytra_is_ArgumentParser(v: Any?): Boolean {
    return v is ArgumentParser
}

fun __pytra_as_ArgumentParser(v: Any?): ArgumentParser {
    return if (v is ArgumentParser) v else ArgumentParser()
}

open class Namespace() {
    var values: MutableMap<Any, Any?> = mutableMapOf()

    constructor(values: Any) : this() {
        if ((__pytra_float(values) == __pytra_float(__pytra_any_default()))) {
            this.values = mutableMapOf<Any, Any?>()
            return
        }
        this.values = values
    }
}

open class _ArgSpec() {
    var names: MutableList<Any?> = mutableListOf()
    var action: String = ""
    var choices: MutableList<Any?> = mutableListOf()
    var default: Any = Any()
    var help_text: String = ""
    var is_optional: Boolean = false
    var dest: String = ""

    constructor(names: MutableList<Any?>, action: String, choices: MutableList<Any?>, default: Any, help_text: String) : this() {
        this.names = names
        this.action = action
        this.choices = choices
        this.default = default
        this.help_text = help_text
        this.is_optional = ((__pytra_int(__pytra_len(names)) > __pytra_int(0L)) && __pytra_truthy(__pytra_str(__pytra_get_index(names, 0L)).startswith("-")))
        if (this.is_optional) {
            var base: Any? = __pytra_str(__pytra_get_index(names, (-1L))).lstrip("-").replace("-", "_")
            this.dest = base
        } else {
            this.dest = __pytra_str(__pytra_get_index(names, 0L))
        }
    }
}

open class ArgumentParser() {
    var description: String = ""
    var _specs: MutableList<Any?> = mutableListOf()

    constructor(description: String) : this() {
        this.description = description
        this._specs = mutableListOf<Any?>()
    }

    open fun add_argument(name0: String, name1: String, name2: String, name3: String, help: String, action: String, choices: MutableList<Any?>, default: Any) {
        var names: MutableList<Any?> = __pytra_as_list(mutableListOf<Any?>())
        if ((__pytra_str(name0) != __pytra_str(""))) {
            names.add(name0)
        }
        if ((__pytra_str(name1) != __pytra_str(""))) {
            names.add(name1)
        }
        if ((__pytra_str(name2) != __pytra_str(""))) {
            names.add(name2)
        }
        if ((__pytra_str(name3) != __pytra_str(""))) {
            names.add(name3)
        }
        if ((__pytra_int(__pytra_len(names)) == __pytra_int(0L))) {
            throw RuntimeException(__pytra_str("add_argument requires at least one name"))
        }
        var spec: _ArgSpec = _ArgSpec(names, action, choices, default, help)
        this._specs = __pytra_as_list(this._specs); this._specs.add(spec)
    }

    open fun _fail(msg: String) {
        if ((__pytra_str(msg) != __pytra_str(""))) {
            sys.write_stderr(__pytra_any_default())
        }
        throw RuntimeException(__pytra_str(SystemExit(2L)))
    }

    open fun parse_args(argv: Any): MutableMap<Any, Any?> {
        var args: MutableList<Any?> = mutableListOf()
        if ((__pytra_float(argv) == __pytra_float(__pytra_any_default()))) {
            args = __pytra_as_list(__pytra_slice(sys.argv, 1L, __pytra_len(sys.argv)))
        } else {
            args = list(argv)
        }
        var specs_pos: MutableList<Any?> = __pytra_as_list(mutableListOf<Any?>())
        var specs_opt: MutableList<Any?> = __pytra_as_list(mutableListOf<Any?>())
        val __iter_0 = __pytra_as_list(this._specs)
        var __i_1: Long = 0L
        while (__i_1 < __iter_0.size.toLong()) {
            val s: _ArgSpec = __pytra_as__ArgSpec(__iter_0[__i_1.toInt()])
            if (__pytra_truthy(s.is_optional)) {
                specs_opt.add(s)
            } else {
                specs_pos.add(s)
            }
            __i_1 += 1L
        }
        var by_name: MutableMap<Any, Any?> = __pytra_as_dict(mutableMapOf<Any, Any?>())
        var spec_i: Long = 0L
        val __iter_2 = __pytra_as_list(specs_opt)
        var __i_3: Long = 0L
        while (__i_3 < __iter_2.size.toLong()) {
            val s: _ArgSpec = __pytra_as__ArgSpec(__iter_2[__i_3.toInt()])
            val __iter_4 = __pytra_as_list(s.names)
            var __i_5: Long = 0L
            while (__i_5 < __iter_4.size.toLong()) {
                val n = __iter_4[__i_5.toInt()]
                __pytra_set_index(by_name, n, spec_i)
                __i_5 += 1L
            }
            spec_i += 1L
            __i_3 += 1L
        }
        var values: MutableMap<Any, Any?> = __pytra_as_dict(mutableMapOf<Any, Any?>())
        val __iter_6 = __pytra_as_list(this._specs)
        var __i_7: Long = 0L
        while (__i_7 < __iter_6.size.toLong()) {
            val s: _ArgSpec = __pytra_as__ArgSpec(__iter_6[__i_7.toInt()])
            if ((__pytra_str(s.action) == __pytra_str("store_true"))) {
                __pytra_set_index(values, s.dest, __pytra_ifexp((__pytra_float(s.default) == __pytra_float(__pytra_any_default())), __pytra_truthy(s.default), false))
            } else {
                if ((__pytra_float(s.default) == __pytra_float(__pytra_any_default()))) {
                    __pytra_set_index(values, s.dest, s.default)
                } else {
                    __pytra_set_index(values, s.dest, __pytra_any_default())
                }
            }
            __i_7 += 1L
        }
        var pos_i: Long = 0L
        var i: Long = 0L
        while ((__pytra_int(i) < __pytra_int(__pytra_len(args)))) {
            var tok: String = __pytra_str(__pytra_get_index(args, i))
            if (__pytra_truthy(tok.startswith("-"))) {
                if (((!__pytra_contains(by_name, tok)))) {
                    this._fail(__pytra_any_default())
                }
                var spec: _ArgSpec = __pytra_as__ArgSpec(__pytra_as__ArgSpec(__pytra_get_index(specs_opt, __pytra_int(__pytra_get_index(by_name, tok)))))
                if ((__pytra_str(spec.action) == __pytra_str("store_true"))) {
                    __pytra_set_index(values, spec.dest, true)
                    i += 1L
                    continue
                }
                if ((__pytra_int(i + 1L) >= __pytra_int(__pytra_len(args)))) {
                    this._fail(__pytra_any_default())
                }
                var val_: String = __pytra_str(__pytra_get_index(args, (i + 1L)))
                if (((__pytra_int(__pytra_len(spec.choices)) > __pytra_int(0L)) && ((!__pytra_contains(spec.choices, val_))))) {
                    this._fail(__pytra_any_default())
                }
                __pytra_set_index(values, spec.dest, val_)
                i += 2L
                continue
            }
            if ((__pytra_int(pos_i) >= __pytra_int(__pytra_len(specs_pos)))) {
                this._fail(__pytra_any_default())
            }
            var spec: _ArgSpec = __pytra_as__ArgSpec(__pytra_as__ArgSpec(__pytra_get_index(specs_pos, pos_i)))
            __pytra_set_index(values, spec.dest, tok)
            pos_i += 1L
            i += 1L
        }
        if ((__pytra_int(pos_i) < __pytra_int(__pytra_len(specs_pos)))) {
            this._fail(__pytra_any_default())
        }
        return values
    }
}
