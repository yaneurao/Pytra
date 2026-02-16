#[path = "../../src/rs_module/py_runtime.rs"]
mod py_runtime;
use py_runtime::{math_cos, math_exp, math_sin, math_sqrt, perf_counter, py_bool, py_grayscale_palette, py_in, py_isalpha, py_isdigit, py_len, py_print, py_save_gif, py_slice, py_write_rgb_png};

// このファイルは自動生成です（native Rust mode）。

fn render_frame(mut width: i64, mut height: i64, mut cr: f64, mut ci: f64, mut max_iter: i64) -> Vec<u8> {
    let mut frame = vec![0u8; (((width) * (height))) as usize];
    let mut idx = 0;
    for y in (0)..(height) {
        let mut zy0 = (((-1.2)) + (((2.4) * (((( y ) as f64) / (( ((height) - (1)) ) as f64))))));
        for x in (0)..(width) {
            let mut zx = (((-1.8)) + (((3.6) * (((( x ) as f64) / (( ((width) - (1)) ) as f64))))));
            let mut zy = zy0;
            let mut i = 0;
            while py_bool(&(((i) < (max_iter)))) {
                let mut zx2 = ((zx) * (zx));
                let mut zy2 = ((zy) * (zy));
                if py_bool(&(((((zx2) + (zy2))) > (4.0)))) {
                    break;
                }
                zy = ((((((2.0) * (zx))) * (zy))) + (ci));
                zx = ((((zx2) - (zy2))) + (cr));
                i = i + 1;
            }
            (frame)[idx as usize] = (((((( (((( 255.0 ) as f64) * (( i ) as f64))) ) as f64) / (( max_iter ) as f64))) as i64)) as u8;
            idx = idx + 1;
        }
    }
    return (frame).clone();
}

fn run_06_julia_parameter_sweep() -> () {
    let mut width = 320;
    let mut height = 240;
    let mut frames_n = 50;
    let mut max_iter = 120;
    let mut out_path = "sample/out/06_julia_parameter_sweep.gif".to_string();
    let mut start = perf_counter();
    let mut frames: Vec<Vec<u8>> = vec![];
    for i in (0)..(frames_n) {
        let mut t = ((( i ) as f64) / (( frames_n ) as f64));
        let mut cr = (((-0.8)) + (((0.32) * (t))));
        let mut ci = ((0.156) + (((0.22) * (((0.5) - (t))))));
        frames.push(render_frame(width, height, cr, ci, max_iter));
    }
    py_save_gif(&(out_path), width, height, &(frames), &(py_grayscale_palette()), 4, 0);
    let mut elapsed = ((perf_counter()) - (start));
    println!("{} {}", "output:".to_string(), out_path);
    println!("{} {}", "frames:".to_string(), frames_n);
    println!("{} {}", "elapsed_sec:".to_string(), elapsed);
}

fn main() {
    run_06_julia_parameter_sweep();
}
