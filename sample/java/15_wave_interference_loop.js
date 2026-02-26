import * as math from "./pytra/std/math.js";
import { perf_counter } from "./pytra/std/time.js";
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
    
    const __start_1 = 0;
    for (let t = __start_1; t < frames_n; t += 1) {
        let frame = (typeof (w * h) === "number" ? new Array(Math.max(0, Math.trunc(Number((w * h))))).fill(0) : (Array.isArray((w * h)) ? (w * h).slice() : Array.from((w * h))));
        let phase = t * 0.12;
        const __start_2 = 0;
        for (let y = __start_2; y < h; y += 1) {
            let row_base = y * w;
            const __start_3 = 0;
            for (let x = __start_3; x < w; x += 1) {
                let dx = x - 160;
                let dy = y - 120;
                let v = math.sin((x + t * 1.5) * 0.045) + math.sin((y - t * 1.2) * 0.04) + math.sin((x + y) * 0.02 + phase) + math.sin(math.sqrt(dx * dx + dy * dy) * 0.08 - phase * 1.3);
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
run_15_wave_interference_loop();
