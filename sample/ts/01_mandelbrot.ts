// このファイルは EAST ベース TypeScript プレビュー出力です。
// TODO: 専用 TSEmitter 実装へ段階移行する。
import { perf_counter } from "./time.js";
import { png } from "./pytra/runtime.js";

// 01: Sample that outputs the Mandelbrot set as a PNG image.
// Syntax is kept straightforward with future transpilation in mind.

function escape_count(cx, cy, max_iter) {
    let x = 0.0;
    let y = 0.0;
    for (let i = 0; i < max_iter; i += 1) {
        let x2 = x * x;
        let y2 = y * y;
        if (x2 + y2 > 4.0) {
            return i;
        }
        y = 2.0 * x * y + cy;
        x = x2 - y2 + cx;
    }
    return max_iter;
}

function color_map(iter_count, max_iter) {
    if (iter_count >= max_iter) {
        return [0, 0, 0];
    }
    let t = iter_count / max_iter;
    let r = Math.trunc(Number(255.0 * t * t));
    let g = Math.trunc(Number(255.0 * t));
    let b = Math.trunc(Number(255.0 * (1.0 - t)));
    return [r, g, b];
}

function render_mandelbrot(width, height, max_iter, x_min, x_max, y_min, y_max) {
    let pixels = bytearray();
    
    for (let y = 0; y < height; y += 1) {
        let py = y_min + (y_max - y_min) * (y / (height - 1));
        
        for (let x = 0; x < width; x += 1) {
            let px = x_min + (x_max - x_min) * (x / (width - 1));
            let it = escape_count(px, py, max_iter);
            let r;
            let g;
            let b;
            if (it >= max_iter) {
                r = 0;
                g = 0;
                b = 0;
            } else {
                let t = it / max_iter;
                r = Math.trunc(Number(255.0 * t * t));
                g = Math.trunc(Number(255.0 * t));
                b = Math.trunc(Number(255.0 * (1.0 - t)));
            }
            pixels.push(r);
            pixels.push(g);
            pixels.push(b);
        }
    }
    return pixels;
}

function run_mandelbrot() {
    let width = 1600;
    let height = 1200;
    let max_iter = 1000;
    let out_path = "sample/out/01_mandelbrot.png";
    
    let start = perf_counter();
    
    let pixels = render_mandelbrot(width, height, max_iter, -2.2, 1.0, -1.2, 1.2);
    png.write_rgb_png(out_path, width, height, pixels);
    
    let elapsed = perf_counter() - start;
    console.log("output:", out_path);
    console.log("size:", width, "x", height);
    console.log("max_iter:", max_iter);
    console.log("elapsed_sec:", elapsed);
}

// __main__ guard
run_mandelbrot();
