// このファイルは自動生成です（Python -> TypeScript native mode）。

const __pytra_root = process.cwd();
const py_runtime = require(__pytra_root + '/src/ts_module/py_runtime.ts');
const py_math = require(__pytra_root + '/src/ts_module/math.ts');
const py_time = require(__pytra_root + '/src/ts_module/time.ts');
const { pyPrint, pyLen, pyBool, pyRange, pyFloorDiv, pyMod, pyIn, pySlice, pyOrd, pyChr, pyBytearray, pyBytes, pyIsDigit, pyIsAlpha } = py_runtime;
const { perfCounter } = py_time;
const perf_counter = perfCounter;
const png_helper = require(__pytra_root + '/src/ts_module/png_helper.ts');

function escape_count(cx, cy, max_iter) {
    let x = 0.0;
    let y = 0.0;
    let i;
    for (let __pytra_i_1 = 0; __pytra_i_1 < max_iter; __pytra_i_1 += 1) {
        i = __pytra_i_1;
        let x2 = ((x) * (x));
        let y2 = ((y) * (y));
        if (pyBool(((((x2) + (y2))) > (4.0)))) {
            return i;
        }
        y = ((((((2.0) * (x))) * (y))) + (cy));
        x = ((((x2) - (y2))) + (cx));
    }
    return max_iter;
}
function color_map(iter_count, max_iter) {
    if (pyBool(((iter_count) >= (max_iter)))) {
        return [0, 0, 0];
    }
    let t = ((iter_count) / (max_iter));
    let r = Math.trunc(Number(((255.0) * (((t) * (t))))));
    let g = Math.trunc(Number(((255.0) * (t))));
    let b = Math.trunc(Number(((255.0) * (((1.0) - (t))))));
    return [r, g, b];
}
function render_mandelbrot(width, height, max_iter, x_min, x_max, y_min, y_max) {
    let pixels = pyBytearray();
    let y;
    for (let __pytra_i_2 = 0; __pytra_i_2 < height; __pytra_i_2 += 1) {
        y = __pytra_i_2;
        let py = ((y_min) + (((((y_max) - (y_min))) * (((y) / (((height) - (1))))))));
        let x;
        for (let __pytra_i_3 = 0; __pytra_i_3 < width; __pytra_i_3 += 1) {
            x = __pytra_i_3;
            let px = ((x_min) + (((((x_max) - (x_min))) * (((x) / (((width) - (1))))))));
            let it = escape_count(px, py, max_iter);
            let r = null;
            let g = null;
            let b = null;
            if (pyBool(((it) >= (max_iter)))) {
                r = 0;
                g = 0;
                b = 0;
            } else {
                let t = ((it) / (max_iter));
                r = Math.trunc(Number(((255.0) * (((t) * (t))))));
                g = Math.trunc(Number(((255.0) * (t))));
                b = Math.trunc(Number(((255.0) * (((1.0) - (t))))));
            }
            pixels.push(r);
            pixels.push(g);
            pixels.push(b);
        }
    }
    return pixels;
}
function run_mandelbrot() {
    let width = 1600;
    let height = 1200;
    let max_iter = 1000;
    let out_path = 'sample/out/01_mandelbrot.png';
    let start = perf_counter();
    let pixels = render_mandelbrot(width, height, max_iter, (-(2.2)), 1.0, (-(1.2)), 1.2);
    png_helper.write_rgb_png(out_path, width, height, pixels);
    let elapsed = ((perf_counter()) - (start));
    pyPrint('output:', out_path);
    pyPrint('size:', width, 'x', height);
    pyPrint('max_iter:', max_iter);
    pyPrint('elapsed_sec:', elapsed);
}
run_mandelbrot();
