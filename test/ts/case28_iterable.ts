// このファイルは自動生成です（Python -> TypeScript native mode）。

const __pytra_root = process.cwd();
const py_runtime = require(__pytra_root + '/src/ts_module/py_runtime.ts');
const py_math = require(__pytra_root + '/src/ts_module/math.ts');
const py_time = require(__pytra_root + '/src/ts_module/time.ts');
const { pyPrint, pyLen, pyBool, pyRange, pyFloorDiv, pyMod, pyIn, pySlice, pyOrd, pyChr, pyBytearray, pyBytes, pyIsDigit, pyIsAlpha } = py_runtime;
const { perfCounter } = py_time;

function main() {
    let l = [1, 2, 3];
    let sum = 0;
    let v;
    for (const __pytra_it_1 of l) {
        v = __pytra_it_1;
        sum = sum + v;
    }
    pyPrint(sum);
}
main();
