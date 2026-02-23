// このファイルは EAST ベース TypeScript プレビュー出力です。
// TODO: 専用 TSEmitter 実装へ段階移行する。
const __pytra_root = process.cwd();
const py_runtime = require(__pytra_root + '/src/js_module/py_runtime.js');
const { PYTRA_TYPE_ID, PY_TYPE_BOOL, PY_TYPE_NUMBER, PY_TYPE_STRING, PY_TYPE_ARRAY, PY_TYPE_MAP, PY_TYPE_SET, PY_TYPE_OBJECT, pyRegisterClassType, pyIsInstance } = py_runtime;

import { perf_counter } from "./time.js";

// 17: Sample that scans a large grid using integer arithmetic only and computes a checksum.
// It avoids floating-point error effects, making cross-language comparisons easier.

function run_integer_grid_checksum(width, height, seed) {
    let mod_main = 2147483647;
    let mod_out = 1000000007;
    let acc = (seed % mod_out);
    
    for (let y = 0; y < height; y += 1) {
        let row_sum = 0;
        for (let x = 0; x < width; x += 1) {
            let v = (((((x * 37) + (y * 73)) + seed)) % mod_main);
            v = ((((v * 48271) + 1)) % mod_main);
            row_sum += (v % 256);
        }
        acc = (((acc + (row_sum * ((y + 1))))) % mod_out);
    }
    return acc;
}

function run_integer_benchmark() {
    let width = 2400;
    let height = 1600;
    
    let start = perf_counter();
    let checksum = run_integer_grid_checksum(width, height, 123456789);
    let elapsed = (perf_counter() - start);
    
    console.log("pixels:", (width * height));
    console.log("checksum:", checksum);
    console.log("elapsed_sec:", elapsed);
}

// __main__ guard
run_integer_benchmark();
