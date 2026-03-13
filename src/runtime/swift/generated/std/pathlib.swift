// AUTO-GENERATED FILE. DO NOT EDIT.
// source: src/pytra/std/pathlib.py
// generated-by: tools/gen_runtime_from_manifest.py

import Foundation


func __pytra_is_Path(_ v: Any?) -> Bool {
    return v is Path
}

class Path {
    var _value: String = ""

    init(_ value: String) {
        self._value = value
    }

    func __str__() -> String {
        return __pytra_str(self._value)
    }

    func __repr__() -> String {
        return (__pytra_str((__pytra_str("Path(") + __pytra_str(self._value))) + __pytra_str(")"))
    }

    func __fspath__() -> String {
        return __pytra_str(self._value)
    }

    func __truediv__(_ rhs: String) -> Path {
        return Path(path.join(self._value, rhs))
    }

    func parent() -> Path {
        var parent_txt: Any = path.dirname(self._value)
        if (__pytra_str(parent_txt) == __pytra_str("")) {
            parent_txt = "."
        }
        return Path(parent_txt)
    }

    func parents() -> [Any] {
        var out: [Any] = __pytra_as_list([])
        var current: String = __pytra_str(path.dirname(self._value))
        while true {
            if (__pytra_str(current) == __pytra_str("")) {
                current = "."
            }
            out.append(Path(current))
            var next_current: String = __pytra_str(path.dirname(current))
            if (__pytra_str(next_current) == __pytra_str("")) {
                next_current = "."
            }
            if (__pytra_str(next_current) == __pytra_str(current)) {
                break
            }
            current = next_current
        }
        return out
    }

    func name() -> String {
        return __pytra_str(path.basename(self._value))
    }

    func suffix() -> String {
        let __tuple_0 = __pytra_as_list(path.splitext(path.basename(self._value)))
        var _: Any = __tuple_0[0]
        var ext: Any = __tuple_0[1]
        return __pytra_str(ext)
    }

    func stem() -> String {
        let __tuple_0 = __pytra_as_list(path.splitext(path.basename(self._value)))
        var root: Any = __tuple_0[0]
        var _: Any = __tuple_0[1]
        return __pytra_str(root)
    }

    func resolve() -> Path {
        return Path(path.abspath(self._value))
    }

    func exists() -> Bool {
        return __pytra_truthy(path.exists(self._value))
    }

    func mkdir(_ parents: Bool, _ exist_ok: Bool) {
        if parents {
            os.makedirs(self._value, exist_ok)
            return
        }
        if (exist_ok && __pytra_truthy(path.exists(self._value))) {
            return
        }
        os.mkdir(self._value)
    }

    func read_text(_ encoding: String) -> String {
        var f: PyFile = open(self._value, "r", encoding)
        return __pytra_str(f.read())
        f.close()
        return ""
    }

    func write_text(_ text: String, _ encoding: String) -> Int64 {
        var f: PyFile = open(self._value, "w", encoding)
        return __pytra_int(f.write(text))
        f.close()
        return 0
    }

    func glob(_ pattern: String) -> [Any] {
        var paths: [Any] = __pytra_as_list(py_glob.glob(path.join(self._value, pattern)))
        var out: [Any] = __pytra_as_list([])
        do {
            let __iter_0 = __pytra_as_list(paths)
            var __i_1: Int64 = 0
            while __i_1 < Int64(__iter_0.count) {
                let p: String = __pytra_str(__iter_0[Int(__i_1)])
                out.append(Path(p))
                __i_1 += 1
            }
        }
        return out
    }

    func cwd() -> Path {
        return Path(os.getcwd())
    }
}
