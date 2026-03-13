// AUTO-GENERATED FILE. DO NOT EDIT.
// source: src/pytra/std/sys.py
// generated-by: tools/gen_runtime_from_manifest.py



fun exit(code: Long) {
    __s.exit(code)
}

fun set_argv(values: MutableList<Any?>) {
    argv.clear()
    val __iter_0 = __pytra_as_list(values)
    var __i_1: Long = 0L
    while (__i_1 < __iter_0.size.toLong()) {
        val v: String = __pytra_str(__iter_0[__i_1.toInt()])
        argv = __pytra_as_list(argv); argv.add(v)
        __i_1 += 1L
    }
}

fun set_path(values: MutableList<Any?>) {
    path.clear()
    val __iter_0 = __pytra_as_list(values)
    var __i_1: Long = 0L
    while (__i_1 < __iter_0.size.toLong()) {
        val v: String = __pytra_str(__iter_0[__i_1.toInt()])
        path = __pytra_as_list(path); path.add(v)
        __i_1 += 1L
    }
}

fun write_stderr(text: String) {
    __s.stderr.write(text)
}

fun write_stdout(text: String) {
    __s.stdout.write(text)
}
