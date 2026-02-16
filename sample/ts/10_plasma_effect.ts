// このファイルは自動生成です（Python -> TypeScript native mode）。

const __pytra_root = process.cwd();
const py_runtime = require(__pytra_root + '/src/ts_module/py_runtime.ts');
const py_math = require(__pytra_root + '/src/ts_module/math.ts');
const py_time = require(__pytra_root + '/src/ts_module/time.ts');
const { pyPrint, pyLen, pyBool, pyRange, pyFloorDiv, pyMod, pyIn, pySlice, pyOrd, pyChr, pyBytearray, pyBytes, pyIsDigit, pyIsAlpha } = py_runtime;
const { perfCounter } = py_time;
const math = require(__pytra_root + '/src/ts_module/math.ts');
const perf_counter = perfCounter;
const { grayscale_palette, save_gif } = require(__pytra_root + '/src/ts_module/gif_helper.ts');

function run_10_plasma_effect() {
    let w = 320;
    let h = 240;
    let frames_n = 216;
    let out_path = 'sample/out/10_plasma_effect.gif';
    let start = perf_counter();
    let frames = [];
    let t;
    for (let __pytra_i_1 = 0; __pytra_i_1 < frames_n; __pytra_i_1 += 1) {
        t = __pytra_i_1;
        let frame = pyBytearray(((w) * (h)));
        let i = 0;
        let y;
        for (let __pytra_i_2 = 0; __pytra_i_2 < h; __pytra_i_2 += 1) {
            y = __pytra_i_2;
            let x;
            for (let __pytra_i_3 = 0; __pytra_i_3 < w; __pytra_i_3 += 1) {
                x = __pytra_i_3;
                let dx = ((x) - (160));
                let dy = ((y) - (120));
                let v = ((((((math.sin(((((x) + (((t) * (2.0))))) * (0.045)))) + (math.sin(((((y) - (((t) * (1.2))))) * (0.05)))))) + (math.sin(((((((x) + (y))) + (((t) * (1.7))))) * (0.03)))))) + (math.sin(((((math.sqrt(((((dx) * (dx))) + (((dy) * (dy)))))) * (0.07))) - (((t) * (0.18)))))));
                let c = Math.trunc(Number(((((v) + (4.0))) * (((255.0) / (8.0))))));
                if (pyBool(((c) < (0)))) {
                    c = 0;
                }
                if (pyBool(((c) > (255)))) {
                    c = 255;
                }
                frame[i] = c;
                i = i + 1;
            }
        }
        frames.push(pyBytes(frame));
    }
    save_gif(out_path, w, h, frames, grayscale_palette(), 3, 0);
    let elapsed = ((perf_counter()) - (start));
    pyPrint('output:', out_path);
    pyPrint('frames:', frames_n);
    pyPrint('elapsed_sec:', elapsed);
}
run_10_plasma_effect();
