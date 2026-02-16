// このファイルは自動生成です（Python -> JavaScript native mode）。

const __pytra_root = process.cwd();
const py_runtime = require(__pytra_root + '/src/js_module/py_runtime.js');
const py_math = require(__pytra_root + '/src/js_module/math.js');
const py_time = require(__pytra_root + '/src/js_module/time.js');
const { pyPrint, pyLen, pyBool, pyRange, pyFloorDiv, pyMod, pyIn, pySlice, pyOrd, pyChr, pyBytearray, pyBytes, pyIsDigit, pyIsAlpha } = py_runtime;
const { perfCounter } = py_time;

function comp_like_24(x) {
    let values = (() => {
    const __pytra_listcomp_1 = [];
    for (const i of [1, 2, 3, 4]) {
        __pytra_listcomp_1.push(i);
    }
    return __pytra_listcomp_1;
})();
    return ((x) + (1));
}
pyPrint(comp_like_24(5));
