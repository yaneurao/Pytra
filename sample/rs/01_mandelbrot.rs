#[path = "../../src/rs_module/py_runtime.rs"]
mod py_runtime;
use py_runtime::{math_cos, math_exp, math_floor, math_sin, math_sqrt, perf_counter, py_bool, py_grayscale_palette, py_in, py_isalpha, py_isdigit, py_len, py_print, py_save_gif, py_slice, py_write_rgb_png};

// このファイルは自動生成です（native Rust mode）。

fn escape_count(mut cx: f64, mut cy: f64, mut max_iter: i64) -> i64 {
    let mut x: f64 = 0.0;
    let mut y: f64 = 0.0;
    for i in (0)..(max_iter) {
        let mut x2: f64 = ((x) * (x));
        let mut y2: f64 = ((y) * (y));
        if py_bool(&(((((x2) + (y2))) > (4.0)))) {
            return i;
        }
        y = ((((((2.0) * (x))) * (y))) + (cy));
        x = ((((x2) - (y2))) + (cx));
    }
    return max_iter;
}

fn color_map(mut iter_count: i64, mut max_iter: i64) -> (i64, i64, i64) {
    if py_bool(&(((iter_count) >= (max_iter)))) {
        return (0, 0, 0);
    }
    let mut t: f64 = ((( iter_count ) as f64) / (( max_iter ) as f64));
    let mut r: i64 = ((((255.0) * (((t) * (t))))) as i64);
    let mut g: i64 = ((((255.0) * (t))) as i64);
    let mut b: i64 = ((((255.0) * (((1.0) - (t))))) as i64);
    return (r, g, b);
}

fn render_mandelbrot(mut width: i64, mut height: i64, mut max_iter: i64, mut x_min: f64, mut x_max: f64, mut y_min: f64, mut y_max: f64) -> Vec<u8> {
    let mut pixels: Vec<u8> = Vec::<u8>::new();
    for y in (0)..(height) {
        let mut py: f64 = ((y_min) + (((((y_max) - (y_min))) * (((( y ) as f64) / (( ((height) - (1)) ) as f64))))));
        for x in (0)..(width) {
            let mut px: f64 = ((x_min) + (((((x_max) - (x_min))) * (((( x ) as f64) / (( ((width) - (1)) ) as f64))))));
            let mut it: i64 = escape_count(px, py, max_iter);
            let mut r: i64;
            let mut g: i64;
            let mut b: i64;
            if py_bool(&(((it) >= (max_iter)))) {
                r = 0;
                g = 0;
                b = 0;
            } else {
                let mut t: f64 = ((( it ) as f64) / (( max_iter ) as f64));
                r = ((((255.0) * (((t) * (t))))) as i64);
                g = ((((255.0) * (t))) as i64);
                b = ((((255.0) * (((1.0) - (t))))) as i64);
            }
            pixels.push((r) as u8);
            pixels.push((g) as u8);
            pixels.push((b) as u8);
        }
    }
    return pixels;
}

fn run_mandelbrot() -> () {
    let mut width: i64 = 1600;
    let mut height: i64 = 1200;
    let mut max_iter: i64 = 1000;
    let mut out_path: String = "sample/out/01_mandelbrot.png".to_string();
    let mut start: f64 = perf_counter();
    let mut pixels: Vec<u8> = render_mandelbrot(width, height, max_iter, (-2.2), 1.0, (-1.2), 1.2);
    py_write_rgb_png(&(out_path), width, height, &(pixels));
    let mut elapsed: f64 = ((perf_counter()) - (start));
    println!("{} {}", "output:".to_string(), out_path);
    println!("{} {} {} {}", "size:".to_string(), width, "x".to_string(), height);
    println!("{} {}", "max_iter:".to_string(), max_iter);
    println!("{} {}", "elapsed_sec:".to_string(), elapsed);
}

fn main() {
    run_mandelbrot();
}
