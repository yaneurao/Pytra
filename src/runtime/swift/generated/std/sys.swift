// AUTO-GENERATED FILE. DO NOT EDIT.
// source: src/pytra/std/sys.py
// generated-by: tools/gen_runtime_from_manifest.py

import Foundation


func exit(_ code: Int64) {
    __s.exit(code)
}

func set_argv(_ values: [Any]) {
    argv.clear()
    do {
        let __iter_0 = __pytra_as_list(values)
        var __i_1: Int64 = 0
        while __i_1 < Int64(__iter_0.count) {
            let v: String = __pytra_str(__iter_0[Int(__i_1)])
            argv = __pytra_as_list(argv); argv.append(v)
            __i_1 += 1
        }
    }
}

func set_path(_ values: [Any]) {
    path.clear()
    do {
        let __iter_0 = __pytra_as_list(values)
        var __i_1: Int64 = 0
        while __i_1 < Int64(__iter_0.count) {
            let v: String = __pytra_str(__iter_0[Int(__i_1)])
            path = __pytra_as_list(path); path.append(v)
            __i_1 += 1
        }
    }
}

func write_stderr(_ text: String) {
    __s.stderr.write(text)
}

func write_stdout(_ text: String) {
    __s.stdout.write(text)
}
