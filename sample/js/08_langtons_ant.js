// このファイルは自動生成です（Python -> JavaScript native mode）。

const __pytra_root = process.cwd();
const py_runtime = require(__pytra_root + '/src/runtime/js/pytra/py_runtime.js');
const py_math = require(__pytra_root + '/src/runtime/js/pytra/math.js');
const py_time = require(__pytra_root + '/src/runtime/js/pytra/time.js');
const { pyPrint, pyLen, pyBool, pyRange, pyFloorDiv, pyMod, pyIn, pySlice, pyOrd, pyChr, pyBytearray, pyBytes, pyIsDigit, pyIsAlpha } = py_runtime;
const { perfCounter } = py_time;
const perf_counter = perfCounter;
const { grayscale_palette, save_gif } = require(__pytra_root + '/src/runtime/js/pytra/gif_helper.js');

function capture(grid, w, h) {
    let frame = pyBytearray(((w) * (h)));
    let i = 0;
    let y;
    for (let __pytra_i_1 = 0; __pytra_i_1 < h; __pytra_i_1 += 1) {
        y = __pytra_i_1;
        let x;
        for (let __pytra_i_2 = 0; __pytra_i_2 < w; __pytra_i_2 += 1) {
            x = __pytra_i_2;
            frame[i] = (pyBool(grid[y][x]) ? 255 : 0);
            i = i + 1;
        }
    }
    return pyBytes(frame);
}
function run_08_langtons_ant() {
    let w = 420;
    let h = 420;
    let out_path = 'sample/out/08_langtons_ant.gif';
    let start = perf_counter();
    let grid = [];
    let gy;
    for (let __pytra_i_3 = 0; __pytra_i_3 < h; __pytra_i_3 += 1) {
        gy = __pytra_i_3;
        let row = [];
        let gx;
        for (let __pytra_i_4 = 0; __pytra_i_4 < w; __pytra_i_4 += 1) {
            gx = __pytra_i_4;
            row.push(0);
        }
        grid.push(row);
    }
    let x = pyFloorDiv(w, 2);
    let y = pyFloorDiv(h, 2);
    let d = 0;
    let steps_total = 600000;
    let capture_every = 3000;
    let frames = [];
    let i;
    for (let __pytra_i_5 = 0; __pytra_i_5 < steps_total; __pytra_i_5 += 1) {
        i = __pytra_i_5;
        if (pyBool(((grid[y][x]) === (0)))) {
            d = pyMod(((d) + (1)), 4);
            grid[y][x] = 1;
        } else {
            d = pyMod(((d) + (3)), 4);
            grid[y][x] = 0;
        }
        if (pyBool(((d) === (0)))) {
            y = pyMod(((((y) - (1))) + (h)), h);
        } else {
            if (pyBool(((d) === (1)))) {
                x = pyMod(((x) + (1)), w);
            } else {
                if (pyBool(((d) === (2)))) {
                    y = pyMod(((y) + (1)), h);
                } else {
                    x = pyMod(((((x) - (1))) + (w)), w);
                }
            }
        }
        if (pyBool(((pyMod(i, capture_every)) === (0)))) {
            frames.push(capture(grid, w, h));
        }
    }
    save_gif(out_path, w, h, frames, grayscale_palette(), 5, 0);
    let elapsed = ((perf_counter()) - (start));
    pyPrint('output:', out_path);
    pyPrint('frames:', pyLen(frames));
    pyPrint('elapsed_sec:', elapsed);
}
run_08_langtons_ant();
