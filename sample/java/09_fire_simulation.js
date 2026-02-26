import { perf_counter } from "./pytra/std/time.js";
import { save_gif } from "./pytra/runtime/gif.js";

// 09: Sample that outputs a simple fire effect as a GIF.

function fire_palette() {
    let p = [];
    const __start_1 = 0;
    for (let i = __start_1; i < 256; i += 1) {
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
    return (Array.isArray((p)) ? (p).slice() : Array.from((p)));
}

function run_09_fire_simulation() {
    let w = 380;
    let h = 260;
    let steps = 420;
    let out_path = "sample/out/09_fire_simulation.gif";
    
    let start = perf_counter();
    let heat = (() => { let __out = []; for (const _ of (() => { const __out = []; const __start = 0; const __stop = h; const __step = 1; if (__step === 0) { return __out; } if (__step > 0) { for (let __i = __start; __i < __stop; __i += __step) { __out.push(__i); } } else { for (let __i = __start; __i > __stop; __i += __step) { __out.push(__i); } } return __out; })()) { __out.push((() => { const __base = ([0]); const __n = Math.max(0, Math.trunc(Number(w))); let __out = []; for (let __i = 0; __i < __n; __i += 1) { for (const __v of __base) { __out.push(__v); } } return __out; })()); } return __out; })();
    let frames = [];
    
    const __start_2 = 0;
    for (let t = __start_2; t < steps; t += 1) {
        const __start_3 = 0;
        for (let x = __start_3; x < w; x += 1) {
            let val = 170 + (x * 13 + t * 17) % 86;
            heat[(((h - 1) < 0) ? ((heat).length + (h - 1)) : (h - 1))][(((x) < 0) ? ((heat[(((h - 1) < 0) ? ((heat).length + (h - 1)) : (h - 1))]).length + (x)) : (x))] = val;
        }
        const __start_4 = 1;
        for (let y = __start_4; y < h; y += 1) {
            const __start_5 = 0;
            for (let x = __start_5; x < w; x += 1) {
                let a = heat[(((y) < 0) ? ((heat).length + (y)) : (y))][(((x) < 0) ? ((heat[(((y) < 0) ? ((heat).length + (y)) : (y))]).length + (x)) : (x))];
                let b = heat[(((y) < 0) ? ((heat).length + (y)) : (y))][((((x - 1 + w) % w) < 0) ? ((heat[(((y) < 0) ? ((heat).length + (y)) : (y))]).length + ((x - 1 + w) % w)) : ((x - 1 + w) % w))];
                let c = heat[(((y) < 0) ? ((heat).length + (y)) : (y))][((((x + 1) % w) < 0) ? ((heat[(((y) < 0) ? ((heat).length + (y)) : (y))]).length + ((x + 1) % w)) : ((x + 1) % w))];
                let d = heat[((((y + 1) % h) < 0) ? ((heat).length + ((y + 1) % h)) : ((y + 1) % h))][(((x) < 0) ? ((heat[((((y + 1) % h) < 0) ? ((heat).length + ((y + 1) % h)) : ((y + 1) % h))]).length + (x)) : (x))];
                let v = Math.floor((a + b + c + d) / 4);
                let cool = 1 + (x + y + t) % 3;
                let nv = v - cool;
                heat[(((y - 1) < 0) ? ((heat).length + (y - 1)) : (y - 1))][(((x) < 0) ? ((heat[(((y - 1) < 0) ? ((heat).length + (y - 1)) : (y - 1))]).length + (x)) : (x))] = (nv > 0 ? nv : 0);
            }
        }
        let frame = (typeof (w * h) === "number" ? new Array(Math.max(0, Math.trunc(Number((w * h))))).fill(0) : (Array.isArray((w * h)) ? (w * h).slice() : Array.from((w * h))));
        const __start_6 = 0;
        for (let yy = __start_6; yy < h; yy += 1) {
            let row_base = yy * w;
            const __start_7 = 0;
            for (let xx = __start_7; xx < w; xx += 1) {
                frame[(((row_base + xx) < 0) ? ((frame).length + (row_base + xx)) : (row_base + xx))] = heat[(((yy) < 0) ? ((heat).length + (yy)) : (yy))][(((xx) < 0) ? ((heat[(((yy) < 0) ? ((heat).length + (yy)) : (yy))]).length + (xx)) : (xx))];
            }
        }
        frames.push((Array.isArray((frame)) ? (frame).slice() : Array.from((frame))));
    }
    save_gif(out_path, w, h, frames, fire_palette());
    let elapsed = perf_counter() - start;
    console.log("output:", out_path);
    console.log("frames:", steps);
    console.log("elapsed_sec:", elapsed);
}

// __main__ guard
run_09_fire_simulation();
