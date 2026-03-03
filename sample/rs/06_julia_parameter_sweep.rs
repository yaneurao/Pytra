mod py_runtime;
pub use crate::py_runtime::{math, pytra, time};
use crate::py_runtime::*;

use crate::time::perf_counter;
use crate::pytra::utils::gif::save_gif;

// 06: Sample that sweeps Julia-set parameters and outputs a GIF.

fn julia_palette() -> Vec<u8> {
    // Keep index 0 black for points inside the set; build a high-saturation gradient for the rest.
    let mut palette = vec![0u8; (256 * 3) as usize];
    let __idx_1 = ((0) as usize);
    palette[__idx_1] = ((0) as u8);
    let __idx_2 = ((1) as usize);
    palette[__idx_2] = ((0) as u8);
    let __idx_3 = ((2) as usize);
    palette[__idx_3] = ((0) as u8);
    for i in (1)..(256) {
            let t = (((i - 1)) as f64) / 254.0;
            let r = ((255.0 * 9.0 * (1.0 - t) * t * t * t) as i64);
            let g = ((255.0 * 15.0 * (1.0 - t) * (1.0 - t) * t * t) as i64);
            let b = ((255.0 * 8.5 * (1.0 - t) * (1.0 - t) * (1.0 - t) * t) as i64);
            let __idx_4 = ((i * 3 + 0) as usize);
            palette[__idx_4] = ((r) as u8);
            let __idx_5 = ((i * 3 + 1) as usize);
            palette[__idx_5] = ((g) as u8);
            let __idx_6 = ((i * 3 + 2) as usize);
            palette[__idx_6] = ((b) as u8);
    }
    return palette;
}

fn render_frame(width: i64, height: i64, cr: f64, ci: f64, max_iter: i64, phase: i64) -> Vec<u8> {
    let mut frame = vec![0u8; (width * height) as usize];
    let __hoisted_cast_1: f64 = ((height - 1) as f64);
    let __hoisted_cast_2: f64 = ((width - 1) as f64);
    for y in (0)..(height) {
            let row_base = y * width;
            let zy0 = -1.2 + 2.4 * (((y) as f64) / __hoisted_cast_1);
            for x in (0)..(width) {
                    let mut zx = -1.8 + 3.6 * (((x) as f64) / __hoisted_cast_2);
                    let mut zy = zy0;
                    let mut i = 0;
                    while i < max_iter {
                        let zx2 = zx * zx;
                        let zy2 = zy * zy;
                        if zx2 + zy2 > 4.0 {
                            break;
                        }
                        zy = 2.0 * zx * zy + ci;
                        zx = zx2 - zy2 + cr;
                        i += 1;
                    }
                    if i >= max_iter {
                        let __idx_i64_10 = ((row_base + x) as i64);
                        let __idx_9 = if __idx_i64_10 < 0 { (frame.len() as i64 + __idx_i64_10) as usize } else { __idx_i64_10 as usize };
                        frame[__idx_9] = ((0) as u8);
                    } else {
                        // Add a small frame phase so colors flow smoothly.
                        let color_index = 1 + (i * 224 / max_iter + phase) % 255;
                        let __idx_i64_12 = ((row_base + x) as i64);
                        let __idx_11 = if __idx_i64_12 < 0 { (frame.len() as i64 + __idx_i64_12) as usize } else { __idx_i64_12 as usize };
                        frame[__idx_11] = ((color_index) as u8);
                    }
            }
    }
    return frame;
}

fn run_06_julia_parameter_sweep() {
    let width = 320;
    let height = 240;
    let frames_n = 72;
    let max_iter = 180;
    let out_path = ("sample/out/06_julia_parameter_sweep.gif").to_string();
    
    let start = perf_counter();
    let mut frames: Vec<Vec<u8>> = vec![];
    // Orbit an ellipse around a known visually good region to reduce flat blown highlights.
    let center_cr = -0.745;
    let center_ci = 0.186;
    let radius_cr = 0.12;
    let radius_ci = 0.10;
    // Add start and phase offsets so GitHub thumbnails do not appear too dark.
    // Tune it to start in a red-leaning color range.
    let start_offset = 20;
    let phase_offset = 180;
    let __hoisted_cast_3: f64 = ((frames_n) as f64);
    for i in (0)..(frames_n) {
            let t = (((i + start_offset) % frames_n) as f64) / __hoisted_cast_3;
            let angle = 2.0 * math::pi * t;
            let cr = center_cr + radius_cr * math::cos(angle);
            let ci = center_ci + radius_ci * math::sin(angle);
            let phase = (phase_offset + i * 5) % 255;
            frames.push(render_frame(width, height, cr, ci, max_iter, phase));
    }
    save_gif(&(out_path), width, height, &(frames), &(julia_palette()), 8, 0);
    let elapsed = perf_counter() - start;
    println!("{} {}", ("output:").to_string(), out_path);
    println!("{} {}", ("frames:").to_string(), frames_n);
    println!("{} {}", ("elapsed_sec:").to_string(), elapsed);
}

fn main() {
    run_06_julia_parameter_sweep();
}
