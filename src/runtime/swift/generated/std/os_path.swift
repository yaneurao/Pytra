// AUTO-GENERATED FILE. DO NOT EDIT.
// source: src/pytra/std/os_path.py
// generated-by: tools/gen_runtime_from_manifest.py

import Foundation


func join(_ a: String, _ b: String) -> String {
    return __pytra_str(__path.join(a, b))
}

func dirname(_ p: String) -> String {
    return __pytra_str(__path.dirname(p))
}

func basename(_ p: String) -> String {
    return __pytra_str(__path.basename(p))
}

func splitext(_ p: String) -> [Any] {
    return __pytra_as_list(__path.splitext(p))
}

func abspath(_ p: String) -> String {
    return __pytra_str(__path.abspath(p))
}

func exists(_ p: String) -> Bool {
    return __pytra_truthy(__path.exists(p))
}
