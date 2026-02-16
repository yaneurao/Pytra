// このファイルは自動生成です（Python -> JavaScript native mode）。

const __pytra_root = process.cwd();
const py_runtime = require(__pytra_root + '/src/js_module/py_runtime.js');
const py_math = require(__pytra_root + '/src/js_module/math.js');
const py_time = require(__pytra_root + '/src/js_module/time.js');
const { pyPrint, pyLen, pyBool, pyRange, pyFloorDiv, pyMod, pyIn, pySlice, pyOrd, pyChr, pyBytearray, pyBytes, pyIsDigit, pyIsAlpha } = py_runtime;
const { perfCounter } = py_time;
const perf_counter = perfCounter;
const { grayscale_palette, save_gif } = require(__pytra_root + '/src/js_module/gif_helper.js');

function capture(grid, w, h, scale) {
    let width = ((w) * (scale));
    let height = ((h) * (scale));
    let frame = pyBytearray(((width) * (height)));
    let y;
    for (let __pytra_i_1 = 0; __pytra_i_1 < h; __pytra_i_1 += 1) {
        y = __pytra_i_1;
        let x;
        for (let __pytra_i_2 = 0; __pytra_i_2 < w; __pytra_i_2 += 1) {
            x = __pytra_i_2;
            let v = (pyBool(((grid[y][x]) === (0))) ? 255 : 40);
            let yy;
            for (let __pytra_i_3 = 0; __pytra_i_3 < scale; __pytra_i_3 += 1) {
                yy = __pytra_i_3;
                let base = ((((((((y) * (scale))) + (yy))) * (width))) + (((x) * (scale))));
                let xx;
                for (let __pytra_i_4 = 0; __pytra_i_4 < scale; __pytra_i_4 += 1) {
                    xx = __pytra_i_4;
                    frame[((base) + (xx))] = v;
                }
            }
        }
    }
    return pyBytes(frame);
}
function run_13_maze_generation_steps() {
    let cell_w = 89;
    let cell_h = 67;
    let scale = 5;
    let capture_every = 20;
    let out_path = 'sample/out/13_maze_generation_steps.gif';
    let start = perf_counter();
    let grid = [];
    let _;
    for (let __pytra_i_5 = 0; __pytra_i_5 < cell_h; __pytra_i_5 += 1) {
        _ = __pytra_i_5;
        let row = [];
        for (let __pytra_i_6 = 0; __pytra_i_6 < cell_w; __pytra_i_6 += 1) {
            _ = __pytra_i_6;
            row.push(1);
        }
        grid.push(row);
    }
    let stack = [[1, 1]];
    grid[1][1] = 0;
    let dirs = [[2, 0], [(-(2)), 0], [0, 2], [0, (-(2))]];
    let frames = [];
    let step = 0;
    while (pyBool(((pyLen(stack)) > (0)))) {
        let last_index = ((pyLen(stack)) - (1));
        const __pytra_tuple_7 = stack[last_index];
        let x = __pytra_tuple_7[0];
        let y = __pytra_tuple_7[1];
        let candidates = [];
        let k;
        for (let __pytra_i_8 = 0; __pytra_i_8 < 4; __pytra_i_8 += 1) {
            k = __pytra_i_8;
            const __pytra_tuple_9 = dirs[k];
            let dx = __pytra_tuple_9[0];
            let dy = __pytra_tuple_9[1];
            let nx = ((x) + (dx));
            let ny = ((y) + (dy));
            if (pyBool((((nx) >= (1)) && ((nx) < (((cell_w) - (1)))) && ((ny) >= (1)) && ((ny) < (((cell_h) - (1)))) && ((grid[ny][nx]) === (1))))) {
                if (pyBool(((dx) === (2)))) {
                    candidates.push([nx, ny, ((x) + (1)), y]);
                } else {
                    if (pyBool(((dx) === ((-(2)))))) {
                        candidates.push([nx, ny, ((x) - (1)), y]);
                    } else {
                        if (pyBool(((dy) === (2)))) {
                            candidates.push([nx, ny, x, ((y) + (1))]);
                        } else {
                            candidates.push([nx, ny, x, ((y) - (1))]);
                        }
                    }
                }
            }
        }
        if (pyBool(((pyLen(candidates)) === (0)))) {
            stack.pop();
        } else {
            let sel = candidates[pyMod(((((((x) * (17))) + (((y) * (29))))) + (((pyLen(stack)) * (13)))), pyLen(candidates))];
            const __pytra_tuple_10 = sel;
            let nx = __pytra_tuple_10[0];
            let ny = __pytra_tuple_10[1];
            let wx = __pytra_tuple_10[2];
            let wy = __pytra_tuple_10[3];
            grid[wy][wx] = 0;
            grid[ny][nx] = 0;
            stack.push([nx, ny]);
        }
        if (pyBool(((pyMod(step, capture_every)) === (0)))) {
            frames.push(capture(grid, cell_w, cell_h, scale));
        }
        step = step + 1;
    }
    frames.push(capture(grid, cell_w, cell_h, scale));
    save_gif(out_path, ((cell_w) * (scale)), ((cell_h) * (scale)), frames, grayscale_palette(), 4, 0);
    let elapsed = ((perf_counter()) - (start));
    pyPrint('output:', out_path);
    pyPrint('frames:', pyLen(frames));
    pyPrint('elapsed_sec:', elapsed);
}
run_13_maze_generation_steps();
