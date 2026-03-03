import * as math from "./pytra/std/math.js";
import { perf_counter } from "./pytra/std/time.js";
import { save_gif } from "./pytra/utils/gif.js";

// 11: Sample that outputs Lissajous-motion particles as a GIF.

function color_palette() {
    let p = [];
    for (let i = 0; i < 256; i += 1) {
        let r = i;
        let g = i * 3 % 256;
        let b = 255 - i;
        p.push(r);
        p.push(g);
        p.push(b);
    }
    return (Array.isArray((p)) ? (p).slice() : Array.from((p)));
}

function run_11_lissajous_particles() {
    let w = 320;
    let h = 240;
    let frames_n = 360;
    let particles = 48;
    let out_path = "sample/out/11_lissajous_particles.gif";
    
    let start = perf_counter();
    let frames = [];
    
    for (let t = 0; t < frames_n; t += 1) {
        let frame = (typeof (w * h) === "number" ? new Array(Math.max(0, Math.trunc(Number((w * h))))).fill(0) : (Array.isArray((w * h)) ? (w * h).slice() : Array.from((w * h))));
        let __hoisted_cast_1 = Number(t);
        
        for (let p = 0; p < particles; p += 1) {
            let phase = p * 0.261799;
            let x = Math.trunc(Number(w * 0.5 + w * 0.38 * math.sin(0.11 * __hoisted_cast_1 + phase * 2.0)));
            let y = Math.trunc(Number(h * 0.5 + h * 0.38 * math.sin(0.17 * __hoisted_cast_1 + phase * 3.0)));
            let color = 30 + p * 9 % 220;
            
            for (let dy = -2; dy < 3; dy += 1) {
                for (let dx = -2; dx < 3; dx += 1) {
                    let xx = x + dx;
                    let yy = y + dy;
                    if (xx >= 0 && xx < w && yy >= 0 && yy < h) {
                        let d2 = dx * dx + dy * dy;
                        if (d2 <= 4) {
                            let idx = yy * w + xx;
                            let v = color - d2 * 20;
                            v = Math.max(0, v);
                            if (v > frame[(((idx) < 0) ? ((frame).length + (idx)) : (idx))]) {
                                frame[(((idx) < 0) ? ((frame).length + (idx)) : (idx))] = v;
                            }
                        }
                    }
                }
            }
        }
        frames.push((Array.isArray((frame)) ? (frame).slice() : Array.from((frame))));
    }
    save_gif(out_path, w, h, frames, color_palette());
    let elapsed = perf_counter() - start;
    console.log("output:", out_path);
    console.log("frames:", frames_n);
    console.log("elapsed_sec:", elapsed);
}

run_11_lissajous_particles();
