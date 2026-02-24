import { perf_counter } from "./time.js";
import { png } from "./pytra/runtime.js";

// 03: Sample that outputs a Julia set as a PNG image.
// Implemented with simple loop-centric logic for transpilation compatibility.

function render_julia(width, height, max_iter, cx, cy) {
    let pixels = bytearray();
    
    for (let y = 0; y < height; y += 1) {
        let zy0 = -1.2 + 2.4 * (y / (height - 1));
        
        for (let x = 0; x < width; x += 1) {
            let zx = -1.8 + 3.6 * (x / (width - 1));
            let zy = zy0;
            
            let i = 0;
            while (i < max_iter) {
                let zx2 = zx * zx;
                let zy2 = zy * zy;
                if (zx2 + zy2 > 4.0) {
                    break;
                }
                zy = 2.0 * zx * zy + cy;
                zx = zx2 - zy2 + cx;
                i += 1;
            }
            let r = 0;
            let g = 0;
            let b = 0;
            if (i >= max_iter) {
                r = 0;
                g = 0;
                b = 0;
            } else {
                let t = i / max_iter;
                r = Math.trunc(Number(255.0 * (0.2 + 0.8 * t)));
                g = Math.trunc(Number(255.0 * (0.1 + 0.9 * t * t)));
                b = Math.trunc(Number(255.0 * (1.0 - t)));
            }
            pixels.push(r);
            pixels.push(g);
            pixels.push(b);
        }
    }
    return pixels;
}

function run_julia() {
    let width = 3840;
    let height = 2160;
    let max_iter = 20000;
    let out_path = "sample/out/03_julia_set.png";
    
    let start = perf_counter();
    let pixels = render_julia(width, height, max_iter, -0.8, 0.156);
    png.write_rgb_png(out_path, width, height, pixels);
    let elapsed = perf_counter() - start;
    
    console.log("output:", out_path);
    console.log("size:", width, "x", height);
    console.log("max_iter:", max_iter);
    console.log("elapsed_sec:", elapsed);
}

// __main__ guard
run_julia();
