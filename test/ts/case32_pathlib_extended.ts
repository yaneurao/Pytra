// このファイルは自動生成です（Python -> TypeScript native mode）。

const __pytra_root = process.cwd();
const py_runtime = require(__pytra_root + '/src/ts_module/py_runtime.ts');
const py_math = require(__pytra_root + '/src/ts_module/math.ts');
const py_time = require(__pytra_root + '/src/ts_module/time.ts');
const pathlib = require(__pytra_root + '/src/ts_module/pathlib.ts');
const { pyPrint, pyLen, pyBool, pyRange, pyFloorDiv, pyMod, pyIn, pySlice, pyOrd, pyChr, pyBytearray, pyBytes, pyIsDigit, pyIsAlpha } = py_runtime;
const { perfCounter } = py_time;
const Path = pathlib.Path;

function main() {
    let root = new pathlib.Path('test/obj/pathlib_case32');
    root.mkdir(true, true);
    let child = pathlib.pathJoin(root, 'values.txt');
    child.write_text('42');
    pyPrint(child.exists());
    pyPrint(child.name());
    pyPrint(child.stem());
    pyPrint(pathlib.pathJoin(child.parent(), 'values.txt').exists());
    pyPrint(child.read_text());
}
main();
