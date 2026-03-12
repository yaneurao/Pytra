// AUTO-GENERATED FILE. DO NOT EDIT.
// source: src/pytra/std/time.py
// generated-by: tools/gen_runtime_from_manifest.py

export function perf_counter(): number {
    return Number(process.hrtime.bigint()) / 1_000_000_000;
}

export const perfCounter = perf_counter;
