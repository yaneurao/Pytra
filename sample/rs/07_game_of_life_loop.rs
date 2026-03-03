mod py_runtime;
pub use crate::py_runtime::{math, pytra, time};
use crate::py_runtime::*;

use crate::time::perf_counter;
use crate::pytra::utils::gif::grayscale_palette;
use crate::pytra::utils::gif::save_gif;

// 07: Sample that outputs Game of Life evolution as a GIF.

fn next_state(grid: &[Vec<i64>], w: i64, h: i64) -> Vec<Vec<i64>> {
    let mut nxt: Vec<Vec<i64>> = vec![];
    for y in (0)..(h) {
            let mut row: Vec<i64> = vec![];
            for x in (0)..(w) {
                    let mut cnt = 0;
                    for dy in (-1)..(2) {
                            for dx in (-1)..(2) {
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

fn render(grid: &[Vec<i64>], w: i64, h: i64, cell: i64) -> Vec<u8> {
    let width = w * cell;
    let height = h * cell;
    let mut frame = vec![0u8; (width * height) as usize];
    for y in (0)..(h) {
            for x in (0)..(w) {
                    let v = (if grid[((y) as usize)][((x) as usize)] != 0 { 255 } else { 0 });
                    for yy in (0)..(cell) {
                            let base = (y * cell + yy) * width + x * cell;
                            for xx in (0)..(cell) {
                                    let __idx_i64_8 = ((base + xx) as i64);
                                    let __idx_7 = if __idx_i64_8 < 0 { (frame.len() as i64 + __idx_i64_8) as usize } else { __idx_i64_8 as usize };
                                    frame[__idx_7] = ((v) as u8);
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
    for y in (0)..(h) {
            for x in (0)..(w) {
                    let noise = (x * 37 + y * 73 + x * y % 19 + (x + y) % 11) % 97;
                    if noise < 3 {
                        let __idx_11 = ((y) as usize);
                        let __idx_12 = ((x) as usize);
                        grid[__idx_11][__idx_12] = 1;
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
                for py in (0)..(ph) {
                        let mut pw = (glider[((py) as usize)]).clone().len() as i64;
                        for px in (0)..(pw) {
                                if glider[((py) as usize)][((px) as usize)] == 1 {
                                    let __idx_15 = (((gy + py) % h) as usize);
                                    let __idx_16 = (((gx + px) % w) as usize);
                                    grid[__idx_15][__idx_16] = 1;
                                }
                        }
                }
            } else if kind == 1 {
                let mut ph = r_pentomino.len() as i64;
                for py in (0)..(ph) {
                        let mut pw = (r_pentomino[((py) as usize)]).clone().len() as i64;
                        for px in (0)..(pw) {
                                if r_pentomino[((py) as usize)][((px) as usize)] == 1 {
                                    let __idx_19 = (((gy + py) % h) as usize);
                                    let __idx_20 = (((gx + px) % w) as usize);
                                    grid[__idx_19][__idx_20] = 1;
                                }
                        }
                }
            } else {
                let mut ph = lwss.len() as i64;
                for py in (0)..(ph) {
                        let mut pw = (lwss[((py) as usize)]).clone().len() as i64;
                        for px in (0)..(pw) {
                                if lwss[((py) as usize)][((px) as usize)] == 1 {
                                    let __idx_23 = (((gy + py) % h) as usize);
                                    let __idx_24 = (((gx + px) % w) as usize);
                                    grid[__idx_23][__idx_24] = 1;
                                }
                        }
                }
            }
            gx += 22;
        }
        gy += 18;
    }
    let mut frames: Vec<Vec<u8>> = vec![];
    for py_underscore in (0)..(steps) {
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
