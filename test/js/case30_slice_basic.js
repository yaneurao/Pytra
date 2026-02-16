// このファイルは自動生成です（Python -> JavaScript native mode）。

const __pytra_root = process.cwd();
const py_runtime = require(__pytra_root + '/src/js_module/py_runtime.js');
const py_math = require(__pytra_root + '/src/js_module/math.js');
const py_time = require(__pytra_root + '/src/js_module/time.js');
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
