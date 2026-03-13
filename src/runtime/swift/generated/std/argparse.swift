// AUTO-GENERATED FILE. DO NOT EDIT.
// source: src/pytra/std/argparse.py
// generated-by: tools/gen_runtime_from_manifest.py

import Foundation


func __pytra_is_Namespace(_ v: Any?) -> Bool {
    return v is Namespace
}

func __pytra_is__ArgSpec(_ v: Any?) -> Bool {
    return v is _ArgSpec
}

func __pytra_is_ArgumentParser(_ v: Any?) -> Bool {
    return v is ArgumentParser
}

class Namespace {
    var values: [AnyHashable: Any] = [:]

    init(_ values: Any) {
        if (__pytra_float(values) == __pytra_float(__pytra_any_default())) {
            self.values = [:]
            return
        }
        self.values = values
    }
}

class _ArgSpec {
    var names: [Any] = []
    var action: String = ""
    var choices: [Any] = []
    var default_: Any = __pytra_any_default()
    var help_text: String = ""
    var is_optional: Bool = false
    var dest: String = ""

    init(_ names: [Any], _ action: String, _ choices: [Any], _ default_: Any, _ help_text: String) {
        self.names = names
        self.action = action
        self.choices = choices
        self.default_ = default_
        self.help_text = help_text
        self.is_optional = ((__pytra_int(__pytra_len(names)) > __pytra_int(Int64(0))) && __pytra_truthy(__pytra_str(__pytra_getIndex(names, Int64(0))).startswith("-")))
        if self.is_optional {
            var base: Any = __pytra_str(__pytra_getIndex(names, (-Int64(1)))).lstrip("-").replace("-", "_")
            self.dest = base
        } else {
            self.dest = __pytra_str(__pytra_getIndex(names, Int64(0)))
        }
    }
}

class ArgumentParser {
    var description: String = ""
    var _specs: [Any] = []

    init(_ description: String) {
        self.description = description
        self._specs = []
    }

    func add_argument(_ name0: String, _ name1: String, _ name2: String, _ name3: String, _ help: String, _ action: String, _ choices: [Any], _ default_: Any) {
        var names: [Any] = __pytra_as_list([])
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
        if (__pytra_int(__pytra_len(names)) == __pytra_int(Int64(0))) {
            fatalError("pytra raise")
        }
        var spec: _ArgSpec = _ArgSpec(names, action, choices, default_, help)
        self._specs = __pytra_as_list(self._specs); self._specs.append(spec)
    }

    func _fail(_ msg: String) {
        if (__pytra_str(msg) != __pytra_str("")) {
            sys.write_stderr(__pytra_any_default())
        }
        fatalError("pytra raise")
    }

    func parse_args(_ argv: Any) -> [AnyHashable: Any] {
        var args: [Any] = []
        if (__pytra_float(argv) == __pytra_float(__pytra_any_default())) {
            args = __pytra_as_list(__pytra_slice(sys.argv, Int64(1), __pytra_len(sys.argv)))
        } else {
            args = list(argv)
        }
        var specs_pos: [Any] = __pytra_as_list([])
        var specs_opt: [Any] = __pytra_as_list([])
        do {
            let __iter_0 = __pytra_as_list(self._specs)
            var __i_1: Int64 = 0
            while __i_1 < Int64(__iter_0.count) {
                let s: _ArgSpec = (__iter_0[Int(__i_1)] as? _ArgSpec) ?? _ArgSpec()
                if __pytra_truthy(s.is_optional) {
                    specs_opt.append(s)
                } else {
                    specs_pos.append(s)
                }
                __i_1 += 1
            }
        }
        var by_name: [AnyHashable: Any] = __pytra_as_dict([:])
        var spec_i: Int64 = Int64(0)
        do {
            let __iter_2 = __pytra_as_list(specs_opt)
            var __i_3: Int64 = 0
            while __i_3 < Int64(__iter_2.count) {
                let s: _ArgSpec = (__iter_2[Int(__i_3)] as? _ArgSpec) ?? _ArgSpec()
                do {
                    let __iter_4 = __pytra_as_list(s.names)
                    var __i_5: Int64 = 0
                    while __i_5 < Int64(__iter_4.count) {
                        let n = __iter_4[Int(__i_5)]
                        by_name[AnyHashable(__pytra_str(n))] = spec_i
                        __i_5 += 1
                    }
                }
                spec_i += Int64(1)
                __i_3 += 1
            }
        }
        var values: [AnyHashable: Any] = __pytra_as_dict([:])
        do {
            let __iter_6 = __pytra_as_list(self._specs)
            var __i_7: Int64 = 0
            while __i_7 < Int64(__iter_6.count) {
                let s: _ArgSpec = (__iter_6[Int(__i_7)] as? _ArgSpec) ?? _ArgSpec()
                if (__pytra_str(s.action) == __pytra_str("store_true")) {
                    values[AnyHashable(__pytra_str(s.dest))] = __pytra_ifexp((__pytra_float(s.default_) == __pytra_float(__pytra_any_default())), __pytra_truthy(s.default_), false)
                } else {
                    if (__pytra_float(s.default_) == __pytra_float(__pytra_any_default())) {
                        values[AnyHashable(__pytra_str(s.dest))] = s.default_
                    } else {
                        values[AnyHashable(__pytra_str(s.dest))] = __pytra_any_default()
                    }
                }
                __i_7 += 1
            }
        }
        var pos_i: Int64 = Int64(0)
        var i: Int64 = Int64(0)
        while (__pytra_int(i) < __pytra_int(__pytra_len(args))) {
            var tok: String = __pytra_str(__pytra_getIndex(args, i))
            if __pytra_truthy(tok.startswith("-")) {
                if ((!__pytra_contains(by_name, tok))) {
                    self._fail(__pytra_any_default())
                }
                var spec: _ArgSpec = ((__pytra_getIndex(specs_opt, __pytra_int(__pytra_getIndex(by_name, tok))) as? _ArgSpec) ?? _ArgSpec() as? _ArgSpec) ?? _ArgSpec()
                if (__pytra_str(spec.action) == __pytra_str("store_true")) {
                    values[AnyHashable(__pytra_str(spec.dest))] = true
                    i += Int64(1)
                    continue
                }
                if (__pytra_int(i + Int64(1)) >= __pytra_int(__pytra_len(args))) {
                    self._fail(__pytra_any_default())
                }
                var val: String = __pytra_str(__pytra_getIndex(args, (i + Int64(1))))
                if ((__pytra_int(__pytra_len(spec.choices)) > __pytra_int(Int64(0))) && ((!__pytra_contains(spec.choices, val)))) {
                    self._fail(__pytra_any_default())
                }
                values[AnyHashable(__pytra_str(spec.dest))] = val
                i += Int64(2)
                continue
            }
            if (__pytra_int(pos_i) >= __pytra_int(__pytra_len(specs_pos))) {
                self._fail(__pytra_any_default())
            }
            var spec: _ArgSpec = ((__pytra_getIndex(specs_pos, pos_i) as? _ArgSpec) ?? _ArgSpec() as? _ArgSpec) ?? _ArgSpec()
            values[AnyHashable(__pytra_str(spec.dest))] = tok
            pos_i += Int64(1)
            i += Int64(1)
        }
        if (__pytra_int(pos_i) < __pytra_int(__pytra_len(specs_pos))) {
            self._fail(__pytra_any_default())
        }
        return values
    }
}
