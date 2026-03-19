// AUTO-GENERATED FILE. DO NOT EDIT.
// source: src/pytra/std/timeit.py
// generated-by: tools/gen_runtime_from_manifest.py

#ifndef PYTRA_GEN_STD_TIMEIT_H
#define PYTRA_GEN_STD_TIMEIT_H

// forward declarations
float64 default_timer();

/* pytra.std.timeit compatibility shim. */

float64 default_timer() {
    /* `timeit.default_timer` compatible entrypoint. */
    return pytra::std::time::perf_counter();
}

#endif  // PYTRA_GEN_STD_TIMEIT_H
