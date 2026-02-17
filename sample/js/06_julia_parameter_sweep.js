// このファイルは自動生成です（Python -> JavaScript native mode）。

const __pytra_root = process.cwd();
const py_runtime = require(__pytra_root + '/src/js_module/py_runtime.js');
const py_math = require(__pytra_root + '/src/js_module/math.js');
const py_time = require(__pytra_root + '/src/js_module/time.js');
const { pyPrint, pyLen, pyBool, pyRange, pyFloorDiv, pyMod, pyIn, pySlice, pyOrd, pyChr, pyBytearray, pyBytes, pyIsDigit, pyIsAlpha } = py_runtime;
const { perfCounter } = py_time;
const math = require(__pytra_root + '/src/js_module/math.js');
const perf_counter = perfCounter;
const { save_gif } = require(__pytra_root + '/src/js_module/gif_helper.js');

function julia_palette() {
    let palette = pyBytearray(((256) * (3)));
    palette[0] = 0;
    palette[1] = 0;
    palette[2] = 0;
    let i;
    for (let __pytra_i_1 = 1; __pytra_i_1 < 256; __pytra_i_1 += 1) {
        i = __pytra_i_1;
        let t = ((((i) - (1))) / (254.0));
        let r = Math.trunc(Number(((255.0) * (((((((((9.0) * (((1.0) - (t))))) * (t))) * (t))) * (t))))));
        let g = Math.trunc(Number(((255.0) * (((((((((15.0) * (((1.0) - (t))))) * (((1.0) - (t))))) * (t))) * (t))))));
        let b = Math.trunc(Number(((255.0) * (((((((((8.5) * (((1.0) - (t))))) * (((1.0) - (t))))) * (((1.0) - (t))))) * (t))))));
        palette[((((i) * (3))) + (0))] = r;
        palette[((((i) * (3))) + (1))] = g;
        palette[((((i) * (3))) + (2))] = b;
    }
    return pyBytes(palette);
}
function render_frame(width, height, cr, ci, max_iter, phase) {
    let frame = pyBytearray(((width) * (height)));
    let idx = 0;
    let y;
    for (let __pytra_i_2 = 0; __pytra_i_2 < height; __pytra_i_2 += 1) {
        y = __pytra_i_2;
        let zy0 = (((-(1.2))) + (((2.4) * (((y) / (((height) - (1))))))));
        let x;
        for (let __pytra_i_3 = 0; __pytra_i_3 < width; __pytra_i_3 += 1) {
            x = __pytra_i_3;
            let zx = (((-(1.8))) + (((3.6) * (((x) / (((width) - (1))))))));
            let zy = zy0;
            let i = 0;
            while (pyBool(((i) < (max_iter)))) {
                let zx2 = ((zx) * (zx));
                let zy2 = ((zy) * (zy));
                if (pyBool(((((zx2) + (zy2))) > (4.0)))) {
                    break;
                }
                zy = ((((((2.0) * (zx))) * (zy))) + (ci));
                zx = ((((zx2) - (zy2))) + (cr));
                i = i + 1;
            }
            if (pyBool(((i) >= (max_iter)))) {
                frame[idx] = 0;
            } else {
                let color_index = ((1) + (pyMod(((pyFloorDiv(((i) * (224)), max_iter)) + (phase)), 255)));
                frame[idx] = color_index;
            }
            idx = idx + 1;
        }
    }
    return pyBytes(frame);
}
function run_06_julia_parameter_sweep() {
    let width = 320;
    let height = 240;
    let frames_n = 72;
    let max_iter = 180;
    let out_path = 'sample/out/06_julia_parameter_sweep.gif';
    let start = perf_counter();
    let frames = [];
    let center_cr = (-(0.745));
    let center_ci = 0.186;
    let radius_cr = 0.12;
    let radius_ci = 0.1;
    let start_offset = 20;
    let phase_offset = 180;
    let i;
    for (let __pytra_i_4 = 0; __pytra_i_4 < frames_n; __pytra_i_4 += 1) {
        i = __pytra_i_4;
        let t = ((pyMod(((i) + (start_offset)), frames_n)) / (frames_n));
        let angle = ((((2.0) * (math.pi))) * (t));
        let cr = ((center_cr) + (((radius_cr) * (math.cos(angle)))));
        let ci = ((center_ci) + (((radius_ci) * (math.sin(angle)))));
        let phase = pyMod(((phase_offset) + (((i) * (5)))), 255);
        frames.push(render_frame(width, height, cr, ci, max_iter, phase));
    }
    save_gif(out_path, width, height, frames, julia_palette(), 8, 0);
    let elapsed = ((perf_counter()) - (start));
    pyPrint('output:', out_path);
    pyPrint('frames:', frames_n);
    pyPrint('elapsed_sec:', elapsed);
}
run_06_julia_parameter_sweep();
