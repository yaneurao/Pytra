import * as math from "./math.js";
import { perf_counter } from "./time.js";
import { save_gif } from "./pytra/runtime/gif.js";

// 06: Sample that sweeps Julia-set parameters and outputs a GIF.

function julia_palette() {
    // Keep index 0 black for points inside the set; build a high-saturation gradient for the rest.
    let palette = bytearray(256 * 3);
    palette[0] = 0;
    palette[1] = 0;
    palette[2] = 0;
    for (let i = 1; i < 256; i += 1) {
        let t = (i - 1) / 254.0;
        let r = Math.trunc(Number(255.0 * 9.0 * (1.0 - t) * t * t * t));
        let g = Math.trunc(Number(255.0 * 15.0 * (1.0 - t) * (1.0 - t) * t * t));
        let b = Math.trunc(Number(255.0 * 8.5 * (1.0 - t) * (1.0 - t) * (1.0 - t) * t));
        palette[i * 3 + 0] = r;
        palette[i * 3 + 1] = g;
        palette[i * 3 + 2] = b;
    }
    return bytes(palette);
}

function render_frame(width, height, cr, ci, max_iter, phase) {
    let frame = bytearray(width * height);
    for (let y = 0; y < height; y += 1) {
        let row_base = y * width;
        let zy0 = -1.2 + 2.4 * (y / (height - 1));
        for (let x = 0; x < width; x += 1) {
            let zx = -1.8 + 3.6 * (x / (width - 1));
            let zy = zy0;
            let i = 0;
            while (i < max_iter) {
                let zx2 = zx * zx;
                let zy2 = zy * zy;
                if (zx2 + zy2 > 4.0) {
                    py_break;
                }
                zy = 2.0 * zx * zy + ci;
                zx = zx2 - zy2 + cr;
                i += 1;
            }
            if (i >= max_iter) {
                frame[row_base + x] = 0;
            } else {
                // Add a small frame phase so colors flow smoothly.
                let color_index = 1 + (Math.floor(i * 224 / max_iter) + phase) % 255;
                frame[row_base + x] = color_index;
            }
        }
    }
    return bytes(frame);
}

function run_06_julia_parameter_sweep() {
    let width = 320;
    let height = 240;
    let frames_n = 72;
    let max_iter = 180;
    let out_path = "sample/out/06_julia_parameter_sweep.gif";
    
    let start = perf_counter();
    let frames = [];
    // Orbit an ellipse around a known visually good region to reduce flat blown highlights.
    let center_cr = -0.745;
    let center_ci = 0.186;
    let radius_cr = 0.12;
    let radius_ci = 0.10;
    // Add start and phase offsets so GitHub thumbnails do not appear too dark.
    // Tune it to start in a red-leaning color range.
    let start_offset = 20;
    let phase_offset = 180;
    for (let i = 0; i < frames_n; i += 1) {
        let t = (i + start_offset) % frames_n / frames_n;
        let angle = 2.0 * math.pi * t;
        let cr = center_cr + radius_cr * math.cos(angle);
        let ci = center_ci + radius_ci * math.sin(angle);
        let phase = (phase_offset + i * 5) % 255;
        frames.push(render_frame(width, height, cr, ci, max_iter, phase));
    }
    save_gif(out_path, width, height, frames, julia_palette());
    let elapsed = perf_counter() - start;
    console.log("output:", out_path);
    console.log("frames:", frames_n);
    console.log("elapsed_sec:", elapsed);
}

// __main__ guard
run_06_julia_parameter_sweep();
