#[path = "../../src/rs_module/py_runtime.rs"]
mod py_runtime;
use py_runtime::{math_cos, math_exp, math_sin, math_sqrt, perf_counter, py_bool, py_grayscale_palette, py_in, py_isalpha, py_isdigit, py_len, py_print, py_save_gif, py_slice, py_write_rgb_png};

// このファイルは自動生成です（native Rust mode）。

fn color_palette() -> Vec<u8> {
    let mut p = Vec::<u8>::new();
    for i in (0)..(256) {
        let mut r = i;
        let mut g = ((((i) * (3))) % (256));
        let mut b = ((255) - (i));
        p.push((r) as u8);
        p.push((g) as u8);
        p.push((b) as u8);
    }
    return (p).clone();
}

fn run_11_lissajous_particles() -> () {
    let mut w = 320;
    let mut h = 240;
    let mut frames_n = 80;
    let mut particles = 24;
    let mut out_path = "sample/out/11_lissajous_particles.gif".to_string();
    let mut start = perf_counter();
    let mut frames: Vec<Vec<u8>> = vec![];
    for t in (0)..(frames_n) {
        let mut frame = vec![0u8; (((w) * (h))) as usize];
        for p in (0)..(particles) {
            let mut phase = (((( p ) as f64) * (( 0.261799 ) as f64)));
            let mut x = (((((((( w ) as f64) * (( 0.5 ) as f64)))) + ((((((( w ) as f64) * (( 0.38 ) as f64)))) * (math_sin((((((((( 0.11 ) as f64) * (( t ) as f64)))) + (((phase) * (2.0))))) as f64))))))) as i64);
            let mut y = (((((((( h ) as f64) * (( 0.5 ) as f64)))) + ((((((( h ) as f64) * (( 0.38 ) as f64)))) * (math_sin((((((((( 0.17 ) as f64) * (( t ) as f64)))) + (((phase) * (3.0))))) as f64))))))) as i64);
            let mut color = ((30) + (((((p) * (9))) % (220))));
            for dy in ((-2))..(3) {
                for dx in ((-2))..(3) {
                    let mut xx = ((x) + (dx));
                    let mut yy = ((y) + (dy));
                    if py_bool(&((((xx) >= (0)) && ((xx) < (w)) && ((yy) >= (0)) && ((yy) < (h))))) {
                        let mut d2 = ((((dx) * (dx))) + (((dy) * (dy))));
                        if py_bool(&(((d2) <= (4)))) {
                            let mut idx = ((((yy) * (w))) + (xx));
                            let mut v = ((color) - (((d2) * (20))));
                            if py_bool(&(((v) < (0)))) {
                                v = 0;
                            }
                            if py_bool(&((((( v ) as f64) > (( (frame)[idx as usize] ) as f64))))) {
                                (frame)[idx as usize] = (v) as u8;
                            }
                        }
                    }
                }
            }
        }
        frames.push((frame).clone());
    }
    py_save_gif(&(out_path), w, h, &(frames), &(color_palette()), 3, 0);
    let mut elapsed = ((perf_counter()) - (start));
    println!("{} {}", "output:".to_string(), out_path);
    println!("{} {}", "frames:".to_string(), frames_n);
    println!("{} {}", "elapsed_sec:".to_string(), elapsed);
}

fn main() {
    run_11_lissajous_particles();
}
