// このファイルは自動生成です（Python -> JavaScript native mode）。

const __pytra_root = process.cwd();
const py_runtime = require(__pytra_root + '/src/js_module/py_runtime.js');
const py_math = require(__pytra_root + '/src/js_module/math.js');
const py_time = require(__pytra_root + '/src/js_module/time.js');
const pathlib = require(__pytra_root + '/src/js_module/pathlib.js');
const { pyPrint, pyLen, pyBool, pyRange, pyFloorDiv, pyMod, pyIn, pySlice, pyOrd, pyChr, pyBytearray, pyBytes, pyIsDigit, pyIsAlpha } = py_runtime;
const { perfCounter } = py_time;
const math = require(__pytra_root + '/src/js_module/math.js');

function main() {
    pyPrint(((math.fabs(math.tan(0.0))) < (1e-12)));
    pyPrint(((math.fabs(((math.log(math.exp(1.0))) - (1.0)))) < (1e-12)));
    pyPrint(Math.trunc(Number(math.log10(1000.0))));
    pyPrint(Math.trunc(Number(((math.fabs((-(3.5)))) * (10.0)))));
    pyPrint(Math.trunc(Number(math.ceil(2.1))));
    pyPrint(Math.trunc(Number(math.pow(2.0, 5.0))));
}
main();
