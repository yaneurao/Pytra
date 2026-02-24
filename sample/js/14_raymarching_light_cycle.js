import * as math from "./math.js";
import { perf_counter } from "./time.js";
import { save_gif } from "./pytra/runtime/gif.js";

// 14: Sample that outputs a moving-light scene in a simple raymarching style as a GIF.

function palette() {
    let p = bytearray();
    for (let i = 0; i < 256; i += 1) {
        let r = min(255, Math.trunc(Number(20 + i * 0.9)));
        let g = min(255, Math.trunc(Number(10 + i * 0.7)));
        let b = min(255, Math.trunc(Number(30 + i)));
        p.push(r);
        p.push(g);
        p.push(b);
    }
    return bytes(p);
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
    return min(255, max(0, v));
}

function run_14_raymarching_light_cycle() {
    let w = 320;
    let h = 240;
    let frames_n = 84;
    let out_path = "sample/out/14_raymarching_light_cycle.gif";
    
    let start = perf_counter();
    let frames = [];
    
    for (let t = 0; t < frames_n; t += 1) {
        let frame = bytearray(w * h);
        let a = (t / frames_n) * math.pi * 2.0;
        let light_x = 0.75 * math.cos(a);
        let light_y = 0.55 * math.sin(a * 1.2);
        
        for (let y = 0; y < h; y += 1) {
            let row_base = y * w;
            let py = (y / (h - 1)) * 2.0 - 1.0;
            for (let x = 0; x < w; x += 1) {
                let px = (x / (w - 1)) * 2.0 - 1.0;
                frame[row_base + x] = scene(px, py, light_x, light_y);
            }
        }
        frames.push(bytes(frame));
    }
    save_gif(out_path, w, h, frames, palette());
    let elapsed = perf_counter() - start;
    console.log("output:", out_path);
    console.log("frames:", frames_n);
    console.log("elapsed_sec:", elapsed);
}

// __main__ guard
run_14_raymarching_light_cycle();
