// このファイルは EAST ベース TypeScript プレビュー出力です。
// TODO: 専用 TSEmitter 実装へ段階移行する。
import * as math from "./math.js";
import { perf_counter } from "./time.js";
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
    
    for (let t = 0; t < frames_n; t += 1) {
        let frame = bytearray(w * h);
        for (let y = 0; y < h; y += 1) {
            let row_base = y * w;
            for (let x = 0; x < w; x += 1) {
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
                frame[row_base + x] = c;
            }
        }
        frames.push(bytes(frame));
    }
    save_gif(out_path, w, h, frames, grayscale_palette());
    let elapsed = perf_counter() - start;
    console.log("output:", out_path);
    console.log("frames:", frames_n);
    console.log("elapsed_sec:", elapsed);
}

// __main__ guard
run_10_plasma_effect();
