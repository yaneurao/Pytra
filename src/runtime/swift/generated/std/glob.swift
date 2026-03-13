// AUTO-GENERATED FILE. DO NOT EDIT.
// source: src/pytra/std/glob.py
// generated-by: tools/gen_runtime_from_manifest.py

import Foundation


func glob(_ pattern: String) -> [Any] {
    return __pytra_as_list(__glob.glob(pattern))
}
