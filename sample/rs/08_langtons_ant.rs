#[path = "../../src/rs_module/py_runtime.rs"]
mod py_runtime;
use py_runtime::{math_cos, math_exp, math_sin, math_sqrt, perf_counter, py_bool, py_grayscale_palette, py_in, py_len, py_print, py_save_gif, py_slice, py_write_rgb_png};

// このファイルは自動生成です（native Rust mode）。

fn capture(grid: Vec<Vec<i64>>, w: i64, h: i64) -> Vec<u8> {
    let mut frame = vec![0u8; (((w) * (h))) as usize];
    let mut i = 0;
    for y in (0)..(h) {
        for x in (0)..(w) {
            (frame)[i as usize] = ((if py_bool(&(((grid)[y as usize])[x as usize])) { 255 } else { 0 })) as u8;
            i = i + 1;
        }
    }
    return (frame).clone();
}

fn run_08_langtons_ant() -> () {
    let mut w = 240;
    let mut h = 240;
    let mut out_path = "sample/out/08_langtons_ant.gif".to_string();
    let mut start = perf_counter();
    let mut grid: Vec<Vec<i64>> = vec![];
    for gy in (0)..(h) {
        let mut row: Vec<i64> = vec![];
        for gx in (0)..(w) {
            row.push(0);
        }
        grid.push(row);
    }
    let mut x = ((w) / (2));
    let mut y = ((h) / (2));
    let mut d = 0;
    let mut steps_total = 180000;
    let mut capture_every = 3000;
    let mut frames: Vec<Vec<u8>> = vec![];
    for i in (0)..(steps_total) {
        if py_bool(&(((((grid)[y as usize])[x as usize]) == (0)))) {
            d = ((((d) + (1))) % (4));
            ((grid)[y as usize])[x as usize] = 1;
        } else {
            d = ((((d) + (3))) % (4));
            ((grid)[y as usize])[x as usize] = 0;
        }
        if py_bool(&(((d) == (0)))) {
            y = ((((((y) - (1))) + (h))) % (h));
        } else {
            if py_bool(&(((d) == (1)))) {
                x = ((((x) + (1))) % (w));
            } else {
                if py_bool(&(((d) == (2)))) {
                    y = ((((y) + (1))) % (h));
                } else {
                    x = ((((((x) - (1))) + (w))) % (w));
                }
            }
        }
        if py_bool(&(((((i) % (capture_every))) == (0)))) {
            frames.push(capture((grid).clone(), w, h));
        }
    }
    py_save_gif(&(out_path), w, h, &(frames), &(py_grayscale_palette()), 5, 0);
    let mut elapsed = ((perf_counter()) - (start));
    println!("{} {}", "output:".to_string(), out_path);
    println!("{} {}", "frames:".to_string(), (py_len(&frames) as i64));
    println!("{} {}", "elapsed_sec:".to_string(), elapsed);
}

fn main() {
    run_08_langtons_ant();
}
