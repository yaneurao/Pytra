// このファイルは自動生成です（Python -> TypeScript native mode）。

const __pytra_root = process.cwd();
const py_runtime = require(__pytra_root + '/src/runtime/ts/pytra/py_runtime.ts');
const py_math = require(__pytra_root + '/src/runtime/ts/pytra/math.ts');
const py_time = require(__pytra_root + '/src/runtime/ts/pytra/time.ts');
const { pyPrint, pyLen, pyBool, pyRange, pyFloorDiv, pyMod, pyIn, pySlice, pyOrd, pyChr, pyBytearray, pyBytes, pyIsDigit, pyIsAlpha } = py_runtime;
const { perfCounter } = py_time;
const perf_counter = perfCounter;
const { grayscale_palette, save_gif } = require(__pytra_root + '/src/runtime/ts/pytra/gif_helper.ts');

function render_frame(width, height, center_x, center_y, scale, max_iter) {
    let frame = pyBytearray(((width) * (height)));
    let idx = 0;
    let y;
    for (let __pytra_i_1 = 0; __pytra_i_1 < height; __pytra_i_1 += 1) {
        y = __pytra_i_1;
        let cy = ((center_y) + (((((y) - (((height) * (0.5))))) * (scale))));
        let x;
        for (let __pytra_i_2 = 0; __pytra_i_2 < width; __pytra_i_2 += 1) {
            x = __pytra_i_2;
            let cx = ((center_x) + (((((x) - (((width) * (0.5))))) * (scale))));
            let zx = 0.0;
            let zy = 0.0;
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
            frame[idx] = Math.trunc(Number(((((255.0) * (i))) / (max_iter))));
            idx = idx + 1;
        }
    }
    return pyBytes(frame);
}
function run_05_mandelbrot_zoom() {
    let width = 320;
    let height = 240;
    let frame_count = 48;
    let max_iter = 110;
    let center_x = (-(0.743643887037151));
    let center_y = 0.13182590420533;
    let base_scale = ((3.2) / (width));
    let zoom_per_frame = 0.93;
    let out_path = 'sample/out/05_mandelbrot_zoom.gif';
    let start = perf_counter();
    let frames = [];
    let scale = base_scale;
    let _;
    for (let __pytra_i_3 = 0; __pytra_i_3 < frame_count; __pytra_i_3 += 1) {
        _ = __pytra_i_3;
        frames.push(render_frame(width, height, center_x, center_y, scale, max_iter));
        scale = scale * zoom_per_frame;
    }
    save_gif(out_path, width, height, frames, grayscale_palette(), 5, 0);
    let elapsed = ((perf_counter()) - (start));
    pyPrint('output:', out_path);
    pyPrint('frames:', frame_count);
    pyPrint('elapsed_sec:', elapsed);
}
run_05_mandelbrot_zoom();
