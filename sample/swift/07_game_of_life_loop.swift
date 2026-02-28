import Foundation


// 07: Sample that outputs Game of Life evolution as a GIF.

func next_state(grid: [Any], w: Int64, h: Int64) -> [Any] {
    var nxt: [Any] = __pytra_as_list([])
    let __step_0 = __pytra_int(Int64(1))
    var y = __pytra_int(Int64(0))
    while ((__step_0 >= 0 && y < __pytra_int(h)) || (__step_0 < 0 && y > __pytra_int(h))) {
        var row: [Any] = __pytra_as_list([])
        let __step_1 = __pytra_int(Int64(1))
        var x = __pytra_int(Int64(0))
        while ((__step_1 >= 0 && x < __pytra_int(w)) || (__step_1 < 0 && x > __pytra_int(w))) {
            var cnt: Int64 = __pytra_int(Int64(0))
            let __step_2 = __pytra_int(Int64(1))
            var dy = __pytra_int((-Int64(1)))
            while ((__step_2 >= 0 && dy < __pytra_int(Int64(2))) || (__step_2 < 0 && dy > __pytra_int(Int64(2)))) {
                let __step_3 = __pytra_int(Int64(1))
                var dx = __pytra_int((-Int64(1)))
                while ((__step_3 >= 0 && dx < __pytra_int(Int64(2))) || (__step_3 < 0 && dx > __pytra_int(Int64(2)))) {
                    if ((__pytra_int(dx) != __pytra_int(Int64(0))) || (__pytra_int(dy) != __pytra_int(Int64(0)))) {
                        var nx: Int64 = __pytra_int((__pytra_int((__pytra_int((__pytra_int(x) + __pytra_int(dx))) + __pytra_int(w))) % __pytra_int(w)))
                        var ny: Int64 = __pytra_int((__pytra_int((__pytra_int((__pytra_int(y) + __pytra_int(dy))) + __pytra_int(h))) % __pytra_int(h)))
                        cnt += __pytra_int(__pytra_getIndex(__pytra_as_list(__pytra_getIndex(grid, ny)), nx))
                    }
                    dx += __step_3
                }
                dy += __step_2
            }
            var alive: Int64 = __pytra_int(__pytra_int(__pytra_getIndex(__pytra_as_list(__pytra_getIndex(grid, y)), x)))
            if ((__pytra_int(alive) == __pytra_int(Int64(1))) && ((__pytra_int(cnt) == __pytra_int(Int64(2))) || (__pytra_int(cnt) == __pytra_int(Int64(3))))) {
                row = __pytra_as_list(row); row.append(Int64(1))
            } else {
                if ((__pytra_int(alive) == __pytra_int(Int64(0))) && (__pytra_int(cnt) == __pytra_int(Int64(3)))) {
                    row = __pytra_as_list(row); row.append(Int64(1))
                } else {
                    row = __pytra_as_list(row); row.append(Int64(0))
                }
            }
            x += __step_1
        }
        nxt = __pytra_as_list(nxt); nxt.append(row)
        y += __step_0
    }
    return nxt
}

func render(grid: [Any], w: Int64, h: Int64, cell: Int64) -> [Any] {
    var width: Int64 = __pytra_int((__pytra_int(w) * __pytra_int(cell)))
    var height: Int64 = __pytra_int((__pytra_int(h) * __pytra_int(cell)))
    var frame: [Any] = __pytra_as_list(__pytra_bytearray((__pytra_int(width) * __pytra_int(height))))
    let __step_0 = __pytra_int(Int64(1))
    var y = __pytra_int(Int64(0))
    while ((__step_0 >= 0 && y < __pytra_int(h)) || (__step_0 < 0 && y > __pytra_int(h))) {
        let __step_1 = __pytra_int(Int64(1))
        var x = __pytra_int(Int64(0))
        while ((__step_1 >= 0 && x < __pytra_int(w)) || (__step_1 < 0 && x > __pytra_int(w))) {
            var v: Int64 = __pytra_int(__pytra_ifexp((__pytra_int(__pytra_getIndex(__pytra_as_list(__pytra_getIndex(grid, y)), x)) != 0), Int64(255), Int64(0)))
            let __step_2 = __pytra_int(Int64(1))
            var yy = __pytra_int(Int64(0))
            while ((__step_2 >= 0 && yy < __pytra_int(cell)) || (__step_2 < 0 && yy > __pytra_int(cell))) {
                var base: Int64 = __pytra_int((__pytra_int((__pytra_int((__pytra_int((__pytra_int(y) * __pytra_int(cell))) + __pytra_int(yy))) * __pytra_int(width))) + __pytra_int((__pytra_int(x) * __pytra_int(cell)))))
                let __step_3 = __pytra_int(Int64(1))
                var xx = __pytra_int(Int64(0))
                while ((__step_3 >= 0 && xx < __pytra_int(cell)) || (__step_3 < 0 && xx > __pytra_int(cell))) {
                    __pytra_setIndex(frame, (__pytra_int(base) + __pytra_int(xx)), v)
                    xx += __step_3
                }
                yy += __step_2
            }
            x += __step_1
        }
        y += __step_0
    }
    return __pytra_bytes(frame)
}

func run_07_game_of_life_loop() {
    var w: Int64 = __pytra_int(Int64(144))
    var h: Int64 = __pytra_int(Int64(108))
    var cell: Int64 = __pytra_int(Int64(4))
    var steps: Int64 = __pytra_int(Int64(105))
    var out_path: String = __pytra_str("sample/out/07_game_of_life_loop.gif")
    var start: Double = __pytra_float(__pytra_perf_counter())
    var grid: [Any] = __pytra_as_list(({ () -> [Any] in var __out: [Any] = []; let __step = __pytra_int(Int64(1)); var __lc_i = __pytra_int(Int64(0)); while ((__step >= 0 && __lc_i < __pytra_int(h)) || (__step < 0 && __lc_i > __pytra_int(h))) { __out.append(__pytra_list_repeat(Int64(0), w)); __lc_i += __step }; return __out })())
    let __step_0 = __pytra_int(Int64(1))
    var y = __pytra_int(Int64(0))
    while ((__step_0 >= 0 && y < __pytra_int(h)) || (__step_0 < 0 && y > __pytra_int(h))) {
        let __step_1 = __pytra_int(Int64(1))
        var x = __pytra_int(Int64(0))
        while ((__step_1 >= 0 && x < __pytra_int(w)) || (__step_1 < 0 && x > __pytra_int(w))) {
            var noise: Int64 = __pytra_int((__pytra_int((__pytra_int((__pytra_int((__pytra_int((__pytra_int(x) * __pytra_int(Int64(37)))) + __pytra_int((__pytra_int(y) * __pytra_int(Int64(73)))))) + __pytra_int((__pytra_int((__pytra_int(x) * __pytra_int(y))) % __pytra_int(Int64(19)))))) + __pytra_int((__pytra_int((__pytra_int(x) + __pytra_int(y))) % __pytra_int(Int64(11)))))) % __pytra_int(Int64(97))))
            if (__pytra_int(noise) < __pytra_int(Int64(3))) {
                __pytra_setIndex(__pytra_as_list(__pytra_getIndex(grid, y)), x, Int64(1))
            }
            x += __step_1
        }
        y += __step_0
    }
    var glider: [Any] = __pytra_as_list([[Int64(0), Int64(1), Int64(0)], [Int64(0), Int64(0), Int64(1)], [Int64(1), Int64(1), Int64(1)]])
    var r_pentomino: [Any] = __pytra_as_list([[Int64(0), Int64(1), Int64(1)], [Int64(1), Int64(1), Int64(0)], [Int64(0), Int64(1), Int64(0)]])
    var lwss: [Any] = __pytra_as_list([[Int64(0), Int64(1), Int64(1), Int64(1), Int64(1)], [Int64(1), Int64(0), Int64(0), Int64(0), Int64(1)], [Int64(0), Int64(0), Int64(0), Int64(0), Int64(1)], [Int64(1), Int64(0), Int64(0), Int64(1), Int64(0)]])
    let __step_2 = __pytra_int(Int64(18))
    var gy = __pytra_int(Int64(8))
    while ((__step_2 >= 0 && gy < __pytra_int((__pytra_int(h) - __pytra_int(Int64(8))))) || (__step_2 < 0 && gy > __pytra_int((__pytra_int(h) - __pytra_int(Int64(8)))))) {
        let __step_3 = __pytra_int(Int64(22))
        var gx = __pytra_int(Int64(8))
        while ((__step_3 >= 0 && gx < __pytra_int((__pytra_int(w) - __pytra_int(Int64(8))))) || (__step_3 < 0 && gx > __pytra_int((__pytra_int(w) - __pytra_int(Int64(8)))))) {
            var kind: Int64 = __pytra_int((__pytra_int((__pytra_int((__pytra_int(gx) * __pytra_int(Int64(7)))) + __pytra_int((__pytra_int(gy) * __pytra_int(Int64(11)))))) % __pytra_int(Int64(3))))
            if (__pytra_int(kind) == __pytra_int(Int64(0))) {
                var ph: Int64 = __pytra_int(__pytra_len(glider))
                let __step_4 = __pytra_int(Int64(1))
                var py = __pytra_int(Int64(0))
                while ((__step_4 >= 0 && py < __pytra_int(ph)) || (__step_4 < 0 && py > __pytra_int(ph))) {
                    var pw: Int64 = __pytra_int(__pytra_len(__pytra_as_list(__pytra_getIndex(glider, py))))
                    let __step_5 = __pytra_int(Int64(1))
                    var px = __pytra_int(Int64(0))
                    while ((__step_5 >= 0 && px < __pytra_int(pw)) || (__step_5 < 0 && px > __pytra_int(pw))) {
                        if (__pytra_int(__pytra_int(__pytra_getIndex(__pytra_as_list(__pytra_getIndex(glider, py)), px))) == __pytra_int(Int64(1))) {
                            __pytra_setIndex(__pytra_as_list(__pytra_getIndex(grid, (__pytra_int((__pytra_int(gy) + __pytra_int(py))) % __pytra_int(h)))), (__pytra_int((__pytra_int(gx) + __pytra_int(px))) % __pytra_int(w)), Int64(1))
                        }
                        px += __step_5
                    }
                    py += __step_4
                }
            } else {
                if (__pytra_int(kind) == __pytra_int(Int64(1))) {
                    var ph: Int64 = __pytra_int(__pytra_len(r_pentomino))
                    let __step_6 = __pytra_int(Int64(1))
                    var py = __pytra_int(Int64(0))
                    while ((__step_6 >= 0 && py < __pytra_int(ph)) || (__step_6 < 0 && py > __pytra_int(ph))) {
                        var pw: Int64 = __pytra_int(__pytra_len(__pytra_as_list(__pytra_getIndex(r_pentomino, py))))
                        let __step_7 = __pytra_int(Int64(1))
                        var px = __pytra_int(Int64(0))
                        while ((__step_7 >= 0 && px < __pytra_int(pw)) || (__step_7 < 0 && px > __pytra_int(pw))) {
                            if (__pytra_int(__pytra_int(__pytra_getIndex(__pytra_as_list(__pytra_getIndex(r_pentomino, py)), px))) == __pytra_int(Int64(1))) {
                                __pytra_setIndex(__pytra_as_list(__pytra_getIndex(grid, (__pytra_int((__pytra_int(gy) + __pytra_int(py))) % __pytra_int(h)))), (__pytra_int((__pytra_int(gx) + __pytra_int(px))) % __pytra_int(w)), Int64(1))
                            }
                            px += __step_7
                        }
                        py += __step_6
                    }
                } else {
                    var ph: Int64 = __pytra_int(__pytra_len(lwss))
                    let __step_8 = __pytra_int(Int64(1))
                    var py = __pytra_int(Int64(0))
                    while ((__step_8 >= 0 && py < __pytra_int(ph)) || (__step_8 < 0 && py > __pytra_int(ph))) {
                        var pw: Int64 = __pytra_int(__pytra_len(__pytra_as_list(__pytra_getIndex(lwss, py))))
                        let __step_9 = __pytra_int(Int64(1))
                        var px = __pytra_int(Int64(0))
                        while ((__step_9 >= 0 && px < __pytra_int(pw)) || (__step_9 < 0 && px > __pytra_int(pw))) {
                            if (__pytra_int(__pytra_int(__pytra_getIndex(__pytra_as_list(__pytra_getIndex(lwss, py)), px))) == __pytra_int(Int64(1))) {
                                __pytra_setIndex(__pytra_as_list(__pytra_getIndex(grid, (__pytra_int((__pytra_int(gy) + __pytra_int(py))) % __pytra_int(h)))), (__pytra_int((__pytra_int(gx) + __pytra_int(px))) % __pytra_int(w)), Int64(1))
                            }
                            px += __step_9
                        }
                        py += __step_8
                    }
                }
            }
            gx += __step_3
        }
        gy += __step_2
    }
    var frames: [Any] = __pytra_as_list([])
    let __step_11 = __pytra_int(Int64(1))
    var __loop_10 = __pytra_int(Int64(0))
    while ((__step_11 >= 0 && __loop_10 < __pytra_int(steps)) || (__step_11 < 0 && __loop_10 > __pytra_int(steps))) {
        frames = __pytra_as_list(frames); frames.append(render(grid, w, h, cell))
        grid = __pytra_as_list(next_state(grid, w, h))
        __loop_10 += __step_11
    }
    __pytra_noop(out_path, (__pytra_int(w) * __pytra_int(cell)), (__pytra_int(h) * __pytra_int(cell)), frames, [])
    var elapsed: Double = __pytra_float((__pytra_float(__pytra_perf_counter()) - __pytra_float(start)))
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
