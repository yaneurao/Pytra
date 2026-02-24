import { perf_counter } from "./time.js";
import { save_gif } from "./pytra/runtime/gif.js";

// 09: Sample that outputs a simple fire effect as a GIF.

function fire_palette() {
    let p = bytearray();
    for (let i = 0; i < 256; i += 1) {
        let r = 0;
        let g = 0;
        let b = 0;
        if (i < 85) {
            r = i * 3;
            g = 0;
            b = 0;
        } else {
            if (i < 170) {
                r = 255;
                g = (i - 85) * 3;
                b = 0;
            } else {
                r = 255;
                g = 255;
                b = (i - 170) * 3;
            }
        }
        p.push(r);
        p.push(g);
        p.push(b);
    }
    return bytes(p);
}

function run_09_fire_simulation() {
    let w = 380;
    let h = 260;
    let steps = 420;
    let out_path = "sample/out/09_fire_simulation.gif";
    
    let start = perf_counter();
    let heat = [[0] * w for _ in range(h)];
    let frames = [];
    
    for (let t = 0; t < steps; t += 1) {
        for (let x = 0; x < w; x += 1) {
            let val = 170 + (x * 13 + t * 17) % 86;
            heat[h - 1][x] = val;
        }
        for (let y = 1; y < h; y += 1) {
            for (let x = 0; x < w; x += 1) {
                let a = heat[y][x];
                let b = heat[y][(x - 1 + w) % w];
                let c = heat[y][(x + 1) % w];
                let d = heat[(y + 1) % h][x];
                let v = Math.floor((a + b + c + d) / 4);
                let cool = 1 + (x + y + t) % 3;
                let nv = v - cool;
                heat[y - 1][x] = (nv > 0 ? nv : 0);
            }
        }
        let frame = bytearray(w * h);
        for (let yy = 0; yy < h; yy += 1) {
            let row_base = yy * w;
            for (let xx = 0; xx < w; xx += 1) {
                frame[row_base + xx] = heat[yy][xx];
            }
        }
        frames.push(bytes(frame));
    }
    save_gif(out_path, w, h, frames, fire_palette());
    let elapsed = perf_counter() - start;
    console.log("output:", out_path);
    console.log("frames:", steps);
    console.log("elapsed_sec:", elapsed);
}

// __main__ guard
run_09_fire_simulation();
