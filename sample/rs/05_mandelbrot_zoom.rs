#[path = "../../src/rs_module/py_runtime.rs"]
mod py_runtime;
use py_runtime::{math_cos, math_exp, math_sin, math_sqrt, perf_counter, py_bool, py_grayscale_palette, py_in, py_isalpha, py_isdigit, py_len, py_print, py_save_gif, py_slice, py_write_rgb_png};

// このファイルは自動生成です（native Rust mode）。

fn render_frame(mut width: i64, mut height: i64, mut center_x: f64, mut center_y: f64, mut scale: f64, mut max_iter: i64) -> Vec<u8> {
    let mut frame = vec![0u8; (((width) * (height))) as usize];
    let mut idx = 0;
    for y in (0)..(height) {
        let mut cy = ((center_y) + ((((((( y ) as f64) - (( (((( height ) as f64) * (( 0.5 ) as f64))) ) as f64)))) * (scale))));
        for x in (0)..(width) {
            let mut cx = ((center_x) + ((((((( x ) as f64) - (( (((( width ) as f64) * (( 0.5 ) as f64))) ) as f64)))) * (scale))));
            let mut zx = 0.0;
            let mut zy = 0.0;
            let mut i = 0;
            while py_bool(&(((i) < (max_iter)))) {
                let mut zx2 = ((zx) * (zx));
                let mut zy2 = ((zy) * (zy));
                if py_bool(&(((((zx2) + (zy2))) > (4.0)))) {
                    break;
                }
                zy = ((((((2.0) * (zx))) * (zy))) + (cy));
                zx = ((((zx2) - (zy2))) + (cx));
                i = i + 1;
            }
            (frame)[idx as usize] = (((((( (((( 255.0 ) as f64) * (( i ) as f64))) ) as f64) / (( max_iter ) as f64))) as i64)) as u8;
            idx = idx + 1;
        }
    }
    return (frame).clone();
}

fn run_05_mandelbrot_zoom() -> () {
    let mut width = 320;
    let mut height = 240;
    let mut frame_count = 48;
    let mut max_iter = 110;
    let mut center_x = (-0.743643887037151);
    let mut center_y = 0.13182590420533;
    let mut base_scale = ((( 3.2 ) as f64) / (( width ) as f64));
    let mut zoom_per_frame = 0.93;
    let mut out_path = "sample/out/05_mandelbrot_zoom.gif".to_string();
    let mut start = perf_counter();
    let mut frames: Vec<Vec<u8>> = vec![];
    let mut scale = base_scale;
    for _ in (0)..(frame_count) {
        frames.push(render_frame(width, height, center_x, center_y, scale, max_iter));
        scale = scale * zoom_per_frame;
    }
    py_save_gif(&(out_path), width, height, &(frames), &(py_grayscale_palette()), 5, 0);
    let mut elapsed = ((perf_counter()) - (start));
    println!("{} {}", "output:".to_string(), out_path);
    println!("{} {}", "frames:".to_string(), frame_count);
    println!("{} {}", "elapsed_sec:".to_string(), elapsed);
}

fn main() {
    run_05_mandelbrot_zoom();
}
