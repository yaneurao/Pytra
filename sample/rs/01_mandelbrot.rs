mod py_runtime;
pub use crate::py_runtime::{math, pytra, time};
use crate::py_runtime::*;

use crate::time::perf_counter;
use crate::pytra::runtime::png;

// 01: Sample that outputs the Mandelbrot set as a PNG image.
// Syntax is kept straightforward with future transpilation in mind.

fn escape_count(cx: f64, cy: f64, max_iter: i64) -> i64 {
    let mut x: f64 = 0.0;
    let mut y: f64 = 0.0;
    let mut i: i64 = 0;
    while i < max_iter {
        let x2: f64 = x * x;
        let y2: f64 = y * y;
        if x2 + y2 > 4.0 {
            return i;
        }
        y = 2.0 * x * y + cy;
        x = x2 - y2 + cx;
        i += 1;
    }
    return max_iter;
}

fn color_map(iter_count: i64, max_iter: i64) -> (i64, i64, i64) {
    if iter_count >= max_iter {
        return (0, 0, 0);
    }
    let t: f64 = ((iter_count) as f64) / ((max_iter) as f64);
    let r: i64 = ((255.0 * t * t) as i64);
    let g: i64 = ((255.0 * t) as i64);
    let b: i64 = ((255.0 * (1.0 - t)) as i64);
    return (r, g, b);
}

fn render_mandelbrot(width: i64, height: i64, max_iter: i64, x_min: f64, x_max: f64, y_min: f64, y_max: f64) -> Vec<u8> {
    let mut pixels: Vec<u8> = Vec::<u8>::with_capacity(((((width) * (height)) * 3)) as usize);
    let __hoisted_cast_1: f64 = ((height - 1) as f64);
    let __hoisted_cast_2: f64 = ((width - 1) as f64);
    let __hoisted_cast_3: f64 = ((max_iter) as f64);
    
    let mut y: i64 = 0;
    while y < height {
        let py: f64 = y_min + (y_max - y_min) * (((y) as f64) / __hoisted_cast_1);
        
        let mut x: i64 = 0;
        while x < width {
            let px: f64 = x_min + (x_max - x_min) * (((x) as f64) / __hoisted_cast_2);
            let it: i64 = escape_count(px, py, max_iter);
            let mut r: i64;
            let mut g: i64;
            let mut b: i64;
            if it >= max_iter {
                r = 0;
                g = 0;
                b = 0;
            } else {
                let t: f64 = ((it) as f64) / __hoisted_cast_3;
                r = ((255.0 * t * t) as i64);
                g = ((255.0 * t) as i64);
                b = ((255.0 * (1.0 - t)) as i64);
            }
            pixels.push(((r) as u8));
            pixels.push(((g) as u8));
            pixels.push(((b) as u8));
            x += 1;
        }
        y += 1;
    }
    return pixels;
}

fn run_mandelbrot() {
    let width: i64 = 1600;
    let height: i64 = 1200;
    let max_iter: i64 = 1000;
    let out_path: String = ("sample/out/01_mandelbrot.png").to_string();
    
    let start: f64 = perf_counter();
    
    let pixels: Vec<u8> = render_mandelbrot(width, height, max_iter, -2.2, 1.0, -1.2, 1.2);
    pytra::runtime::png::write_rgb_png(&(out_path), width, height, &(pixels));
    
    let elapsed: f64 = perf_counter() - start;
    println!("{} {}", ("output:").to_string(), out_path);
    println!("{} {} {} {}", ("size:").to_string(), width, ("x").to_string(), height);
    println!("{} {}", ("max_iter:").to_string(), max_iter);
    println!("{} {}", ("elapsed_sec:").to_string(), elapsed);
}

fn main() {
    run_mandelbrot();
}
