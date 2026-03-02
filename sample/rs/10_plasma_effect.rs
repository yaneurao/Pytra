mod py_runtime;
pub use crate::py_runtime::{math, pytra, time};
use crate::py_runtime::*;

use crate::time::perf_counter;
use crate::pytra::runtime::gif::grayscale_palette;
use crate::pytra::runtime::gif::save_gif;

// 10: Sample that outputs a plasma effect as a GIF.

fn run_10_plasma_effect() {
    let w = 320;
    let h = 240;
    let frames_n = 216;
    let out_path = ("sample/out/10_plasma_effect.gif").to_string();
    
    let start = perf_counter();
    let mut frames: Vec<Vec<u8>> = vec![];
    
    let mut t: i64 = 0;
    for __for_i_1 in (0)..(frames_n) {
        t = __for_i_1;
            let mut frame = vec![0u8; (w * h) as usize];
            let mut y: i64 = 0;
            for __for_i_2 in (0)..(h) {
                y = __for_i_2;
                    let row_base = y * w;
                    let mut x: i64 = 0;
                    for __for_i_3 in (0)..(w) {
                        x = __for_i_3;
                            let dx = x - 160;
                            let dy = y - 120;
                            let v = math::sin((((x) as f64) + ((t) as f64) * 2.0) * 0.045) + math::sin((((y) as f64) - ((t) as f64) * 1.2) * 0.05) + math::sin((((x + y) as f64) + ((t) as f64) * 1.7) * 0.03) + math::sin(math::sqrt(dx * dx + dy * dy) * 0.07 - ((t) as f64) * 0.18);
                            let mut c = (((v + 4.0) * (255.0 / 8.0)) as i64);
                            if c < 0 {
                                c = 0;
                            }
                            if c > 255 {
                                c = 255;
                            }
                            let __idx_4 = ((row_base + x) as usize);
                            frame[__idx_4] = ((c) as u8);
                    }
            }
            frames.push((frame).clone());
    }
    save_gif(&(out_path), w, h, &(frames), &(grayscale_palette()), 3, 0);
    let elapsed = perf_counter() - start;
    println!("{} {}", ("output:").to_string(), out_path);
    println!("{} {}", ("frames:").to_string(), frames_n);
    println!("{} {}", ("elapsed_sec:").to_string(), elapsed);
}

fn main() {
    run_10_plasma_effect();
}
