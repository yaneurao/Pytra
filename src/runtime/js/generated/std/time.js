// AUTO-GENERATED FILE. DO NOT EDIT.
// source: src/pytra/std/time.py
// generated-by: tools/gen_runtime_from_manifest.py

function perf_counter() {
    return Number(process.hrtime.bigint()) / 1_000_000_000;
}

const perfCounter = perf_counter;
module.exports = {perf_counter, perfCounter};
