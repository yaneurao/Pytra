import * as math from "./pytra/std/math.js";
import { perf_counter } from "./pytra/std/time.js";
import { save_gif } from "./pytra/runtime/gif.js";

// 14: Sample that outputs a moving-light scene in a simple raymarching style as a GIF.

function palette() {
    let p = [];
    const __start_1 = 0;
    for (let i = __start_1; i < 256; i += 1) {
        let r = Math.min(255, Math.trunc(Number(20 + i * 0.9)));
        let g = Math.min(255, Math.trunc(Number(10 + i * 0.7)));
        let b = Math.min(255, 30 + i);
        p.push(r);
        p.push(g);
        p.push(b);
    }
    return (Array.isArray((p)) ? (p).slice() : Array.from((p)));
}

function scene(x, y, light_x, light_y) {
    let x1 = x + 0.45;
    let y1 = y + 0.2;
    let x2 = x - 0.35;
    let y2 = y - 0.15;
    let r1 = math.sqrt(x1 * x1 + y1 * y1);
    let r2 = math.sqrt(x2 * x2 + y2 * y2);
    let blob = math.exp(-7.0 * r1 * r1) + math.exp(-8.0 * r2 * r2);
    
    let lx = x - light_x;
    let ly = y - light_y;
    let l = math.sqrt(lx * lx + ly * ly);
    let lit = 1.0 / (1.0 + 3.5 * l * l);
    
    let v = Math.trunc(Number(255.0 * blob * lit * 5.0));
    return Math.min(255, Math.max(0, v));
}

function run_14_raymarching_light_cycle() {
    let w = 320;
    let h = 240;
    let frames_n = 84;
    let out_path = "sample/out/14_raymarching_light_cycle.gif";
    
    let start = perf_counter();
    let frames = [];
    let __hoisted_cast_1 = Number(frames_n);
    let __hoisted_cast_2 = Number(h - 1);
    let __hoisted_cast_3 = Number(w - 1);
    
    const __start_2 = 0;
    for (let t = __start_2; t < frames_n; t += 1) {
        let frame = (typeof (w * h) === "number" ? new Array(Math.max(0, Math.trunc(Number((w * h))))).fill(0) : (Array.isArray((w * h)) ? (w * h).slice() : Array.from((w * h))));
        let a = (t / __hoisted_cast_1) * math.pi * 2.0;
        let light_x = 0.75 * math.cos(a);
        let light_y = 0.55 * math.sin(a * 1.2);
        
        const __start_3 = 0;
        for (let y = __start_3; y < h; y += 1) {
            let row_base = y * w;
            let py = (y / __hoisted_cast_2) * 2.0 - 1.0;
            const __start_4 = 0;
            for (let x = __start_4; x < w; x += 1) {
                let px = (x / __hoisted_cast_3) * 2.0 - 1.0;
                frame[(((row_base + x) < 0) ? ((frame).length + (row_base + x)) : (row_base + x))] = scene(px, py, light_x, light_y);
            }
        }
        frames.push((Array.isArray((frame)) ? (frame).slice() : Array.from((frame))));
    }
    save_gif(out_path, w, h, frames, palette());
    let elapsed = perf_counter() - start;
    console.log("output:", out_path);
    console.log("frames:", frames_n);
    console.log("elapsed_sec:", elapsed);
}

run_14_raymarching_light_cycle();
