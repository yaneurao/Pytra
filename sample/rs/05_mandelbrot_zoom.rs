mod py_runtime;
pub use crate::py_runtime::{math, pytra, time};
use crate::py_runtime::*;

use crate::time::perf_counter;
use crate::pytra::runtime::gif::grayscale_palette;
use crate::pytra::runtime::gif::save_gif;

// 05: Sample that outputs a Mandelbrot zoom as an animated GIF.

fn render_frame(width: i64, height: i64, center_x: f64, center_y: f64, scale: f64, max_iter: i64) -> Vec<u8> {
    let mut frame = vec![0u8; (width * height) as usize];
    let __hoisted_cast_1: f64 = ((max_iter) as f64);
    let mut y: i64 = 0;
    while y < height {
        let row_base = y * width;
        let cy = center_y + (((y) as f64) - ((height) as f64) * 0.5) * scale;
        let mut x: i64 = 0;
        while x < width {
            let cx = center_x + (((x) as f64) - ((width) as f64) * 0.5) * scale;
            let mut zx = 0.0;
            let mut zy = 0.0;
            let mut i = 0;
            while i < max_iter {
                let zx2 = zx * zx;
                let zy2 = zy * zy;
                if zx2 + zy2 > 4.0 {
                    break;
                }
                zy = 2.0 * zx * zy + cy;
                zx = zx2 - zy2 + cx;
                i += 1;
            }
            let __idx_i64_1 = ((row_base + x) as i64);
            let __idx_2 = if __idx_i64_1 < 0 { (frame.len() as i64 + __idx_i64_1) as usize } else { __idx_i64_1 as usize };
            frame[__idx_2] = ((((255.0 * ((i) as f64) / __hoisted_cast_1) as i64)) as u8);
            x += 1;
        }
        y += 1;
    }
    return (frame).clone();
}

fn run_05_mandelbrot_zoom() {
    let width = 320;
    let height = 240;
    let frame_count = 48;
    let max_iter = 110;
    let center_x = -0.743643887037151;
    let center_y = 0.13182590420533;
    let base_scale = 3.2 / ((width) as f64);
    let zoom_per_frame = 0.93;
    let out_path = ("sample/out/05_mandelbrot_zoom.gif").to_string();
    
    let start = perf_counter();
    let mut frames: Vec<Vec<u8>> = vec![];
    let mut scale = base_scale;
    let mut py_underscore: i64 = 0;
    while py_underscore < frame_count {
        frames.push(render_frame(width, height, center_x, center_y, scale, max_iter));
        scale *= zoom_per_frame;
        py_underscore += 1;
    }
    save_gif(&(out_path), width, height, &(frames), &(grayscale_palette()), 5, 0);
    let elapsed = perf_counter() - start;
    println!("{} {}", ("output:").to_string(), out_path);
    println!("{} {}", ("frames:").to_string(), frame_count);
    println!("{} {}", ("elapsed_sec:").to_string(), elapsed);
}

fn main() {
    run_05_mandelbrot_zoom();
}
