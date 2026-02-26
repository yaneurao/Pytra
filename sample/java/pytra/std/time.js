const rt = require(process.cwd() + '/src/runtime/js/pytra/time.js');
const perf_counter = typeof rt.perf_counter === 'function' ? rt.perf_counter : rt.perfCounter;
exports.perf_counter = perf_counter;
exports.perfCounter = perf_counter;
