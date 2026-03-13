// AUTO-GENERATED FILE. DO NOT EDIT.
// source: src/pytra/std/os.py
// generated-by: tools/gen_runtime_from_manifest.py



fun getcwd(): String {
    return __pytra_str(__os.getcwd())
}

fun mkdir(p: String) {
    __os.mkdir(p)
}

fun makedirs(p: String, exist_ok: Boolean) {
    __os.makedirs(p, exist_ok)
}
