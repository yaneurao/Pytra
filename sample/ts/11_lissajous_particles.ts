// このファイルは自動生成です（Python -> TypeScript native mode）。

const __pytra_root = process.cwd();
const py_runtime = require(__pytra_root + '/src/runtime/ts/pytra/py_runtime.ts');
const py_math = require(__pytra_root + '/src/runtime/ts/pytra/math.ts');
const py_time = require(__pytra_root + '/src/runtime/ts/pytra/time.ts');
const { pyPrint, pyLen, pyBool, pyRange, pyFloorDiv, pyMod, pyIn, pySlice, pyOrd, pyChr, pyBytearray, pyBytes, pyIsDigit, pyIsAlpha } = py_runtime;
const { perfCounter } = py_time;
const math = require(__pytra_root + '/src/runtime/ts/pytra/math.ts');
const perf_counter = perfCounter;
const { save_gif } = require(__pytra_root + '/src/runtime/ts/pytra/gif_helper.ts');

function color_palette() {
    let p = pyBytearray();
    let i;
    for (let __pytra_i_1 = 0; __pytra_i_1 < 256; __pytra_i_1 += 1) {
        i = __pytra_i_1;
        let r = i;
        let g = pyMod(((i) * (3)), 256);
        let b = ((255) - (i));
        p.push(r);
        p.push(g);
        p.push(b);
    }
    return pyBytes(p);
}
function run_11_lissajous_particles() {
    let w = 320;
    let h = 240;
    let frames_n = 360;
    let particles = 48;
    let out_path = 'sample/out/11_lissajous_particles.gif';
    let start = perf_counter();
    let frames = [];
    let t;
    for (let __pytra_i_2 = 0; __pytra_i_2 < frames_n; __pytra_i_2 += 1) {
        t = __pytra_i_2;
        let frame = pyBytearray(((w) * (h)));
        let p;
        for (let __pytra_i_3 = 0; __pytra_i_3 < particles; __pytra_i_3 += 1) {
            p = __pytra_i_3;
            let phase = ((p) * (0.261799));
            let x = Math.trunc(Number(((((w) * (0.5))) + (((((w) * (0.38))) * (math.sin(((((0.11) * (t))) + (((phase) * (2.0)))))))))));
            let y = Math.trunc(Number(((((h) * (0.5))) + (((((h) * (0.38))) * (math.sin(((((0.17) * (t))) + (((phase) * (3.0)))))))))));
            let color = ((30) + (pyMod(((p) * (9)), 220)));
            let dy;
            for (let __pytra_i_4 = (-(2)); __pytra_i_4 < 3; __pytra_i_4 += 1) {
                dy = __pytra_i_4;
                let dx;
                for (let __pytra_i_5 = (-(2)); __pytra_i_5 < 3; __pytra_i_5 += 1) {
                    dx = __pytra_i_5;
                    let xx = ((x) + (dx));
                    let yy = ((y) + (dy));
                    if (pyBool((((xx) >= (0)) && ((xx) < (w)) && ((yy) >= (0)) && ((yy) < (h))))) {
                        let d2 = ((((dx) * (dx))) + (((dy) * (dy))));
                        if (pyBool(((d2) <= (4)))) {
                            let idx = ((((yy) * (w))) + (xx));
                            let v = ((color) - (((d2) * (20))));
                            if (pyBool(((v) < (0)))) {
                                v = 0;
                            }
                            if (pyBool(((v) > (frame[idx])))) {
                                frame[idx] = v;
                            }
                        }
                    }
                }
            }
        }
        frames.push(pyBytes(frame));
    }
    save_gif(out_path, w, h, frames, color_palette(), 3, 0);
    let elapsed = ((perf_counter()) - (start));
    pyPrint('output:', out_path);
    pyPrint('frames:', frames_n);
    pyPrint('elapsed_sec:', elapsed);
}
run_11_lissajous_particles();
