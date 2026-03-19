// AUTO-GENERATED FILE. DO NOT EDIT.
// source: src/pytra/std/time.py
// generated-by: tools/gen_runtime_from_manifest.py

#ifndef PYTRA_GEN_STD_TIME_H
#define PYTRA_GEN_STD_TIME_H

// forward declarations
float64 perf_counter();

/* pytra.std.time: extern-marked time API with Python runtime fallback. */

float64 perf_counter() {
    return __t.perf_counter();
}

#endif  // PYTRA_GEN_STD_TIME_H
