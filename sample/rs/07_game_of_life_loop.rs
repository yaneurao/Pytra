#[path = "../../src/rs_module/py_runtime.rs"]
mod py_runtime;
use py_runtime::{math_cos, math_exp, math_floor, math_sin, math_sqrt, perf_counter, py_bool, py_grayscale_palette, py_in, py_isalpha, py_isdigit, py_len, py_print, py_save_gif, py_slice, py_write_rgb_png};

// このファイルは自動生成です（native Rust mode）。

fn next_state(grid: &Vec<Vec<i64>>, mut w: i64, mut h: i64) -> Vec<Vec<i64>> {
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

fn render(grid: &Vec<Vec<i64>>, mut w: i64, mut h: i64, mut cell: i64) -> Vec<u8> {
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
    let mut w = 144;
    let mut h = 108;
    let mut cell = 4;
    let mut steps = 210;
    let mut out_path = "sample/out/07_game_of_life_loop.gif".to_string();
    let mut start = perf_counter();
    let mut grid: Vec<Vec<i64>> = vec![];
    for _ in (0)..(h) {
        let mut row: Vec<i64> = vec![];
        for _ in (0)..(w) {
            row.push(0);
        }
        grid.push(row);
    }
    for y in (0)..(h) {
        for x in (0)..(w) {
            let mut noise = ((((((((((x) * (37))) + (((y) * (73))))) + (((((x) * (y))) % (19))))) + (((((x) + (y))) % (11))))) % (97));
            if py_bool(&(((noise) < (3)))) {
                ((grid)[y as usize])[x as usize] = 1;
            }
        }
    }
    let mut glider = vec![vec![0, 1, 0], vec![0, 0, 1], vec![1, 1, 1]];
    let mut r_pentomino = vec![vec![0, 1, 1], vec![1, 1, 0], vec![0, 1, 0]];
    let mut lwss = vec![vec![0, 1, 1, 1, 1], vec![1, 0, 0, 0, 1], vec![0, 0, 0, 0, 1], vec![1, 0, 0, 1, 0]];
    let mut __pytra_i_1 = 8;
    while ((18) > 0 && __pytra_i_1 < (((h) - (8)))) || ((18) < 0 && __pytra_i_1 > (((h) - (8)))) {
        let gy = __pytra_i_1;
        let mut __pytra_i_2 = 8;
        while ((22) > 0 && __pytra_i_2 < (((w) - (8)))) || ((22) < 0 && __pytra_i_2 > (((w) - (8)))) {
            let gx = __pytra_i_2;
            let mut kind = ((((((gx) * (7))) + (((gy) * (11))))) % (3));
            if py_bool(&(((kind) == (0)))) {
                let mut ph = (py_len(&(glider)) as i64);
                for py in (0)..(ph) {
                    let mut pw = (py_len(&((glider)[py as usize])) as i64);
                    for px in (0)..(pw) {
                        if py_bool(&(((((glider)[py as usize])[px as usize]) == (1)))) {
                            ((grid)[((((gy) + (py))) % (h)) as usize])[((((gx) + (px))) % (w)) as usize] = 1;
                        }
                    }
                }
            } else {
                if py_bool(&(((kind) == (1)))) {
                    let mut ph = (py_len(&(r_pentomino)) as i64);
                    for py in (0)..(ph) {
                        let mut pw = (py_len(&((r_pentomino)[py as usize])) as i64);
                        for px in (0)..(pw) {
                            if py_bool(&(((((r_pentomino)[py as usize])[px as usize]) == (1)))) {
                                ((grid)[((((gy) + (py))) % (h)) as usize])[((((gx) + (px))) % (w)) as usize] = 1;
                            }
                        }
                    }
                } else {
                    let mut ph = (py_len(&(lwss)) as i64);
                    for py in (0)..(ph) {
                        let mut pw = (py_len(&((lwss)[py as usize])) as i64);
                        for px in (0)..(pw) {
                            if py_bool(&(((((lwss)[py as usize])[px as usize]) == (1)))) {
                                ((grid)[((((gy) + (py))) % (h)) as usize])[((((gx) + (px))) % (w)) as usize] = 1;
                            }
                        }
                    }
                }
            }
            __pytra_i_2 += (22);
        }
        __pytra_i_1 += (18);
    }
    let mut frames: Vec<Vec<u8>> = vec![];
    for _ in (0)..(steps) {
        frames.push(render(&(grid), w, h, cell));
        grid = next_state(&(grid), w, h);
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
