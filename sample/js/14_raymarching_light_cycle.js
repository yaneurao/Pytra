// このファイルは自動生成です（Python -> JavaScript native mode）。

const __pytra_root = process.cwd();
const py_runtime = require(__pytra_root + '/src/runtime/js/pytra/py_runtime.js');
const py_math = require(__pytra_root + '/src/runtime/js/pytra/math.js');
const py_time = require(__pytra_root + '/src/runtime/js/pytra/time.js');
const { pyPrint, pyLen, pyBool, pyRange, pyFloorDiv, pyMod, pyIn, pySlice, pyOrd, pyChr, pyBytearray, pyBytes, pyIsDigit, pyIsAlpha } = py_runtime;
const { perfCounter } = py_time;
const math = require(__pytra_root + '/src/runtime/js/pytra/math.js');
const perf_counter = perfCounter;
const { save_gif } = require(__pytra_root + '/src/runtime/js/pytra/gif_helper.js');

function palette() {
    let p = pyBytearray();
    let i;
    for (let __pytra_i_1 = 0; __pytra_i_1 < 256; __pytra_i_1 += 1) {
        i = __pytra_i_1;
        let r = Math.trunc(Number(((20) + (((i) * (0.9))))));
        if (pyBool(((r) > (255)))) {
            r = 255;
        }
        let g = Math.trunc(Number(((10) + (((i) * (0.7))))));
        if (pyBool(((g) > (255)))) {
            g = 255;
        }
        let b = Math.trunc(Number(((30) + (i))));
        if (pyBool(((b) > (255)))) {
            b = 255;
        }
        p.push(r);
        p.push(g);
        p.push(b);
    }
    return pyBytes(p);
}
function scene(x, y, light_x, light_y) {
    let x1 = ((x) + (0.45));
    let y1 = ((y) + (0.2));
    let x2 = ((x) - (0.35));
    let y2 = ((y) - (0.15));
    let r1 = math.sqrt(((((x1) * (x1))) + (((y1) * (y1)))));
    let r2 = math.sqrt(((((x2) * (x2))) + (((y2) * (y2)))));
    let blob = ((math.exp((((((-(7.0))) * (r1))) * (r1)))) + (math.exp((((((-(8.0))) * (r2))) * (r2)))));
    let lx = ((x) - (light_x));
    let ly = ((y) - (light_y));
    let l = math.sqrt(((((lx) * (lx))) + (((ly) * (ly)))));
    let lit = ((1.0) / (((1.0) + (((((3.5) * (l))) * (l))))));
    let v = Math.trunc(Number(((((((255.0) * (blob))) * (lit))) * (5.0))));
    if (pyBool(((v) < (0)))) {
        return 0;
    }
    if (pyBool(((v) > (255)))) {
        return 255;
    }
    return v;
}
function run_14_raymarching_light_cycle() {
    let w = 320;
    let h = 240;
    let frames_n = 84;
    let out_path = 'sample/out/14_raymarching_light_cycle.gif';
    let start = perf_counter();
    let frames = [];
    let t;
    for (let __pytra_i_2 = 0; __pytra_i_2 < frames_n; __pytra_i_2 += 1) {
        t = __pytra_i_2;
        let frame = pyBytearray(((w) * (h)));
        let a = ((((((t) / (frames_n))) * (math.pi))) * (2.0));
        let light_x = ((0.75) * (math.cos(a)));
        let light_y = ((0.55) * (math.sin(((a) * (1.2)))));
        let i = 0;
        let y;
        for (let __pytra_i_3 = 0; __pytra_i_3 < h; __pytra_i_3 += 1) {
            y = __pytra_i_3;
            let py = ((((((y) / (((h) - (1))))) * (2.0))) - (1.0));
            let x;
            for (let __pytra_i_4 = 0; __pytra_i_4 < w; __pytra_i_4 += 1) {
                x = __pytra_i_4;
                let px = ((((((x) / (((w) - (1))))) * (2.0))) - (1.0));
                frame[i] = scene(px, py, light_x, light_y);
                i = i + 1;
            }
        }
        frames.push(pyBytes(frame));
    }
    save_gif(out_path, w, h, frames, palette(), 3, 0);
    let elapsed = ((perf_counter()) - (start));
    pyPrint('output:', out_path);
    pyPrint('frames:', frames_n);
    pyPrint('elapsed_sec:', elapsed);
}
run_14_raymarching_light_cycle();
