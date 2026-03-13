// AUTO-GENERATED FILE. DO NOT EDIT.
// source: src/pytra/std/time.py
// generated-by: tools/gen_runtime_from_manifest.py

import * as time_native from "../../native/std/time_native";

export function perf_counter(): number {
    return time_native.perf_counter();
}

export const perfCounter = perf_counter;
