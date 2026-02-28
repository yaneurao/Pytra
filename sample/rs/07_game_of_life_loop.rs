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
    while y < h {
        let mut row: Vec<i64> = vec![];
        let mut x: i64 = 0;
        while x < w {
            let mut cnt = 0;
            let mut dy: i64 = -1;
            while dy < 2 {
                let mut dx: i64 = -1;
                while dx < 2 {
                    if (dx != 0) || (dy != 0) {
                        let nx = (x + dx + w) % w;
                        let ny = (y + dy + h) % h;
                        cnt += grid[((if ((ny) as i64) < 0 { (grid.len() as i64 + ((ny) as i64)) } else { ((ny) as i64) }) as usize)][((if ((nx) as i64) < 0 { (grid[((if ((ny) as i64) < 0 { (grid.len() as i64 + ((ny) as i64)) } else { ((ny) as i64) }) as usize)].len() as i64 + ((nx) as i64)) } else { ((nx) as i64) }) as usize)];
                    }
                    dx += 1;
                }
                dy += 1;
            }
            let alive = grid[((if ((y) as i64) < 0 { (grid.len() as i64 + ((y) as i64)) } else { ((y) as i64) }) as usize)][((if ((x) as i64) < 0 { (grid[((if ((y) as i64) < 0 { (grid.len() as i64 + ((y) as i64)) } else { ((y) as i64) }) as usize)].len() as i64 + ((x) as i64)) } else { ((x) as i64) }) as usize)];
            if (alive == 1) && ((cnt == 2) || (cnt == 3)) {
                row.push(1);
            } else {
                if (alive == 0) && (cnt == 3) {
                    row.push(1);
                } else {
                    row.push(0);
                }
            }
            x += 1;
        }
        nxt.push(row);
        y += 1;
    }
    return nxt;
}

fn render(grid: &Vec<Vec<i64>>, w: i64, h: i64, cell: i64) -> Vec<u8> {
    let width = w * cell;
    let height = h * cell;
    let mut frame = vec![0u8; (width * height) as usize];
    let mut y: i64 = 0;
    while y < h {
        let mut x: i64 = 0;
        while x < w {
            let v = (if grid[((if ((y) as i64) < 0 { (grid.len() as i64 + ((y) as i64)) } else { ((y) as i64) }) as usize)][((if ((x) as i64) < 0 { (grid[((if ((y) as i64) < 0 { (grid.len() as i64 + ((y) as i64)) } else { ((y) as i64) }) as usize)].len() as i64 + ((x) as i64)) } else { ((x) as i64) }) as usize)] != 0 { 255 } else { 0 });
            let mut yy: i64 = 0;
            while yy < cell {
                let base = (y * cell + yy) * width + x * cell;
                let mut xx: i64 = 0;
                while xx < cell {
                    let __idx_i64_1 = ((base + xx) as i64);
                    let __idx_2 = if __idx_i64_1 < 0 { (frame.len() as i64 + __idx_i64_1) as usize } else { __idx_i64_1 as usize };
                    frame[__idx_2] = ((v) as u8);
                    xx += 1;
                }
                yy += 1;
            }
            x += 1;
        }
        y += 1;
    }
    return (frame).clone();
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
    while y < h {
        let mut x: i64 = 0;
        while x < w {
            let noise = (x * 37 + y * 73 + x * y % 19 + (x + y) % 11) % 97;
            if noise < 3 {
                let __idx_i64_3 = ((y) as i64);
                let __idx_4 = if __idx_i64_3 < 0 { (grid.len() as i64 + __idx_i64_3) as usize } else { __idx_i64_3 as usize };
                let __idx_i64_5 = ((x) as i64);
                let __idx_6 = if __idx_i64_5 < 0 { (grid[__idx_4].len() as i64 + __idx_i64_5) as usize } else { __idx_i64_5 as usize };
                grid[__idx_4][__idx_6] = 1;
            }
            x += 1;
        }
        y += 1;
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
                while py < ph {
                    let mut pw = (glider[((if ((py) as i64) < 0 { (glider.len() as i64 + ((py) as i64)) } else { ((py) as i64) }) as usize)]).clone().len() as i64;
                    let mut px: i64 = 0;
                    while px < pw {
                        if glider[((if ((py) as i64) < 0 { (glider.len() as i64 + ((py) as i64)) } else { ((py) as i64) }) as usize)][((if ((px) as i64) < 0 { (glider[((if ((py) as i64) < 0 { (glider.len() as i64 + ((py) as i64)) } else { ((py) as i64) }) as usize)].len() as i64 + ((px) as i64)) } else { ((px) as i64) }) as usize)] == 1 {
                            let __idx_i64_7 = (((gy + py) % h) as i64);
                            let __idx_8 = if __idx_i64_7 < 0 { (grid.len() as i64 + __idx_i64_7) as usize } else { __idx_i64_7 as usize };
                            let __idx_i64_9 = (((gx + px) % w) as i64);
                            let __idx_10 = if __idx_i64_9 < 0 { (grid[__idx_8].len() as i64 + __idx_i64_9) as usize } else { __idx_i64_9 as usize };
                            grid[__idx_8][__idx_10] = 1;
                        }
                        px += 1;
                    }
                    py += 1;
                }
            } else {
                if kind == 1 {
                    let mut ph = r_pentomino.len() as i64;
                    let mut py: i64 = 0;
                    while py < ph {
                        let mut pw = (r_pentomino[((if ((py) as i64) < 0 { (r_pentomino.len() as i64 + ((py) as i64)) } else { ((py) as i64) }) as usize)]).clone().len() as i64;
                        let mut px: i64 = 0;
                        while px < pw {
                            if r_pentomino[((if ((py) as i64) < 0 { (r_pentomino.len() as i64 + ((py) as i64)) } else { ((py) as i64) }) as usize)][((if ((px) as i64) < 0 { (r_pentomino[((if ((py) as i64) < 0 { (r_pentomino.len() as i64 + ((py) as i64)) } else { ((py) as i64) }) as usize)].len() as i64 + ((px) as i64)) } else { ((px) as i64) }) as usize)] == 1 {
                                let __idx_i64_11 = (((gy + py) % h) as i64);
                                let __idx_12 = if __idx_i64_11 < 0 { (grid.len() as i64 + __idx_i64_11) as usize } else { __idx_i64_11 as usize };
                                let __idx_i64_13 = (((gx + px) % w) as i64);
                                let __idx_14 = if __idx_i64_13 < 0 { (grid[__idx_12].len() as i64 + __idx_i64_13) as usize } else { __idx_i64_13 as usize };
                                grid[__idx_12][__idx_14] = 1;
                            }
                            px += 1;
                        }
                        py += 1;
                    }
                } else {
                    let mut ph = lwss.len() as i64;
                    let mut py: i64 = 0;
                    while py < ph {
                        let mut pw = (lwss[((if ((py) as i64) < 0 { (lwss.len() as i64 + ((py) as i64)) } else { ((py) as i64) }) as usize)]).clone().len() as i64;
                        let mut px: i64 = 0;
                        while px < pw {
                            if lwss[((if ((py) as i64) < 0 { (lwss.len() as i64 + ((py) as i64)) } else { ((py) as i64) }) as usize)][((if ((px) as i64) < 0 { (lwss[((if ((py) as i64) < 0 { (lwss.len() as i64 + ((py) as i64)) } else { ((py) as i64) }) as usize)].len() as i64 + ((px) as i64)) } else { ((px) as i64) }) as usize)] == 1 {
                                let __idx_i64_15 = (((gy + py) % h) as i64);
                                let __idx_16 = if __idx_i64_15 < 0 { (grid.len() as i64 + __idx_i64_15) as usize } else { __idx_i64_15 as usize };
                                let __idx_i64_17 = (((gx + px) % w) as i64);
                                let __idx_18 = if __idx_i64_17 < 0 { (grid[__idx_16].len() as i64 + __idx_i64_17) as usize } else { __idx_i64_17 as usize };
                                grid[__idx_16][__idx_18] = 1;
                            }
                            px += 1;
                        }
                        py += 1;
                    }
                }
            }
            gx += 22;
        }
        gy += 18;
    }
    let mut frames: Vec<Vec<u8>> = vec![];
    let mut py_underscore: i64 = 0;
    while py_underscore < steps {
        frames.push(render(&(grid), w, h, cell));
        grid = next_state(&(grid), w, h);
        py_underscore += 1;
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
