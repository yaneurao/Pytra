// AUTO-GENERATED FILE. DO NOT EDIT.
// source: src/pytra/std/os_path.py
// generated-by: tools/gen_runtime_from_manifest.py

package main


func join(a string, b string) string {
    return __pytra_str(__path.join(a, b))
}

func dirname(p string) string {
    return __pytra_str(__path.dirname(p))
}

func basename(p string) string {
    return __pytra_str(__path.basename(p))
}

func splitext(p string) []any {
    return __pytra_as_list(__path.splitext(p))
}

func abspath(p string) string {
    return __pytra_str(__path.abspath(p))
}

func exists(p string) bool {
    return __pytra_truthy(__path.exists(p))
}
