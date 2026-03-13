// AUTO-GENERATED FILE. DO NOT EDIT.
// source: src/pytra/std/glob.py
// generated-by: tools/gen_runtime_from_manifest.py



fun glob(pattern: String): MutableList<Any?> {
    return __pytra_as_list(__glob.glob(pattern))
}
