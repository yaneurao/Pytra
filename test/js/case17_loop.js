// このファイルは自動生成です（Python -> JavaScript native mode）。

const __pytra_root = process.cwd();
const py_runtime = require(__pytra_root + '/src/js_module/py_runtime.js');
const py_math = require(__pytra_root + '/src/js_module/math.js');
const py_time = require(__pytra_root + '/src/js_module/time.js');
const { pyPrint, pyLen, pyBool, pyRange, pyFloorDiv, pyMod, pyIn, pySlice, pyOrd, pyChr, pyBytearray, pyBytes, pyIsDigit, pyIsAlpha } = py_runtime;
const { perfCounter } = py_time;

function calc_17(values) {
    let total = 0;
    let v;
    for (const __pytra_it_1 of values) {
        v = __pytra_it_1;
        if (pyBool(((pyMod(v, 2)) === (0)))) {
            total = total + v;
        } else {
            total = total + ((v) * (2));
        }
    }
    return total;
}
pyPrint(calc_17([1, 2, 3, 4]));
