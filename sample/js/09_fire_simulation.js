// このファイルは自動生成です（Python -> JavaScript native mode）。

const __pytra_root = process.cwd();
const py_runtime = require(__pytra_root + '/src/runtime/js/pytra/py_runtime.js');
const py_math = require(__pytra_root + '/src/runtime/js/pytra/math.js');
const py_time = require(__pytra_root + '/src/runtime/js/pytra/time.js');
const { pyPrint, pyLen, pyBool, pyRange, pyFloorDiv, pyMod, pyIn, pySlice, pyOrd, pyChr, pyBytearray, pyBytes, pyIsDigit, pyIsAlpha } = py_runtime;
const { perfCounter } = py_time;
const perf_counter = perfCounter;
const { save_gif } = require(__pytra_root + '/src/runtime/js/pytra/gif_helper.js');

function fire_palette() {
    let p = pyBytearray();
    let i;
    for (let __pytra_i_1 = 0; __pytra_i_1 < 256; __pytra_i_1 += 1) {
        i = __pytra_i_1;
        let r = 0;
        let g = 0;
        let b = 0;
        if (pyBool(((i) < (85)))) {
            r = ((i) * (3));
            g = 0;
            b = 0;
        } else {
            if (pyBool(((i) < (170)))) {
                r = 255;
                g = ((((i) - (85))) * (3));
                b = 0;
            } else {
                r = 255;
                g = 255;
                b = ((((i) - (170))) * (3));
            }
        }
        p.push(r);
        p.push(g);
        p.push(b);
    }
    return pyBytes(p);
}
function run_09_fire_simulation() {
    let w = 380;
    let h = 260;
    let steps = 420;
    let out_path = 'sample/out/09_fire_simulation.gif';
    let start = perf_counter();
    let heat = [];
    let _;
    for (let __pytra_i_2 = 0; __pytra_i_2 < h; __pytra_i_2 += 1) {
        _ = __pytra_i_2;
        let row = [];
        for (let __pytra_i_3 = 0; __pytra_i_3 < w; __pytra_i_3 += 1) {
            _ = __pytra_i_3;
            row.push(0);
        }
        heat.push(row);
    }
    let frames = [];
    let t;
    for (let __pytra_i_4 = 0; __pytra_i_4 < steps; __pytra_i_4 += 1) {
        t = __pytra_i_4;
        let x;
        for (let __pytra_i_5 = 0; __pytra_i_5 < w; __pytra_i_5 += 1) {
            x = __pytra_i_5;
            let val = ((170) + (pyMod(((((x) * (13))) + (((t) * (17)))), 86)));
            heat[((h) - (1))][x] = val;
        }
        let y;
        for (let __pytra_i_6 = 1; __pytra_i_6 < h; __pytra_i_6 += 1) {
            y = __pytra_i_6;
            for (let __pytra_i_7 = 0; __pytra_i_7 < w; __pytra_i_7 += 1) {
                x = __pytra_i_7;
                let a = heat[y][x];
                let b = heat[y][pyMod(((((x) - (1))) + (w)), w)];
                let c = heat[y][pyMod(((x) + (1)), w)];
                let d = heat[pyMod(((y) + (1)), h)][x];
                let v = pyFloorDiv(((((((a) + (b))) + (c))) + (d)), 4);
                let cool = ((1) + (pyMod(((((x) + (y))) + (t)), 3)));
                let nv = ((v) - (cool));
                heat[((y) - (1))][x] = (pyBool(((nv) > (0))) ? nv : 0);
            }
        }
        let frame = pyBytearray(((w) * (h)));
        let i = 0;
        let yy;
        for (let __pytra_i_8 = 0; __pytra_i_8 < h; __pytra_i_8 += 1) {
            yy = __pytra_i_8;
            let xx;
            for (let __pytra_i_9 = 0; __pytra_i_9 < w; __pytra_i_9 += 1) {
                xx = __pytra_i_9;
                frame[i] = heat[yy][xx];
                i = i + 1;
            }
        }
        frames.push(pyBytes(frame));
    }
    save_gif(out_path, w, h, frames, fire_palette(), 4, 0);
    let elapsed = ((perf_counter()) - (start));
    pyPrint('output:', out_path);
    pyPrint('frames:', steps);
    pyPrint('elapsed_sec:', elapsed);
}
run_09_fire_simulation();
