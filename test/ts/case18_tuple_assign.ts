// このファイルは自動生成です（Python -> TypeScript native mode）。

const __pytra_root = process.cwd();
const py_runtime = require(__pytra_root + '/src/ts_module/py_runtime.ts');
const py_math = require(__pytra_root + '/src/ts_module/math.ts');
const py_time = require(__pytra_root + '/src/ts_module/time.ts');
const { pyPrint, pyLen, pyBool, pyRange, pyFloorDiv, pyMod, pyIn, pySlice, pyOrd, pyChr, pyBytearray, pyBytes, pyIsDigit, pyIsAlpha } = py_runtime;
const { perfCounter } = py_time;

function swap_sum_18(a, b) {
    let x = a;
    let y = b;
    const __pytra_tuple_1 = [y, x];
    x = __pytra_tuple_1[0];
    y = __pytra_tuple_1[1];
    return ((x) + (y));
}
pyPrint(swap_sum_18(10, 20));
