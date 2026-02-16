#[path = "../../src/rs_module/py_runtime.rs"]
mod py_runtime;
use py_runtime::{math_cos, math_exp, math_sin, math_sqrt, perf_counter, py_bool, py_grayscale_palette, py_in, py_isalpha, py_isdigit, py_len, py_print, py_save_gif, py_slice, py_write_rgb_png};

// このファイルは自動生成です（native Rust mode）。

fn julia_palette() -> Vec<u8> {
    let mut palette = vec![0u8; (((256) * (3))) as usize];
    (palette)[0 as usize] = (0) as u8;
    (palette)[1 as usize] = (0) as u8;
    (palette)[2 as usize] = (0) as u8;
    for i in (1)..(256) {
        let mut t = ((( ((i) - (1)) ) as f64) / (( 254.0 ) as f64));
        let mut r = ((((255.0) * (((((((((9.0) * (((1.0) - (t))))) * (t))) * (t))) * (t))))) as i64);
        let mut g = ((((255.0) * (((((((((15.0) * (((1.0) - (t))))) * (((1.0) - (t))))) * (t))) * (t))))) as i64);
        let mut b = ((((255.0) * (((((((((8.5) * (((1.0) - (t))))) * (((1.0) - (t))))) * (((1.0) - (t))))) * (t))))) as i64);
        (palette)[((((i) * (3))) + (0)) as usize] = (r) as u8;
        (palette)[((((i) * (3))) + (1)) as usize] = (g) as u8;
        (palette)[((((i) * (3))) + (2)) as usize] = (b) as u8;
    }
    return (palette).clone();
}

fn render_frame(mut width: i64, mut height: i64, mut cr: f64, mut ci: f64, mut max_iter: i64, mut phase: i64) -> Vec<u8> {
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
            if py_bool(&(((i) >= (max_iter)))) {
                (frame)[idx as usize] = (0) as u8;
            } else {
                let mut color_index = ((1) + (((((((((i) * (224))) / (max_iter))) + (phase))) % (255))));
                (frame)[idx as usize] = (color_index) as u8;
            }
            idx = idx + 1;
        }
    }
    return (frame).clone();
}

fn run_06_julia_parameter_sweep() -> () {
    let mut width = 320;
    let mut height = 240;
    let mut frames_n = 72;
    let mut max_iter = 180;
    let mut out_path = "sample/out/06_julia_parameter_sweep.gif".to_string();
    let mut start = perf_counter();
    let mut frames: Vec<Vec<u8>> = vec![];
    let mut center_cr = (-0.745);
    let mut center_ci = 0.186;
    let mut radius_cr = 0.12;
    let mut radius_ci = 0.1;
    for i in (0)..(frames_n) {
        let mut t = ((( i ) as f64) / (( frames_n ) as f64));
        let mut angle = ((((2.0) * (std::f64::consts::PI))) * (t));
        let mut cr = ((center_cr) + (((radius_cr) * (math_cos(((angle) as f64))))));
        let mut ci = ((center_ci) + (((radius_ci) * (math_sin(((angle) as f64))))));
        let mut phase = ((((i) * (5))) % (255));
        frames.push(render_frame(width, height, cr, ci, max_iter, phase));
    }
    py_save_gif(&(out_path), width, height, &(frames), &(julia_palette()), 8, 0);
    let mut elapsed = ((perf_counter()) - (start));
    println!("{} {}", "output:".to_string(), out_path);
    println!("{} {}", "frames:".to_string(), frames_n);
    println!("{} {}", "elapsed_sec:".to_string(), elapsed);
}

fn main() {
    run_06_julia_parameter_sweep();
}
