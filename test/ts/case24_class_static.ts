// このファイルは自動生成です（Python -> TypeScript native mode）。

const __pytra_root = process.cwd();
const py_runtime = require(__pytra_root + '/src/ts_module/py_runtime.ts');
const py_math = require(__pytra_root + '/src/ts_module/math.ts');
const py_time = require(__pytra_root + '/src/ts_module/time.ts');
const { pyPrint, pyLen, pyBool, pyRange, pyFloorDiv, pyMod, pyIn, pySlice, pyOrd, pyChr, pyBytearray, pyBytes, pyIsDigit, pyIsAlpha } = py_runtime;
const { perfCounter } = py_time;

class Counter26 {
    constructor() {}

    add(x) {
        Counter26.total = Counter26.total + x;
        return Counter26.total;
    }
}
Counter26.total = 0;
let c = new Counter26();
pyPrint(c.add(5));
