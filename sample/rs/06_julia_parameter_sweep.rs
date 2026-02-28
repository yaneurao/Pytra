mod py_runtime;
pub use crate::py_runtime::{math, pytra, time};
use crate::py_runtime::*;

use crate::time::perf_counter;
use crate::pytra::runtime::gif::save_gif;

// 06: Sample that sweeps Julia-set parameters and outputs a GIF.

fn julia_palette() -> Vec<u8> {
    // Keep index 0 black for points inside the set; build a high-saturation gradient for the rest.
    let mut palette = vec![0u8; (256 * 3) as usize];
    let __idx_i64_1 = ((0) as i64);
    let __idx_2 = if __idx_i64_1 < 0 { (palette.len() as i64 + __idx_i64_1) as usize } else { __idx_i64_1 as usize };
    palette[__idx_2] = ((0) as u8);
    let __idx_i64_3 = ((1) as i64);
    let __idx_4 = if __idx_i64_3 < 0 { (palette.len() as i64 + __idx_i64_3) as usize } else { __idx_i64_3 as usize };
    palette[__idx_4] = ((0) as u8);
    let __idx_i64_5 = ((2) as i64);
    let __idx_6 = if __idx_i64_5 < 0 { (palette.len() as i64 + __idx_i64_5) as usize } else { __idx_i64_5 as usize };
    palette[__idx_6] = ((0) as u8);
    let mut i: i64 = 1;
    while i < 256 {
        let t = (((i - 1)) as f64) / 254.0;
        let r = ((255.0 * 9.0 * (1.0 - t) * t * t * t) as i64);
        let g = ((255.0 * 15.0 * (1.0 - t) * (1.0 - t) * t * t) as i64);
        let b = ((255.0 * 8.5 * (1.0 - t) * (1.0 - t) * (1.0 - t) * t) as i64);
        let __idx_i64_7 = ((i * 3 + 0) as i64);
        let __idx_8 = if __idx_i64_7 < 0 { (palette.len() as i64 + __idx_i64_7) as usize } else { __idx_i64_7 as usize };
        palette[__idx_8] = ((r) as u8);
        let __idx_i64_9 = ((i * 3 + 1) as i64);
        let __idx_10 = if __idx_i64_9 < 0 { (palette.len() as i64 + __idx_i64_9) as usize } else { __idx_i64_9 as usize };
        palette[__idx_10] = ((g) as u8);
        let __idx_i64_11 = ((i * 3 + 2) as i64);
        let __idx_12 = if __idx_i64_11 < 0 { (palette.len() as i64 + __idx_i64_11) as usize } else { __idx_i64_11 as usize };
        palette[__idx_12] = ((b) as u8);
        i += 1;
    }
    return (palette).clone();
}

fn render_frame(width: i64, height: i64, cr: f64, ci: f64, max_iter: i64, phase: i64) -> Vec<u8> {
    let mut frame = vec![0u8; (width * height) as usize];
    let __hoisted_cast_1: f64 = ((height - 1) as f64);
    let __hoisted_cast_2: f64 = ((width - 1) as f64);
    let mut y: i64 = 0;
    while y < height {
        let row_base = y * width;
        let zy0 = -1.2 + 2.4 * (((y) as f64) / __hoisted_cast_1);
        let mut x: i64 = 0;
        while x < width {
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
                let __idx_i64_13 = ((row_base + x) as i64);
                let __idx_14 = if __idx_i64_13 < 0 { (frame.len() as i64 + __idx_i64_13) as usize } else { __idx_i64_13 as usize };
                frame[__idx_14] = ((0) as u8);
            } else {
                // Add a small frame phase so colors flow smoothly.
                let color_index = 1 + (i * 224 / max_iter + phase) % 255;
                let __idx_i64_15 = ((row_base + x) as i64);
                let __idx_16 = if __idx_i64_15 < 0 { (frame.len() as i64 + __idx_i64_15) as usize } else { __idx_i64_15 as usize };
                frame[__idx_16] = ((color_index) as u8);
            }
            x += 1;
        }
        y += 1;
    }
    return (frame).clone();
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
    let mut i: i64 = 0;
    while i < frames_n {
        let t = (((i + start_offset) % frames_n) as f64) / __hoisted_cast_3;
        let angle = 2.0 * math::pi * t;
        let cr = center_cr + radius_cr * math::cos(angle);
        let ci = center_ci + radius_ci * math::sin(angle);
        let phase = (phase_offset + i * 5) % 255;
        frames.push(render_frame(width, height, cr, ci, max_iter, phase));
        i += 1;
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
