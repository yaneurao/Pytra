#[path = "../../src/runtime/rs/pytra/built_in/py_runtime.rs"]
mod py_runtime;
use py_runtime::{math_cos, math_exp, math_floor, math_sin, math_sqrt, perf_counter, py_bool, py_grayscale_palette, py_in, py_isalpha, py_isdigit, py_len, py_print, py_save_gif, py_slice, py_write_rgb_png};

// このファイルは自動生成です（native Rust mode）。

fn capture(grid: &Vec<Vec<i64>>, mut w: i64, mut h: i64, mut scale: i64) -> Vec<u8> {
    let mut width = ((w) * (scale));
    let mut height = ((h) * (scale));
    let mut frame = vec![0u8; (((width) * (height))) as usize];
    for y in (0)..(h) {
        for x in (0)..(w) {
            let mut v = (if py_bool(&(((((grid)[y as usize])[x as usize]) == (0)))) { 255 } else { 40 });
            for yy in (0)..(scale) {
                let mut base = ((((((((y) * (scale))) + (yy))) * (width))) + (((x) * (scale))));
                for xx in (0)..(scale) {
                    (frame)[((base) + (xx)) as usize] = (v) as u8;
                }
            }
        }
    }
    return (frame).clone();
}

fn run_13_maze_generation_steps() -> () {
    let mut cell_w = 89;
    let mut cell_h = 67;
    let mut scale = 5;
    let mut capture_every = 20;
    let mut out_path = "sample/out/13_maze_generation_steps.gif".to_string();
    let mut start = perf_counter();
    let mut grid: Vec<Vec<i64>> = vec![];
    for _ in (0)..(cell_h) {
        let mut row: Vec<i64> = vec![];
        for _ in (0)..(cell_w) {
            row.push(1);
        }
        grid.push(row);
    }
    let mut stack: Vec<(i64, i64)> = vec![(1, 1)];
    ((grid)[1 as usize])[1 as usize] = 0;
    let mut dirs: Vec<(i64, i64)> = vec![(2, 0), ((-2), 0), (0, 2), (0, (-2))];
    let mut frames: Vec<Vec<u8>> = vec![];
    let mut step = 0;
    while py_bool(&((((py_len(&(stack)) as i64)) > (0)))) {
        let mut last_index = (((py_len(&(stack)) as i64)) - (1));
        let __pytra_tuple_rhs_1 = ((stack)[last_index as usize]).clone();
        let mut x = __pytra_tuple_rhs_1.0;
        let mut y = __pytra_tuple_rhs_1.1;
        let mut candidates: Vec<(i64, i64, i64, i64)> = vec![];
        for k in (0)..(4) {
            let __pytra_tuple_rhs_2 = ((dirs)[k as usize]).clone();
            let mut dx = __pytra_tuple_rhs_2.0;
            let mut dy = __pytra_tuple_rhs_2.1;
            let mut nx = ((x) + (dx));
            let mut ny = ((y) + (dy));
            if py_bool(&((((nx) >= (1)) && ((nx) < (((cell_w) - (1)))) && ((ny) >= (1)) && ((ny) < (((cell_h) - (1)))) && ((((grid)[ny as usize])[nx as usize]) == (1))))) {
                if py_bool(&(((dx) == (2)))) {
                    candidates.push((nx, ny, ((x) + (1)), y));
                } else {
                    if py_bool(&(((dx) == ((-2))))) {
                        candidates.push((nx, ny, ((x) - (1)), y));
                    } else {
                        if py_bool(&(((dy) == (2)))) {
                            candidates.push((nx, ny, x, ((y) + (1))));
                        } else {
                            candidates.push((nx, ny, x, ((y) - (1))));
                        }
                    }
                }
            }
        }
        if py_bool(&((((py_len(&(candidates)) as i64)) == (0)))) {
            stack.pop().unwrap();
        } else {
            let mut sel = ((candidates)[((((((((x) * (17))) + (((y) * (29))))) + ((((py_len(&(stack)) as i64)) * (13))))) % ((py_len(&(candidates)) as i64))) as usize]).clone();
            let __pytra_tuple_rhs_3 = sel;
            let mut nx = __pytra_tuple_rhs_3.0;
            let mut ny = __pytra_tuple_rhs_3.1;
            let mut wx = __pytra_tuple_rhs_3.2;
            let mut wy = __pytra_tuple_rhs_3.3;
            ((grid)[wy as usize])[wx as usize] = 0;
            ((grid)[ny as usize])[nx as usize] = 0;
            stack.push((nx, ny));
        }
        if py_bool(&(((((step) % (capture_every))) == (0)))) {
            frames.push(capture(&(grid), cell_w, cell_h, scale));
        }
        step = step + 1;
    }
    frames.push(capture(&(grid), cell_w, cell_h, scale));
    py_save_gif(&(out_path), ((cell_w) * (scale)), ((cell_h) * (scale)), &(frames), &(py_grayscale_palette()), 4, 0);
    let mut elapsed = ((perf_counter()) - (start));
    println!("{} {}", "output:".to_string(), out_path);
    println!("{} {}", "frames:".to_string(), (py_len(&(frames)) as i64));
    println!("{} {}", "elapsed_sec:".to_string(), elapsed);
}

fn main() {
    run_13_maze_generation_steps();
}
