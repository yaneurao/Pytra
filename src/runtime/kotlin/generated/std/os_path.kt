// AUTO-GENERATED FILE. DO NOT EDIT.
// source: src/pytra/std/os_path.py
// generated-by: tools/gen_runtime_from_manifest.py



fun join(a: String, b: String): String {
    return __pytra_str(__path.join(a, b))
}

fun dirname(p: String): String {
    return __pytra_str(__path.dirname(p))
}

fun basename(p: String): String {
    return __pytra_str(__path.basename(p))
}

fun splitext(p: String): MutableList<Any?> {
    return __pytra_as_list(__path.splitext(p))
}

fun abspath(p: String): String {
    return __pytra_str(__path.abspath(p))
}

fun exists(p: String): Boolean {
    return __pytra_truthy(__path.exists(p))
}
