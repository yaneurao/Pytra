// このファイルは自動生成です（Python -> JavaScript native mode）。

const __pytra_root = process.cwd();
const py_runtime = require(__pytra_root + '/src/js_module/py_runtime.js');
const py_math = require(__pytra_root + '/src/js_module/math.js');
const py_time = require(__pytra_root + '/src/js_module/time.js');
const { pyPrint, pyLen, pyBool, pyRange, pyFloorDiv, pyMod, pyIn, pySlice, pyOrd, pyChr, pyBytearray, pyBytes, pyIsDigit, pyIsAlpha } = py_runtime;
const { perfCounter } = py_time;
const perf_counter = perfCounter;
const { grayscale_palette, save_gif } = require(__pytra_root + '/src/js_module/gif_helper.js');

function next_state(grid, w, h) {
    let nxt = [];
    let y;
    for (let __pytra_i_1 = 0; __pytra_i_1 < h; __pytra_i_1 += 1) {
        y = __pytra_i_1;
        let row = [];
        let x;
        for (let __pytra_i_2 = 0; __pytra_i_2 < w; __pytra_i_2 += 1) {
            x = __pytra_i_2;
            let cnt = 0;
            let dy;
            for (let __pytra_i_3 = (-(1)); __pytra_i_3 < 2; __pytra_i_3 += 1) {
                dy = __pytra_i_3;
                let dx;
                for (let __pytra_i_4 = (-(1)); __pytra_i_4 < 2; __pytra_i_4 += 1) {
                    dx = __pytra_i_4;
                    if (pyBool((((dx) !== (0)) || ((dy) !== (0))))) {
                        let nx = pyMod(((((x) + (dx))) + (w)), w);
                        let ny = pyMod(((((y) + (dy))) + (h)), h);
                        cnt = cnt + grid[ny][nx];
                    }
                }
            }
            let alive = grid[y][x];
            if (pyBool((((alive) === (1)) && (((cnt) === (2)) || ((cnt) === (3)))))) {
                row.push(1);
            } else {
                if (pyBool((((alive) === (0)) && ((cnt) === (3))))) {
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
function render(grid, w, h, cell) {
    let width = ((w) * (cell));
    let height = ((h) * (cell));
    let frame = pyBytearray(((width) * (height)));
    let y;
    for (let __pytra_i_5 = 0; __pytra_i_5 < h; __pytra_i_5 += 1) {
        y = __pytra_i_5;
        let x;
        for (let __pytra_i_6 = 0; __pytra_i_6 < w; __pytra_i_6 += 1) {
            x = __pytra_i_6;
            let v = (pyBool(grid[y][x]) ? 255 : 0);
            let yy;
            for (let __pytra_i_7 = 0; __pytra_i_7 < cell; __pytra_i_7 += 1) {
                yy = __pytra_i_7;
                let base = ((((((((y) * (cell))) + (yy))) * (width))) + (((x) * (cell))));
                let xx;
                for (let __pytra_i_8 = 0; __pytra_i_8 < cell; __pytra_i_8 += 1) {
                    xx = __pytra_i_8;
                    frame[((base) + (xx))] = v;
                }
            }
        }
    }
    return pyBytes(frame);
}
function run_07_game_of_life_loop() {
    let w = 144;
    let h = 108;
    let cell = 4;
    let steps = 210;
    let out_path = 'sample/out/07_game_of_life_loop.gif';
    let start = perf_counter();
    let grid = [];
    let _;
    for (let __pytra_i_9 = 0; __pytra_i_9 < h; __pytra_i_9 += 1) {
        _ = __pytra_i_9;
        let row = [];
        for (let __pytra_i_10 = 0; __pytra_i_10 < w; __pytra_i_10 += 1) {
            _ = __pytra_i_10;
            row.push(0);
        }
        grid.push(row);
    }
    let y;
    for (let __pytra_i_11 = 0; __pytra_i_11 < h; __pytra_i_11 += 1) {
        y = __pytra_i_11;
        let x;
        for (let __pytra_i_12 = 0; __pytra_i_12 < w; __pytra_i_12 += 1) {
            x = __pytra_i_12;
            let noise = pyMod(((((((((x) * (37))) + (((y) * (73))))) + (pyMod(((x) * (y)), 19)))) + (pyMod(((x) + (y)), 11))), 97);
            if (pyBool(((noise) < (3)))) {
                grid[y][x] = 1;
            }
        }
    }
    let glider = [[0, 1, 0], [0, 0, 1], [1, 1, 1]];
    let r_pentomino = [[0, 1, 1], [1, 1, 0], [0, 1, 0]];
    let lwss = [[0, 1, 1, 1, 1], [1, 0, 0, 0, 1], [0, 0, 0, 0, 1], [1, 0, 0, 1, 0]];
    let gy;
    for (let __pytra_i_13 = 8; (18 > 0 ? __pytra_i_13 < ((h) - (8)) : __pytra_i_13 > ((h) - (8))); __pytra_i_13 += 18) {
        gy = __pytra_i_13;
        let gx;
        for (let __pytra_i_14 = 8; (22 > 0 ? __pytra_i_14 < ((w) - (8)) : __pytra_i_14 > ((w) - (8))); __pytra_i_14 += 22) {
            gx = __pytra_i_14;
            let kind = pyMod(((((gx) * (7))) + (((gy) * (11)))), 3);
            if (pyBool(((kind) === (0)))) {
                let ph = pyLen(glider);
                let py;
                for (let __pytra_i_15 = 0; __pytra_i_15 < ph; __pytra_i_15 += 1) {
                    py = __pytra_i_15;
                    let pw = pyLen(glider[py]);
                    let px;
                    for (let __pytra_i_16 = 0; __pytra_i_16 < pw; __pytra_i_16 += 1) {
                        px = __pytra_i_16;
                        if (pyBool(((glider[py][px]) === (1)))) {
                            grid[pyMod(((gy) + (py)), h)][pyMod(((gx) + (px)), w)] = 1;
                        }
                    }
                }
            } else {
                if (pyBool(((kind) === (1)))) {
                    let ph = pyLen(r_pentomino);
                    let py;
                    for (let __pytra_i_17 = 0; __pytra_i_17 < ph; __pytra_i_17 += 1) {
                        py = __pytra_i_17;
                        let pw = pyLen(r_pentomino[py]);
                        let px;
                        for (let __pytra_i_18 = 0; __pytra_i_18 < pw; __pytra_i_18 += 1) {
                            px = __pytra_i_18;
                            if (pyBool(((r_pentomino[py][px]) === (1)))) {
                                grid[pyMod(((gy) + (py)), h)][pyMod(((gx) + (px)), w)] = 1;
                            }
                        }
                    }
                } else {
                    let ph = pyLen(lwss);
                    let py;
                    for (let __pytra_i_19 = 0; __pytra_i_19 < ph; __pytra_i_19 += 1) {
                        py = __pytra_i_19;
                        let pw = pyLen(lwss[py]);
                        let px;
                        for (let __pytra_i_20 = 0; __pytra_i_20 < pw; __pytra_i_20 += 1) {
                            px = __pytra_i_20;
                            if (pyBool(((lwss[py][px]) === (1)))) {
                                grid[pyMod(((gy) + (py)), h)][pyMod(((gx) + (px)), w)] = 1;
                            }
                        }
                    }
                }
            }
        }
    }
    let frames = [];
    for (let __pytra_i_21 = 0; __pytra_i_21 < steps; __pytra_i_21 += 1) {
        _ = __pytra_i_21;
        frames.push(render(grid, w, h, cell));
        grid = next_state(grid, w, h);
    }
    save_gif(out_path, ((w) * (cell)), ((h) * (cell)), frames, grayscale_palette(), 4, 0);
    let elapsed = ((perf_counter()) - (start));
    pyPrint('output:', out_path);
    pyPrint('frames:', steps);
    pyPrint('elapsed_sec:', elapsed);
}
run_07_game_of_life_loop();
