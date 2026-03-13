// AUTO-GENERATED FILE. DO NOT EDIT.
// source: src/pytra/std/timeit.py
// generated-by: tools/gen_runtime_from_manifest.py

import { perf_counter } from "./pytra/std/time.js";

function default_timer() {
    return perf_counter();
}

module.exports = {default_timer};
