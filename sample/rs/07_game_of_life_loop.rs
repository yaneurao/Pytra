#[path = "../../src/rs_module/py_runtime.rs"]
mod py_runtime;
use py_runtime::{math_cos, math_exp, math_sin, math_sqrt, perf_counter, py_bool, py_grayscale_palette, py_in, py_len, py_print, py_save_gif, py_slice, py_write_rgb_png};

// このファイルは自動生成です（native Rust mode）。

fn next_state(grid: Vec<Vec<i64>>, w: i64, h: i64) -> Vec<Vec<i64>> {
    let mut nxt: Vec<Vec<i64>> = vec![];
    for y in (0)..(h) {
        let mut row: Vec<i64> = vec![];
        for x in (0)..(w) {
            let mut cnt = 0;
            for dy in ((-1))..(2) {
                for dx in ((-1))..(2) {
                    if py_bool(&((((dx) != (0)) || ((dy) != (0))))) {
                        let mut nx = ((((((x) + (dx))) + (w))) % (w));
                        let mut ny = ((((((y) + (dy))) + (h))) % (h));
                        cnt = cnt + ((grid)[ny as usize])[nx as usize];
                    }
                }
            }
            let mut alive = ((grid)[y as usize])[x as usize];
            if py_bool(&((((alive) == (1)) && (((cnt) == (2)) || ((cnt) == (3)))))) {
                row.push(1);
            } else {
                if py_bool(&((((alive) == (0)) && ((cnt) == (3))))) {
                    row.push(1);
                } else {
                    row.push(0);
                }
            }
        }
        nxt.push(row);
    }
    return nxt;
}

fn render(grid: Vec<Vec<i64>>, w: i64, h: i64, cell: i64) -> Vec<u8> {
    let mut width = ((w) * (cell));
    let mut height = ((h) * (cell));
    let mut frame = vec![0u8; (((width) * (height))) as usize];
    for y in (0)..(h) {
        for x in (0)..(w) {
            let mut v = (if py_bool(&(((grid)[y as usize])[x as usize])) { 255 } else { 0 });
            for yy in (0)..(cell) {
                let mut base = ((((((((y) * (cell))) + (yy))) * (width))) + (((x) * (cell))));
                for xx in (0)..(cell) {
                    (frame)[((base) + (xx)) as usize] = (v) as u8;
                }
            }
        }
    }
    return (frame).clone();
}

fn run_07_game_of_life_loop() -> () {
    let mut w = 96;
    let mut h = 72;
    let mut cell = 3;
    let mut steps = 70;
    let mut out_path = "sample/out/07_game_of_life_loop.gif".to_string();
    let mut start = perf_counter();
    let mut grid: Vec<Vec<i64>> = vec![];
    for y in (0)..(h) {
        let mut row: Vec<i64> = vec![];
        for x in (0)..(w) {
            row.push((if py_bool(&(((((((((((x) * (17))) + (((y) * (31))))) + (13))) % (11))) < (3)))) { 1 } else { 0 }));
        }
        grid.push(row);
    }
    let mut frames: Vec<Vec<u8>> = vec![];
    for _ in (0)..(steps) {
        frames.push(render((grid).clone(), w, h, cell));
        grid = next_state((grid).clone(), w, h);
    }
    py_save_gif(&(out_path), ((w) * (cell)), ((h) * (cell)), &(frames), &(py_grayscale_palette()), 4, 0);
    let mut elapsed = ((perf_counter()) - (start));
    println!("{} {}", "output:".to_string(), out_path);
    println!("{} {}", "frames:".to_string(), steps);
    println!("{} {}", "elapsed_sec:".to_string(), elapsed);
}

fn main() {
    run_07_game_of_life_loop();
}
