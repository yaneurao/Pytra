#[path = "../../src/runtime/rs/pytra/built_in/py_runtime.rs"]
mod py_runtime;
use py_runtime::{math_cos, math_exp, math_floor, math_sin, math_sqrt, perf_counter, py_bool, py_grayscale_palette, py_in, py_isalpha, py_isdigit, py_len, py_print, py_save_gif, py_slice, py_write_rgb_png};

// このファイルは自動生成です（native Rust mode）。

fn run_10_plasma_effect() -> () {
    let mut w = 320;
    let mut h = 240;
    let mut frames_n = 216;
    let mut out_path = "sample/out/10_plasma_effect.gif".to_string();
    let mut start = perf_counter();
    let mut frames: Vec<Vec<u8>> = vec![];
    for t in (0)..(frames_n) {
        let mut frame = vec![0u8; (((w) * (h))) as usize];
        let mut i = 0;
        for y in (0)..(h) {
            for x in (0)..(w) {
                let mut dx = ((x) - (160));
                let mut dy = ((y) - (120));
                let mut v = ((((((math_sin((((((((( x ) as f64) + (( (((( t ) as f64) * (( 2.0 ) as f64))) ) as f64)))) * (0.045))) as f64))) + (math_sin((((((((( y ) as f64) - (( (((( t ) as f64) * (( 1.2 ) as f64))) ) as f64)))) * (0.05))) as f64))))) + (math_sin((((((((( ((x) + (y)) ) as f64) + (( (((( t ) as f64) * (( 1.7 ) as f64))) ) as f64)))) * (0.03))) as f64))))) + (math_sin(((((((math_sqrt(((((((dx) * (dx))) + (((dy) * (dy))))) as f64))) * (0.07))) - ((((( t ) as f64) * (( 0.18 ) as f64)))))) as f64))));
                let mut c = ((((((v) + (4.0))) * (((( 255.0 ) as f64) / (( 8.0 ) as f64))))) as i64);
                if py_bool(&(((c) < (0)))) {
                    c = 0;
                }
                if py_bool(&(((c) > (255)))) {
                    c = 255;
                }
                (frame)[i as usize] = (c) as u8;
                i = i + 1;
            }
        }
        frames.push((frame).clone());
    }
    py_save_gif(&(out_path), w, h, &(frames), &(py_grayscale_palette()), 3, 0);
    let mut elapsed = ((perf_counter()) - (start));
    println!("{} {}", "output:".to_string(), out_path);
    println!("{} {}", "frames:".to_string(), frames_n);
    println!("{} {}", "elapsed_sec:".to_string(), elapsed);
}

fn main() {
    run_10_plasma_effect();
}
