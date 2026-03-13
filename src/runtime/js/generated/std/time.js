// AUTO-GENERATED FILE. DO NOT EDIT.
// source: src/pytra/std/time.py
// generated-by: tools/gen_runtime_from_manifest.py

const time_native = require("../../native/std/time_native.js");

function perf_counter() {
    return time_native.perf_counter();
}

const perfCounter = perf_counter;
module.exports = { perf_counter, perfCounter };
