#[path = "../../src/rs_module/py_runtime.rs"]
mod py_runtime;
use py_runtime::{math_cos, math_exp, math_floor, math_sin, math_sqrt, perf_counter, py_bool, py_grayscale_palette, py_in, py_isalpha, py_isdigit, py_len, py_print, py_save_gif, py_slice, py_write_rgb_png};

// このファイルは自動生成です（native Rust mode）。

fn palette() -> Vec<u8> {
    let mut p = Vec::<u8>::new();
    for i in (0)..(256) {
        let mut r = (((((( 20 ) as f64) + (( (((( i ) as f64) * (( 0.9 ) as f64))) ) as f64)))) as i64);
        if py_bool(&(((r) > (255)))) {
            r = 255;
        }
        let mut g = (((((( 10 ) as f64) + (( (((( i ) as f64) * (( 0.7 ) as f64))) ) as f64)))) as i64);
        if py_bool(&(((g) > (255)))) {
            g = 255;
        }
        let mut b = ((((30) + (i))) as i64);
        if py_bool(&(((b) > (255)))) {
            b = 255;
        }
        p.push((r) as u8);
        p.push((g) as u8);
        p.push((b) as u8);
    }
    return (p).clone();
}

fn scene(mut x: f64, mut y: f64, mut light_x: f64, mut light_y: f64) -> i64 {
    let mut x1 = ((x) + (0.45));
    let mut y1 = ((y) + (0.2));
    let mut x2 = ((x) - (0.35));
    let mut y2 = ((y) - (0.15));
    let mut r1 = math_sqrt(((((((x1) * (x1))) + (((y1) * (y1))))) as f64));
    let mut r2 = math_sqrt(((((((x2) * (x2))) + (((y2) * (y2))))) as f64));
    let mut blob = ((math_exp((((((((-7.0)) * (r1))) * (r1))) as f64))) + (math_exp((((((((-8.0)) * (r2))) * (r2))) as f64))));
    let mut lx = ((x) - (light_x));
    let mut ly = ((y) - (light_y));
    let mut l = math_sqrt(((((((lx) * (lx))) + (((ly) * (ly))))) as f64));
    let mut lit = ((( 1.0 ) as f64) / (( ((1.0) + (((((3.5) * (l))) * (l)))) ) as f64));
    let mut v = ((((((((255.0) * (blob))) * (lit))) * (5.0))) as i64);
    if py_bool(&(((v) < (0)))) {
        return 0;
    }
    if py_bool(&(((v) > (255)))) {
        return 255;
    }
    return v;
}

fn run_14_raymarching_light_cycle() -> () {
    let mut w = 320;
    let mut h = 240;
    let mut frames_n = 84;
    let mut out_path = "sample/out/14_raymarching_light_cycle.gif".to_string();
    let mut start = perf_counter();
    let mut frames: Vec<Vec<u8>> = vec![];
    for t in (0)..(frames_n) {
        let mut frame = vec![0u8; (((w) * (h))) as usize];
        let mut a = ((((((( t ) as f64) / (( frames_n ) as f64))) * (std::f64::consts::PI))) * (2.0));
        let mut light_x = ((0.75) * (math_cos(((a) as f64))));
        let mut light_y = ((0.55) * (math_sin(((((a) * (1.2))) as f64))));
        let mut i = 0;
        for y in (0)..(h) {
            let mut py = ((((((( y ) as f64) / (( ((h) - (1)) ) as f64))) * (2.0))) - (1.0));
            for x in (0)..(w) {
                let mut px = ((((((( x ) as f64) / (( ((w) - (1)) ) as f64))) * (2.0))) - (1.0));
                (frame)[i as usize] = (scene(px, py, light_x, light_y)) as u8;
                i = i + 1;
            }
        }
        frames.push((frame).clone());
    }
    py_save_gif(&(out_path), w, h, &(frames), &(palette()), 3, 0);
    let mut elapsed = ((perf_counter()) - (start));
    println!("{} {}", "output:".to_string(), out_path);
    println!("{} {}", "frames:".to_string(), frames_n);
    println!("{} {}", "elapsed_sec:".to_string(), elapsed);
}

fn main() {
    run_14_raymarching_light_cycle();
}
