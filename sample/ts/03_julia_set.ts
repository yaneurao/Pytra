// このファイルは自動生成です（Python -> TypeScript native mode）。

const __pytra_root = process.cwd();
const py_runtime = require(__pytra_root + '/src/runtime/ts/pytra/py_runtime.ts');
const py_math = require(__pytra_root + '/src/runtime/ts/pytra/math.ts');
const py_time = require(__pytra_root + '/src/runtime/ts/pytra/time.ts');
const { pyPrint, pyLen, pyBool, pyRange, pyFloorDiv, pyMod, pyIn, pySlice, pyOrd, pyChr, pyBytearray, pyBytes, pyIsDigit, pyIsAlpha } = py_runtime;
const { perfCounter } = py_time;
const perf_counter = perfCounter;
const png_helper = require(__pytra_root + '/src/runtime/ts/pytra/png_helper.ts');

function render_julia(width, height, max_iter, cx, cy) {
    let pixels = pyBytearray();
    let y;
    for (let __pytra_i_1 = 0; __pytra_i_1 < height; __pytra_i_1 += 1) {
        y = __pytra_i_1;
        let zy0 = (((-(1.2))) + (((2.4) * (((y) / (((height) - (1))))))));
        let x;
        for (let __pytra_i_2 = 0; __pytra_i_2 < width; __pytra_i_2 += 1) {
            x = __pytra_i_2;
            let zx = (((-(1.8))) + (((3.6) * (((x) / (((width) - (1))))))));
            let zy = zy0;
            let i = 0;
            while (pyBool(((i) < (max_iter)))) {
                let zx2 = ((zx) * (zx));
                let zy2 = ((zy) * (zy));
                if (pyBool(((((zx2) + (zy2))) > (4.0)))) {
                    break;
                }
                zy = ((((((2.0) * (zx))) * (zy))) + (cy));
                zx = ((((zx2) - (zy2))) + (cx));
                i = i + 1;
            }
            let r = 0;
            let g = 0;
            let b = 0;
            if (pyBool(((i) >= (max_iter)))) {
                r = 0;
                g = 0;
                b = 0;
            } else {
                let t = ((i) / (max_iter));
                r = Math.trunc(Number(((255.0) * (((0.2) + (((0.8) * (t))))))));
                g = Math.trunc(Number(((255.0) * (((0.1) + (((0.9) * (((t) * (t))))))))));
                b = Math.trunc(Number(((255.0) * (((1.0) - (t))))));
            }
            pixels.push(r);
            pixels.push(g);
            pixels.push(b);
        }
    }
    return pixels;
}
function run_julia() {
    let width = 3840;
    let height = 2160;
    let max_iter = 20000;
    let out_path = 'sample/out/03_julia_set.png';
    let start = perf_counter();
    let pixels = render_julia(width, height, max_iter, (-(0.8)), 0.156);
    png_helper.write_rgb_png(out_path, width, height, pixels);
    let elapsed = ((perf_counter()) - (start));
    pyPrint('output:', out_path);
    pyPrint('size:', width, 'x', height);
    pyPrint('max_iter:', max_iter);
    pyPrint('elapsed_sec:', elapsed);
}
run_julia();
