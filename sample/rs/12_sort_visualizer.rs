#[path = "../../src/rs_module/py_runtime.rs"]
mod py_runtime;
use py_runtime::{math_cos, math_exp, math_floor, math_sin, math_sqrt, perf_counter, py_bool, py_grayscale_palette, py_in, py_isalpha, py_isdigit, py_len, py_print, py_save_gif, py_slice, py_write_rgb_png};

// このファイルは自動生成です（native Rust mode）。

fn render(values: &Vec<i64>, mut w: i64, mut h: i64) -> Vec<u8> {
    let mut frame = vec![0u8; (((w) * (h))) as usize];
    let mut n = (py_len(values) as i64);
    let mut bar_w = ((( w ) as f64) / (( n ) as f64));
    for i in (0)..(n) {
        let mut x0 = (((((( i ) as f64) * (( bar_w ) as f64)))) as i64);
        let mut x1 = (((((( ((i) + (1)) ) as f64) * (( bar_w ) as f64)))) as i64);
        if py_bool(&(((x1) <= (x0)))) {
            x1 = ((x0) + (1));
        }
        let mut bh = (((((( ((( (values)[i as usize] ) as f64) / (( n ) as f64)) ) as f64) * (( h ) as f64)))) as i64);
        let mut y = ((h) - (bh));
        for y in (y)..(h) {
            for x in (x0)..(x1) {
                (frame)[((((y) * (w))) + (x)) as usize] = (255) as u8;
            }
        }
    }
    return (frame).clone();
}

fn run_12_sort_visualizer() -> () {
    let mut w = 320;
    let mut h = 180;
    let mut n = 124;
    let mut out_path = "sample/out/12_sort_visualizer.gif".to_string();
    let mut start = perf_counter();
    let mut values: Vec<i64> = vec![];
    for i in (0)..(n) {
        values.push(((((((i) * (37))) + (19))) % (n)));
    }
    let mut frames: Vec<Vec<u8>> = vec![render(&(values), w, h)];
    let mut op = 0;
    for i in (0)..(n) {
        let mut swapped = false;
        for j in (0)..(((((n) - (i))) - (1))) {
            if py_bool(&((((values)[j as usize]) > ((values)[((j) + (1)) as usize])))) {
                let mut tmp = (values)[j as usize];
                (values)[j as usize] = (values)[((j) + (1)) as usize];
                (values)[((j) + (1)) as usize] = tmp;
                swapped = true;
            }
            if py_bool(&(((((op) % (8))) == (0)))) {
                frames.push(render(&(values), w, h));
            }
            op = op + 1;
        }
        if py_bool(&((!swapped))) {
            break;
        }
    }
    py_save_gif(&(out_path), w, h, &(frames), &(py_grayscale_palette()), 3, 0);
    let mut elapsed = ((perf_counter()) - (start));
    println!("{} {}", "output:".to_string(), out_path);
    println!("{} {}", "frames:".to_string(), (py_len(&(frames)) as i64));
    println!("{} {}", "elapsed_sec:".to_string(), elapsed);
}

fn main() {
    run_12_sort_visualizer();
}
