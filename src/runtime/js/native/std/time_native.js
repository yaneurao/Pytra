// Generated std/time.js delegates host bindings through this native seam.

function perf_counter() {
    return Number(process.hrtime.bigint()) / 1_000_000_000;
}

const perfCounter = perf_counter;

module.exports = {perf_counter, perfCounter};
