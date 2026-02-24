import { perf_counter } from "./time.js";
import { grayscale_palette } from "./pytra/runtime/gif.js";
import { save_gif } from "./pytra/runtime/gif.js";

// 05: Sample that outputs a Mandelbrot zoom as an animated GIF.

function render_frame(width, height, center_x, center_y, scale, max_iter) {
    let frame = bytearray(width * height);
    for (let y = 0; y < height; y += 1) {
        let row_base = y * width;
        let cy = center_y + (y - height * 0.5) * scale;
        for (let x = 0; x < width; x += 1) {
            let cx = center_x + (x - width * 0.5) * scale;
            let zx = 0.0;
            let zy = 0.0;
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
            frame[row_base + x] = Math.trunc(Number(255.0 * i / max_iter));
        }
    }
    return bytes(frame);
}

function run_05_mandelbrot_zoom() {
    let width = 320;
    let height = 240;
    let frame_count = 48;
    let max_iter = 110;
    let center_x = -0.743643887037151;
    let center_y = 0.13182590420533;
    let base_scale = 3.2 / width;
    let zoom_per_frame = 0.93;
    let out_path = "sample/out/05_mandelbrot_zoom.gif";
    
    let start = perf_counter();
    let frames = [];
    let scale = base_scale;
    for (let _ = 0; _ < frame_count; _ += 1) {
        frames.push(render_frame(width, height, center_x, center_y, scale, max_iter));
        scale *= zoom_per_frame;
    }
    save_gif(out_path, width, height, frames, grayscale_palette());
    let elapsed = perf_counter() - start;
    console.log("output:", out_path);
    console.log("frames:", frame_count);
    console.log("elapsed_sec:", elapsed);
}

// __main__ guard
run_05_mandelbrot_zoom();
