// AUTO-GENERATED FILE. DO NOT EDIT.
// source: src/pytra/std/os.py
// generated-by: tools/gen_runtime_from_manifest.py

package main


func getcwd() string {
    return __pytra_str(__os.getcwd())
}

func mkdir(p string) {
    __os.mkdir(p)
}

func makedirs(p string, exist_ok bool) {
    __os.makedirs(p, exist_ok)
}
