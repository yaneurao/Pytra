// AUTO-GENERATED FILE. DO NOT EDIT.
// source: src/pytra/std/sys.py
// generated-by: tools/gen_runtime_from_manifest.py

package main


func exit(code int64) {
    __s.exit(code)
}

func set_argv(values []any) {
    argv.clear()
    __iter_0 := __pytra_as_list(values)
    for __i_1 := int64(0); __i_1 < int64(len(__iter_0)); __i_1 += 1 {
        var v string = __pytra_str(__iter_0[__i_1])
        argv = append(__pytra_as_list(argv), v)
    }
}

func set_path(values []any) {
    path.clear()
    __iter_0 := __pytra_as_list(values)
    for __i_1 := int64(0); __i_1 < int64(len(__iter_0)); __i_1 += 1 {
        var v string = __pytra_str(__iter_0[__i_1])
        path = append(__pytra_as_list(path), v)
    }
}

func write_stderr(text string) {
    __s.stderr.write(text)
}

func write_stdout(text string) {
    __s.stdout.write(text)
}
