mod py_runtime;
pub use crate::py_runtime::{math, pytra, time};
use crate::py_runtime::*;

use crate::time::perf_counter;
use crate::pytra::utils::gif::grayscale_palette;
use crate::pytra::utils::gif::save_gif;

// 07: Sample that outputs Game of Life evolution as a GIF.

fn next_state(grid: &Vec<Vec<i64>>, w: i64, h: i64) -> Vec<Vec<i64>> {
    let mut nxt: Vec<Vec<i64>> = vec![];
    let mut y: i64 = 0;
    for __for_i_1 in (0)..(h) {
        y = __for_i_1;
            let mut row: Vec<i64> = vec![];
            let mut x: i64 = 0;
            for __for_i_2 in (0)..(w) {
                x = __for_i_2;
                    let mut cnt = 0;
                    let mut dy: i64 = -1;
                    for __for_i_3 in (-1)..(2) {
                        dy = __for_i_3;
                            let mut dx: i64 = -1;
                            for __for_i_4 in (-1)..(2) {
                                dx = __for_i_4;
                                    if (dx != 0) || (dy != 0) {
                                        let nx = (x + dx + w) % w;
                                        let ny = (y + dy + h) % h;
                                        cnt += grid[((if ((ny) as i64) < 0 { (grid.len() as i64 + ((ny) as i64)) } else { ((ny) as i64) }) as usize)][((if ((nx) as i64) < 0 { (grid[((if ((ny) as i64) < 0 { (grid.len() as i64 + ((ny) as i64)) } else { ((ny) as i64) }) as usize)].len() as i64 + ((nx) as i64)) } else { ((nx) as i64) }) as usize)];
                                    }
                            }
                    }
                    let alive = grid[((y) as usize)][((x) as usize)];
                    if (alive == 1) && ((cnt == 2) || (cnt == 3)) {
                        row.push(1);
                    } else if (alive == 0) && (cnt == 3) {
                        row.push(1);
                    } else {
                        row.push(0);
                    }
            }
            nxt.push(row);
    }
    return nxt;
}

fn render(grid: &Vec<Vec<i64>>, w: i64, h: i64, cell: i64) -> Vec<u8> {
    let width = w * cell;
    let height = h * cell;
    let mut frame = vec![0u8; (width * height) as usize];
    let mut y: i64 = 0;
    for __for_i_5 in (0)..(h) {
        y = __for_i_5;
            let mut x: i64 = 0;
            for __for_i_6 in (0)..(w) {
                x = __for_i_6;
                    let v = (if grid[((y) as usize)][((x) as usize)] != 0 { 255 } else { 0 });
                    let mut yy: i64 = 0;
                    for __for_i_7 in (0)..(cell) {
                        yy = __for_i_7;
                            let base = (y * cell + yy) * width + x * cell;
                            let mut xx: i64 = 0;
                            for __for_i_8 in (0)..(cell) {
                                xx = __for_i_8;
                                    let __idx_i64_10 = ((base + xx) as i64);
                                    let __idx_9 = if __idx_i64_10 < 0 { (frame.len() as i64 + __idx_i64_10) as usize } else { __idx_i64_10 as usize };
                                    frame[__idx_9] = ((v) as u8);
                            }
                    }
            }
    }
    return frame;
}

fn run_07_game_of_life_loop() {
    let w = 144;
    let h = 108;
    let cell = 4;
    let steps = 105;
    let out_path = ("sample/out/07_game_of_life_loop.gif").to_string();
    
    let start = perf_counter();
    let mut grid: Vec<Vec<i64>> = (((0)..(h))).map(|py_underscore| vec![0; ((w) as usize)]).collect::<Vec<_>>();
    
    // Lay down sparse noise so the whole field is less likely to stabilize too early.
    // Avoid large integer literals so all transpilers handle the expression consistently.
    let mut y: i64 = 0;
    for __for_i_11 in (0)..(h) {
        y = __for_i_11;
            let mut x: i64 = 0;
            for __for_i_12 in (0)..(w) {
                x = __for_i_12;
                    let noise = (x * 37 + y * 73 + x * y % 19 + (x + y) % 11) % 97;
                    if noise < 3 {
                        let __idx_13 = ((y) as usize);
                        let __idx_14 = ((x) as usize);
                        grid[__idx_13][__idx_14] = 1;
                    }
            }
    }
    // Place multiple well-known long-lived patterns.
    let glider = vec![vec![0, 1, 0], vec![0, 0, 1], vec![1, 1, 1]];
    let r_pentomino = vec![vec![0, 1, 1], vec![1, 1, 0], vec![0, 1, 0]];
    let lwss = vec![vec![0, 1, 1, 1, 1], vec![1, 0, 0, 0, 1], vec![0, 0, 0, 0, 1], vec![1, 0, 0, 1, 0]];
    
    let mut gy: i64 = 8;
    while gy < h - 8 {
        let mut gx: i64 = 8;
        while gx < w - 8 {
            let kind = (gx * 7 + gy * 11) % 3;
            if kind == 0 {
                let mut ph = glider.len() as i64;
                let mut py: i64 = 0;
                for __for_i_15 in (0)..(ph) {
                    py = __for_i_15;
                        let mut pw = (glider[((py) as usize)]).clone().len() as i64;
                        let mut px: i64 = 0;
                        for __for_i_16 in (0)..(pw) {
                            px = __for_i_16;
                                if glider[((py) as usize)][((px) as usize)] == 1 {
                                    let __idx_17 = (((gy + py) % h) as usize);
                                    let __idx_18 = (((gx + px) % w) as usize);
                                    grid[__idx_17][__idx_18] = 1;
                                }
                        }
                }
            } else if kind == 1 {
                let mut ph = r_pentomino.len() as i64;
                let mut py: i64 = 0;
                for __for_i_19 in (0)..(ph) {
                    py = __for_i_19;
                        let mut pw = (r_pentomino[((py) as usize)]).clone().len() as i64;
                        let mut px: i64 = 0;
                        for __for_i_20 in (0)..(pw) {
                            px = __for_i_20;
                                if r_pentomino[((py) as usize)][((px) as usize)] == 1 {
                                    let __idx_21 = (((gy + py) % h) as usize);
                                    let __idx_22 = (((gx + px) % w) as usize);
                                    grid[__idx_21][__idx_22] = 1;
                                }
                        }
                }
            } else {
                let mut ph = lwss.len() as i64;
                let mut py: i64 = 0;
                for __for_i_23 in (0)..(ph) {
                    py = __for_i_23;
                        let mut pw = (lwss[((py) as usize)]).clone().len() as i64;
                        let mut px: i64 = 0;
                        for __for_i_24 in (0)..(pw) {
                            px = __for_i_24;
                                if lwss[((py) as usize)][((px) as usize)] == 1 {
                                    let __idx_25 = (((gy + py) % h) as usize);
                                    let __idx_26 = (((gx + px) % w) as usize);
                                    grid[__idx_25][__idx_26] = 1;
                                }
                        }
                }
            }
            gx += 22;
        }
        gy += 18;
    }
    let mut frames: Vec<Vec<u8>> = vec![];
    let mut py_underscore: i64 = 0;
    for __for_i_27 in (0)..(steps) {
        py_underscore = __for_i_27;
            frames.push(render(&(grid), w, h, cell));
            grid = next_state(&(grid), w, h);
    }
    save_gif(&(out_path), w * cell, h * cell, &(frames), &(grayscale_palette()), 4, 0);
    let elapsed = perf_counter() - start;
    println!("{} {}", ("output:").to_string(), out_path);
    println!("{} {}", ("frames:").to_string(), steps);
    println!("{} {}", ("elapsed_sec:").to_string(), elapsed);
}

fn main() {
    run_07_game_of_life_loop();
}
