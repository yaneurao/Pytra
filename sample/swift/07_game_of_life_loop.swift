import Foundation


// 07: Sample that outputs Game of Life evolution as a GIF.

func next_state(grid: [Any], w: Int64, h: Int64) -> [Any] {
    var nxt: [Any] = __pytra_as_list([])
    var y = __pytra_int(Int64(0))
    while (y < __pytra_int(h)) {
        var row: [Any] = __pytra_as_list([])
        var x = __pytra_int(Int64(0))
        while (x < __pytra_int(w)) {
            var cnt: Int64 = Int64(0)
            var dy = __pytra_int(-Int64(1))
            while (dy < __pytra_int(Int64(2))) {
                var dx = __pytra_int(-Int64(1))
                while (dx < __pytra_int(Int64(2))) {
                    if ((__pytra_int(dx) != __pytra_int(Int64(0))) || (__pytra_int(dy) != __pytra_int(Int64(0)))) {
                        var nx: Int64 = (((x + dx) + w) % w)
                        var ny: Int64 = (((y + dy) + h) % h)
                        cnt += __pytra_int(__pytra_getIndex(__pytra_as_list(__pytra_getIndex(grid, ny)), nx))
                    }
                    dx += 1
                }
                dy += 1
            }
            var alive: Int64 = __pytra_int(__pytra_getIndex(__pytra_as_list(__pytra_getIndex(grid, y)), x))
            if ((__pytra_int(alive) == __pytra_int(Int64(1))) && ((__pytra_int(cnt) == __pytra_int(Int64(2))) || (__pytra_int(cnt) == __pytra_int(Int64(3))))) {
                row.append(Int64(1))
            } else {
                if ((__pytra_int(alive) == __pytra_int(Int64(0))) && (__pytra_int(cnt) == __pytra_int(Int64(3)))) {
                    row.append(Int64(1))
                } else {
                    row.append(Int64(0))
                }
            }
            x += 1
        }
        nxt.append(row)
        y += 1
    }
    return nxt
}

func render(grid: [Any], w: Int64, h: Int64, cell: Int64) -> [Any] {
    var width: Int64 = (w * cell)
    var height: Int64 = (h * cell)
    var frame: [Any] = __pytra_as_list(__pytra_bytearray((width * height)))
    var y = __pytra_int(Int64(0))
    while (y < __pytra_int(h)) {
        var x = __pytra_int(Int64(0))
        while (x < __pytra_int(w)) {
            var v: Int64 = __pytra_int(__pytra_ifexp((__pytra_int(__pytra_getIndex(__pytra_as_list(__pytra_getIndex(grid, y)), x)) != 0), Int64(255), Int64(0)))
            var yy = __pytra_int(Int64(0))
            while (yy < __pytra_int(cell)) {
                var base: Int64 = ((((y * cell) + yy) * width) + (x * cell))
                var xx = __pytra_int(Int64(0))
                while (xx < __pytra_int(cell)) {
                    __pytra_setIndex(frame, (base + xx), v)
                    xx += 1
                }
                yy += 1
            }
            x += 1
        }
        y += 1
    }
    return __pytra_as_list(__pytra_bytes(frame))
}

func run_07_game_of_life_loop() {
    var w: Int64 = Int64(144)
    var h: Int64 = Int64(108)
    var cell: Int64 = Int64(4)
    var steps: Int64 = Int64(105)
    var out_path: String = "sample/out/07_game_of_life_loop.gif"
    var start: Double = __pytra_perf_counter()
    var grid: [Any] = __pytra_as_list(({ () -> [Any] in var __out: [Any] = []; let __step = __pytra_int(Int64(1)); var __lc_i = __pytra_int(Int64(0)); while ((__step >= 0 && __lc_i < __pytra_int(h)) || (__step < 0 && __lc_i > __pytra_int(h))) { __out.append(__pytra_list_repeat(Int64(0), w)); __lc_i += __step }; return __out })())
    var y = __pytra_int(Int64(0))
    while (y < __pytra_int(h)) {
        var x = __pytra_int(Int64(0))
        while (x < __pytra_int(w)) {
            var noise: Int64 = (((((x * Int64(37)) + (y * Int64(73))) + ((x * y) % Int64(19))) + ((x + y) % Int64(11))) % Int64(97))
            if (__pytra_int(noise) < __pytra_int(Int64(3))) {
                __pytra_setIndex(__pytra_as_list(__pytra_getIndex(grid, y)), x, Int64(1))
            }
            x += 1
        }
        y += 1
    }
    var glider: [Any] = __pytra_as_list([[Int64(0), Int64(1), Int64(0)], [Int64(0), Int64(0), Int64(1)], [Int64(1), Int64(1), Int64(1)]])
    var r_pentomino: [Any] = __pytra_as_list([[Int64(0), Int64(1), Int64(1)], [Int64(1), Int64(1), Int64(0)], [Int64(0), Int64(1), Int64(0)]])
    var lwss: [Any] = __pytra_as_list([[Int64(0), Int64(1), Int64(1), Int64(1), Int64(1)], [Int64(1), Int64(0), Int64(0), Int64(0), Int64(1)], [Int64(0), Int64(0), Int64(0), Int64(0), Int64(1)], [Int64(1), Int64(0), Int64(0), Int64(1), Int64(0)]])
    var gy = __pytra_int(Int64(8))
    let __step_2 = __pytra_int(Int64(18))
    while ((__step_2 >= 0 && gy < __pytra_int(h - Int64(8))) || (__step_2 < 0 && gy > __pytra_int(h - Int64(8)))) {
        var gx = __pytra_int(Int64(8))
        let __step_3 = __pytra_int(Int64(22))
        while ((__step_3 >= 0 && gx < __pytra_int(w - Int64(8))) || (__step_3 < 0 && gx > __pytra_int(w - Int64(8)))) {
            var kind: Int64 = (((gx * Int64(7)) + (gy * Int64(11))) % Int64(3))
            if (__pytra_int(kind) == __pytra_int(Int64(0))) {
                var ph: Int64 = __pytra_len(glider)
                var py = __pytra_int(Int64(0))
                while (py < __pytra_int(ph)) {
                    var pw: Int64 = __pytra_len(__pytra_as_list(__pytra_getIndex(glider, py)))
                    var px = __pytra_int(Int64(0))
                    while (px < __pytra_int(pw)) {
                        if (__pytra_int(__pytra_getIndex(__pytra_as_list(__pytra_getIndex(glider, py)), px)) == __pytra_int(Int64(1))) {
                            __pytra_setIndex(__pytra_as_list(__pytra_getIndex(grid, ((gy + py) % h))), ((gx + px) % w), Int64(1))
                        }
                        px += 1
                    }
                    py += 1
                }
            } else {
                if (__pytra_int(kind) == __pytra_int(Int64(1))) {
                    var ph: Int64 = __pytra_len(r_pentomino)
                    var py = __pytra_int(Int64(0))
                    while (py < __pytra_int(ph)) {
                        var pw: Int64 = __pytra_len(__pytra_as_list(__pytra_getIndex(r_pentomino, py)))
                        var px = __pytra_int(Int64(0))
                        while (px < __pytra_int(pw)) {
                            if (__pytra_int(__pytra_getIndex(__pytra_as_list(__pytra_getIndex(r_pentomino, py)), px)) == __pytra_int(Int64(1))) {
                                __pytra_setIndex(__pytra_as_list(__pytra_getIndex(grid, ((gy + py) % h))), ((gx + px) % w), Int64(1))
                            }
                            px += 1
                        }
                        py += 1
                    }
                } else {
                    var ph: Int64 = __pytra_len(lwss)
                    var py = __pytra_int(Int64(0))
                    while (py < __pytra_int(ph)) {
                        var pw: Int64 = __pytra_len(__pytra_as_list(__pytra_getIndex(lwss, py)))
                        var px = __pytra_int(Int64(0))
                        while (px < __pytra_int(pw)) {
                            if (__pytra_int(__pytra_getIndex(__pytra_as_list(__pytra_getIndex(lwss, py)), px)) == __pytra_int(Int64(1))) {
                                __pytra_setIndex(__pytra_as_list(__pytra_getIndex(grid, ((gy + py) % h))), ((gx + px) % w), Int64(1))
                            }
                            px += 1
                        }
                        py += 1
                    }
                }
            }
            gx += __step_3
        }
        gy += __step_2
    }
    var frames: [Any] = __pytra_as_list([])
    var __loop_10 = __pytra_int(Int64(0))
    while (__loop_10 < __pytra_int(steps)) {
        frames.append(render(grid, w, h, cell))
        grid = __pytra_as_list(next_state(grid, w, h))
        __loop_10 += 1
    }
    __pytra_noop(out_path, (w * cell), (h * cell), frames, [])
    var elapsed: Double = (__pytra_perf_counter() - start)
    __pytra_print("output:", out_path)
    __pytra_print("frames:", steps)
    __pytra_print("elapsed_sec:", elapsed)
}

@main
struct Main {
    static func main() {
        run_07_game_of_life_loop()
    }
}
