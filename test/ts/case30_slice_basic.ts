// このファイルは自動生成です（Python -> TypeScript native mode）。

const __pytra_root = process.cwd();
const py_runtime = require(__pytra_root + '/src/ts_module/py_runtime.ts');
const py_math = require(__pytra_root + '/src/ts_module/math.ts');
const py_time = require(__pytra_root + '/src/ts_module/time.ts');
const { pyPrint, pyLen, pyBool, pyRange, pyFloorDiv, pyMod, pyIn, pySlice, pyOrd, pyChr, pyBytearray, pyBytes, pyIsDigit, pyIsAlpha } = py_runtime;
const { perfCounter } = py_time;

function main() {
    let nums = [10, 20, 30, 40, 50];
    let text = 'abcdef';
    let mid_nums = pySlice(nums, 1, 4);
    let mid_text = pySlice(text, 2, 5);
    pyPrint(mid_nums[0]);
    pyPrint(mid_nums[2]);
    pyPrint(mid_text);
}
main();
