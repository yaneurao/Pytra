import * as math from "./pytra/std/math.js";
import { perf_counter } from "./pytra/std/time.js";
import { grayscale_palette } from "./pytra/runtime/gif.js";
import { save_gif } from "./pytra/runtime/gif.js";

// 10: Sample that outputs a plasma effect as a GIF.

function run_10_plasma_effect() {
    let w = 320;
    let h = 240;
    let frames_n = 216;
    let out_path = "sample/out/10_plasma_effect.gif";
    
    let start = perf_counter();
    let frames = [];
    
    const __start_1 = 0;
    for (let t = __start_1; t < frames_n; t += 1) {
        let frame = (typeof (w * h) === "number" ? new Array(Math.max(0, Math.trunc(Number((w * h))))).fill(0) : (Array.isArray((w * h)) ? (w * h).slice() : Array.from((w * h))));
        const __start_2 = 0;
        for (let y = __start_2; y < h; y += 1) {
            let row_base = y * w;
            const __start_3 = 0;
            for (let x = __start_3; x < w; x += 1) {
                let dx = x - 160;
                let dy = y - 120;
                let v = math.sin((x + t * 2.0) * 0.045) + math.sin((y - t * 1.2) * 0.05) + math.sin((x + y + t * 1.7) * 0.03) + math.sin(math.sqrt(dx * dx + dy * dy) * 0.07 - t * 0.18);
                let c = Math.trunc(Number((v + 4.0) * (255.0 / 8.0)));
                if (c < 0) {
                    c = 0;
                }
                if (c > 255) {
                    c = 255;
                }
                frame[(((row_base + x) < 0) ? ((frame).length + (row_base + x)) : (row_base + x))] = c;
            }
        }
        frames.push((Array.isArray((frame)) ? (frame).slice() : Array.from((frame))));
    }
    save_gif(out_path, w, h, frames, grayscale_palette());
    let elapsed = perf_counter() - start;
    console.log("output:", out_path);
    console.log("frames:", frames_n);
    console.log("elapsed_sec:", elapsed);
}

// __main__ guard
run_10_plasma_effect();
