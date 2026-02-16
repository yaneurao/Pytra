// このファイルは自動生成です（Python -> JavaScript native mode）。

const __pytra_root = process.cwd();
const py_runtime = require(__pytra_root + '/src/js_module/py_runtime.js');
const py_math = require(__pytra_root + '/src/js_module/math.js');
const py_time = require(__pytra_root + '/src/js_module/time.js');
const { pyPrint, pyLen, pyBool, pyRange, pyFloorDiv, pyMod, pyIn, pySlice, pyOrd, pyChr, pyBytearray, pyBytes, pyIsDigit, pyIsAlpha } = py_runtime;
const { perfCounter } = py_time;
const perf_counter = perfCounter;

function lcg_next(state) {
    return pyMod(((((1664525) * (state))) + (1013904223)), 4294967296);
}
function run_pi_trial(total_samples, seed) {
    let inside = 0;
    let state = seed;
    let _;
    for (let __pytra_i_1 = 0; __pytra_i_1 < total_samples; __pytra_i_1 += 1) {
        _ = __pytra_i_1;
        state = lcg_next(state);
        let x = ((state) / (4294967296.0));
        state = lcg_next(state);
        let y = ((state) / (4294967296.0));
        let dx = ((x) - (0.5));
        let dy = ((y) - (0.5));
        if (pyBool(((((((dx) * (dx))) + (((dy) * (dy))))) <= (0.25)))) {
            inside = inside + 1;
        }
    }
    return ((((4.0) * (inside))) / (total_samples));
}
function run_monte_carlo_pi() {
    let samples = 54000000;
    let seed = 123456789;
    let start = perf_counter();
    let pi_est = run_pi_trial(samples, seed);
    let elapsed = ((perf_counter()) - (start));
    pyPrint('samples:', samples);
    pyPrint('pi_estimate:', pi_est);
    pyPrint('elapsed_sec:', elapsed);
}
run_monte_carlo_pi();
