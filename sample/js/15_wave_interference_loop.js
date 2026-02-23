const __pytra_root = process.cwd();
const py_runtime = require(__pytra_root + '/src/js_module/py_runtime.js');
const { PYTRA_TYPE_ID, PY_TYPE_BOOL, PY_TYPE_NUMBER, PY_TYPE_STRING, PY_TYPE_ARRAY, PY_TYPE_MAP, PY_TYPE_SET, PY_TYPE_OBJECT, pyRegisterClassType, pyIsInstance } = py_runtime;

import * as math from "./math.js";
import { perf_counter } from "./time.js";
import { grayscale_palette } from "./pytra/utils/gif.js";
import { save_gif } from "./pytra/utils/gif.js";

// 15: Sample that renders wave interference animation and writes a GIF.

function run_15_wave_interference_loop() {
    let w = 320;
    let h = 240;
    let frames_n = 96;
    let out_path = "sample/out/15_wave_interference_loop.gif";
    
    let start = perf_counter();
    let frames = [];
    
    for (let t = 0; t < frames_n; t += 1) {
        let frame = bytearray((w * h));
        let phase = (t * 0.12);
        for (let y = 0; y < h; y += 1) {
            let row_base = (y * w);
            for (let x = 0; x < w; x += 1) {
                let dx = (x - 160);
                let dy = (y - 120);
                let v = (((math.sin((((x + (t * 1.5))) * 0.045)) + math.sin((((y - (t * 1.2))) * 0.04))) + math.sin(((((x + y)) * 0.02) + phase))) + math.sin(((math.sqrt(((dx * dx) + (dy * dy))) * 0.08) - (phase * 1.3))));
                let c = Math.trunc(Number((((v + 4.0)) * ((255.0 / 8.0)))));
                if (c < 0) {
                    c = 0;
                }
                if (c > 255) {
                    c = 255;
                }
                frame[(row_base + x)] = c;
            }
        }
        frames.push(bytes(frame));
    }
    save_gif(out_path, w, h, frames, grayscale_palette());
    let elapsed = (perf_counter() - start);
    console.log("output:", out_path);
    console.log("frames:", frames_n);
    console.log("elapsed_sec:", elapsed);
}

// __main__ guard
run_15_wave_interference_loop();
