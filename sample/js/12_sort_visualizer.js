// このファイルは自動生成です（Python -> JavaScript native mode）。

const __pytra_root = process.cwd();
const py_runtime = require(__pytra_root + '/src/js_module/py_runtime.js');
const py_math = require(__pytra_root + '/src/js_module/math.js');
const py_time = require(__pytra_root + '/src/js_module/time.js');
const { pyPrint, pyLen, pyBool, pyRange, pyFloorDiv, pyMod, pyIn, pySlice, pyOrd, pyChr, pyBytearray, pyBytes, pyIsDigit, pyIsAlpha } = py_runtime;
const { perfCounter } = py_time;
const perf_counter = perfCounter;
const { grayscale_palette, save_gif } = require(__pytra_root + '/src/js_module/gif_helper.js');

function render(values, w, h) {
    let frame = pyBytearray(((w) * (h)));
    let n = pyLen(values);
    let bar_w = ((w) / (n));
    let i;
    for (let __pytra_i_1 = 0; __pytra_i_1 < n; __pytra_i_1 += 1) {
        i = __pytra_i_1;
        let x0 = Math.trunc(Number(((i) * (bar_w))));
        let x1 = Math.trunc(Number(((((i) + (1))) * (bar_w))));
        if (pyBool(((x1) <= (x0)))) {
            x1 = ((x0) + (1));
        }
        let bh = Math.trunc(Number(((((values[i]) / (n))) * (h))));
        let y = ((h) - (bh));
        for (let __pytra_i_2 = y; __pytra_i_2 < h; __pytra_i_2 += 1) {
            y = __pytra_i_2;
            let x;
            for (let __pytra_i_3 = x0; __pytra_i_3 < x1; __pytra_i_3 += 1) {
                x = __pytra_i_3;
                frame[((((y) * (w))) + (x))] = 255;
            }
        }
    }
    return pyBytes(frame);
}
function run_12_sort_visualizer() {
    let w = 320;
    let h = 180;
    let n = 124;
    let out_path = 'sample/out/12_sort_visualizer.gif';
    let start = perf_counter();
    let values = [];
    let i;
    for (let __pytra_i_4 = 0; __pytra_i_4 < n; __pytra_i_4 += 1) {
        i = __pytra_i_4;
        values.push(pyMod(((((i) * (37))) + (19)), n));
    }
    let frames = [render(values, w, h)];
    let op = 0;
    for (let __pytra_i_5 = 0; __pytra_i_5 < n; __pytra_i_5 += 1) {
        i = __pytra_i_5;
        let swapped = false;
        let j;
        for (let __pytra_i_6 = 0; __pytra_i_6 < ((((n) - (i))) - (1)); __pytra_i_6 += 1) {
            j = __pytra_i_6;
            if (pyBool(((values[j]) > (values[((j) + (1))])))) {
                let tmp = values[j];
                values[j] = values[((j) + (1))];
                values[((j) + (1))] = tmp;
                swapped = true;
            }
            if (pyBool(((pyMod(op, 8)) === (0)))) {
                frames.push(render(values, w, h));
            }
            op = op + 1;
        }
        if (pyBool((!pyBool(swapped)))) {
            break;
        }
    }
    save_gif(out_path, w, h, frames, grayscale_palette(), 3, 0);
    let elapsed = ((perf_counter()) - (start));
    pyPrint('output:', out_path);
    pyPrint('frames:', pyLen(frames));
    pyPrint('elapsed_sec:', elapsed);
}
run_12_sort_visualizer();
