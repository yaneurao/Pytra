#[path = "../../src/rs_module/py_runtime.rs"]
mod py_runtime;
use py_runtime::{math_cos, math_exp, math_sin, math_sqrt, perf_counter, py_bool, py_grayscale_palette, py_in, py_isalpha, py_isdigit, py_len, py_print, py_save_gif, py_slice, py_write_rgb_png};

// このファイルは自動生成です（native Rust mode）。

fn render_julia(mut width: i64, mut height: i64, mut max_iter: i64, mut cx: f64, mut cy: f64) -> Vec<u8> {
    let mut pixels: Vec<u8> = Vec::<u8>::new();
    for y in (0)..(height) {
        let mut zy0: f64 = (((-1.2)) + (((2.4) * (((( y ) as f64) / (( ((height) - (1)) ) as f64))))));
        for x in (0)..(width) {
            let mut zx: f64 = (((-1.8)) + (((3.6) * (((( x ) as f64) / (( ((width) - (1)) ) as f64))))));
            let mut zy: f64 = zy0;
            let mut i: i64 = 0;
            while py_bool(&(((i) < (max_iter)))) {
                let mut zx2: f64 = ((zx) * (zx));
                let mut zy2: f64 = ((zy) * (zy));
                if py_bool(&(((((zx2) + (zy2))) > (4.0)))) {
                    break;
                }
                zy = ((((((2.0) * (zx))) * (zy))) + (cy));
                zx = ((((zx2) - (zy2))) + (cx));
                i = i + 1;
            }
            let mut r: i64 = 0;
            let mut g: i64 = 0;
            let mut b: i64 = 0;
            if py_bool(&(((i) >= (max_iter)))) {
                r = 0;
                g = 0;
                b = 0;
            } else {
                let mut t: f64 = ((( i ) as f64) / (( max_iter ) as f64));
                r = ((((255.0) * (((0.2) + (((0.8) * (t))))))) as i64);
                g = ((((255.0) * (((0.1) + (((0.9) * (((t) * (t))))))))) as i64);
                b = ((((255.0) * (((1.0) - (t))))) as i64);
            }
            pixels.push((r) as u8);
            pixels.push((g) as u8);
            pixels.push((b) as u8);
        }
    }
    return pixels;
}

fn run_julia() -> () {
    let mut width: i64 = 1280;
    let mut height: i64 = 720;
    let mut max_iter: i64 = 520;
    let mut out_path: String = "sample/out/julia_03.png".to_string();
    let mut start: f64 = perf_counter();
    let mut pixels: Vec<u8> = render_julia(width, height, max_iter, (-0.8), 0.156);
    py_write_rgb_png(&(out_path), width, height, &(pixels));
    let mut elapsed: f64 = ((perf_counter()) - (start));
    println!("{} {}", "output:".to_string(), out_path);
    println!("{} {} {} {}", "size:".to_string(), width, "x".to_string(), height);
    println!("{} {}", "max_iter:".to_string(), max_iter);
    println!("{} {}", "elapsed_sec:".to_string(), elapsed);
}

fn main() {
    run_julia();
}
