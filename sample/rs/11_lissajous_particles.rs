mod py_runtime;
pub use crate::py_runtime::{math, pytra, time};
use crate::py_runtime::*;

use crate::time::perf_counter;
use crate::pytra::runtime::gif::save_gif;

// 11: Sample that outputs Lissajous-motion particles as a GIF.

fn color_palette() -> Vec<u8> {
    let mut p = Vec::<u8>::new();
    let mut i: i64 = 0;
    while i < 256 {
        let r = i;
        let g = i * 3 % 256;
        let b = 255 - i;
        p.push(((r) as u8));
        p.push(((g) as u8));
        p.push(((b) as u8));
        i += 1;
    }
    return (p).clone();
}

fn run_11_lissajous_particles() {
    let w = 320;
    let h = 240;
    let frames_n = 360;
    let particles = 48;
    let out_path = ("sample/out/11_lissajous_particles.gif").to_string();
    
    let start = perf_counter();
    let mut frames: Vec<Vec<u8>> = vec![];
    
    let mut t: i64 = 0;
    while t < frames_n {
        let mut frame = vec![0u8; (w * h) as usize];
        let __hoisted_cast_1: f64 = ((t) as f64);
        
        let mut p: i64 = 0;
        while p < particles {
            let phase = ((p) as f64) * 0.261799;
            let x = ((((w) as f64) * 0.5 + ((w) as f64) * 0.38 * math::sin(0.11 * __hoisted_cast_1 + phase * 2.0)) as i64);
            let y = ((((h) as f64) * 0.5 + ((h) as f64) * 0.38 * math::sin(0.17 * __hoisted_cast_1 + phase * 3.0)) as i64);
            let color = 30 + p * 9 % 220;
            
            let mut dy: i64 = -2;
            while dy < 3 {
                let mut dx: i64 = -2;
                while dx < 3 {
                    let xx = x + dx;
                    let yy = y + dy;
                    if (xx >= 0) && (xx < w) && (yy >= 0) && (yy < h) {
                        let d2 = dx * dx + dy * dy;
                        if d2 <= 4 {
                            let idx = yy * w + xx;
                            let mut v = color - d2 * 20;
                            v = py_any_to_i64(&(if 0 > v { 0 } else { v }));
                            if v > ((frame[((if ((idx) as i64) < 0 { (frame.len() as i64 + ((idx) as i64)) } else { ((idx) as i64) }) as usize)]) as i64) {
                                let __idx_i64_1 = ((idx) as i64);
                                let __idx_2 = if __idx_i64_1 < 0 { (frame.len() as i64 + __idx_i64_1) as usize } else { __idx_i64_1 as usize };
                                frame[__idx_2] = ((py_any_to_i64(&v)) as u8);
                            }
                        }
                    }
                    dx += 1;
                }
                dy += 1;
            }
            p += 1;
        }
        frames.push((frame).clone());
        t += 1;
    }
    save_gif(&(out_path), w, h, &(frames), &(color_palette()), 3, 0);
    let elapsed = perf_counter() - start;
    println!("{} {}", ("output:").to_string(), out_path);
    println!("{} {}", ("frames:").to_string(), frames_n);
    println!("{} {}", ("elapsed_sec:").to_string(), elapsed);
}

fn main() {
    run_11_lissajous_particles();
}
