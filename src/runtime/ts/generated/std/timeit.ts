// AUTO-GENERATED FILE. DO NOT EDIT.
// source: src/pytra/std/timeit.py
// generated-by: tools/gen_runtime_from_manifest.py

const { perf_counter } = require("./time.js");

function default_timer() {
    return perf_counter();
}

module.exports = {default_timer};
