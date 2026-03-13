// AUTO-GENERATED FILE. DO NOT EDIT.
// source: src/pytra/std/os.py
// generated-by: tools/gen_runtime_from_manifest.py

import Foundation


func getcwd() -> String {
    return __pytra_str(__os.getcwd())
}

func mkdir(_ p: String) {
    __os.mkdir(p)
}

func makedirs(_ p: String, _ exist_ok: Bool) {
    __os.makedirs(p, exist_ok)
}
