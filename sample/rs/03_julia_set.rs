mod py_runtime;
pub use crate::py_runtime::{math, pytra, time};
use crate::py_runtime::*;

use crate::time::perf_counter;
use crate::pytra::runtime::png;

// 03: Sample that outputs a Julia set as a PNG image.
// Implemented with simple loop-centric logic for transpilation compatibility.

fn render_julia(width: i64, height: i64, max_iter: i64, cx: f64, cy: f64) -> Vec<u8> {
    let mut pixels: Vec<u8> = Vec::<u8>::with_capacity(((((width) * (height)) * 3)) as usize);
    let __hoisted_cast_1: f64 = ((height - 1) as f64);
    let __hoisted_cast_2: f64 = ((width - 1) as f64);
    let __hoisted_cast_3: f64 = ((max_iter) as f64);
    
    let mut y: i64 = 0;
    while y < height {
        let zy0: f64 = -1.2 + 2.4 * (((y) as f64) / __hoisted_cast_1);
        
        let mut x: i64 = 0;
        while x < width {
            let mut zx: f64 = -1.8 + 3.6 * (((x) as f64) / __hoisted_cast_2);
            let mut zy: f64 = zy0;
            
            let mut i: i64 = 0;
            while i < max_iter {
                let zx2: f64 = zx * zx;
                let zy2: f64 = zy * zy;
                if zx2 + zy2 > 4.0 {
                    break;
                }
                zy = 2.0 * zx * zy + cy;
                zx = zx2 - zy2 + cx;
                i += 1;
            }
            let mut r: i64 = 0;
            let mut g: i64 = 0;
            let mut b: i64 = 0;
            if i >= max_iter {
                r = 0;
                g = 0;
                b = 0;
            } else {
                let t: f64 = ((i) as f64) / __hoisted_cast_3;
                r = ((255.0 * (0.2 + 0.8 * t)) as i64);
                g = ((255.0 * (0.1 + 0.9 * t * t)) as i64);
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

fn run_julia() {
    let width: i64 = 3840;
    let height: i64 = 2160;
    let max_iter: i64 = 20000;
    let out_path: String = ("sample/out/03_julia_set.png").to_string();
    
    let start: f64 = perf_counter();
    let pixels: Vec<u8> = render_julia(width, height, max_iter, -0.8, 0.156);
    pytra::runtime::png::write_rgb_png(&(out_path), width, height, &(pixels));
    let elapsed: f64 = perf_counter() - start;
    
    println!("{} {}", ("output:").to_string(), out_path);
    println!("{} {} {} {}", ("size:").to_string(), width, ("x").to_string(), height);
    println!("{} {}", ("max_iter:").to_string(), max_iter);
    println!("{} {}", ("elapsed_sec:").to_string(), elapsed);
}

fn main() {
    run_julia();
}
