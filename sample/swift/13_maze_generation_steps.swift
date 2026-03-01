import Foundation


// 13: Sample that outputs DFS maze-generation progress as a GIF.

func capture(grid: [Any], w: Int64, h: Int64, scale: Int64) -> [Any] {
    var width: Int64 = (w * scale)
    var height: Int64 = (h * scale)
    var frame: [Any] = __pytra_as_list(__pytra_bytearray((width * height)))
    var y = __pytra_int(Int64(0))
    while (y < __pytra_int(h)) {
        var x = __pytra_int(Int64(0))
        while (x < __pytra_int(w)) {
            var v: Int64 = __pytra_int(__pytra_ifexp((__pytra_int(__pytra_getIndex(__pytra_as_list(__pytra_getIndex(grid, y)), x)) == __pytra_int(Int64(0))), Int64(255), Int64(40)))
            var yy = __pytra_int(Int64(0))
            while (yy < __pytra_int(scale)) {
                var base: Int64 = ((((y * scale) + yy) * width) + (x * scale))
                var xx = __pytra_int(Int64(0))
                while (xx < __pytra_int(scale)) {
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

func run_13_maze_generation_steps() {
    var cell_w: Int64 = Int64(89)
    var cell_h: Int64 = Int64(67)
    var scale: Int64 = Int64(5)
    var capture_every: Int64 = Int64(20)
    var out_path: String = "sample/out/13_maze_generation_steps.gif"
    var start: Double = __pytra_perf_counter()
    var grid: [Any] = __pytra_as_list(({ () -> [Any] in var __out: [Any] = []; let __step = __pytra_int(Int64(1)); var __lc_i = __pytra_int(Int64(0)); while ((__step >= 0 && __lc_i < __pytra_int(cell_h)) || (__step < 0 && __lc_i > __pytra_int(cell_h))) { __out.append(__pytra_list_repeat(Int64(1), cell_w)); __lc_i += __step }; return __out })())
    var stack: [Any] = __pytra_as_list([[Int64(1), Int64(1)]])
    __pytra_setIndex(__pytra_as_list(__pytra_getIndex(grid, Int64(1))), Int64(1), Int64(0))
    var dirs: [Any] = __pytra_as_list([[Int64(2), Int64(0)], [(-Int64(2)), Int64(0)], [Int64(0), Int64(2)], [Int64(0), (-Int64(2))]])
    var frames: [Any] = __pytra_as_list([])
    var step: Int64 = Int64(0)
    while (__pytra_len(stack) != 0) {
        let __tuple_0 = __pytra_as_list(__pytra_as_list(__pytra_getIndex(stack, (-Int64(1)))))
        x = __pytra_int(__tuple_0[0])
        y = __pytra_int(__tuple_0[1])
        var candidates: [Any] = __pytra_as_list([])
        var k = __pytra_int(Int64(0))
        while (k < __pytra_int(Int64(4))) {
            let __tuple_2 = __pytra_as_list(__pytra_as_list(__pytra_getIndex(dirs, k)))
            dx = __pytra_int(__tuple_2[0])
            dy = __pytra_int(__tuple_2[1])
            var nx: Any = (x + dx)
            var ny: Any = (y + dy)
            if ((__pytra_int(nx) >= __pytra_int(Int64(1))) && (__pytra_int(nx) < __pytra_int(cell_w - Int64(1))) && (__pytra_int(ny) >= __pytra_int(Int64(1))) && (__pytra_int(ny) < __pytra_int(cell_h - Int64(1))) && (__pytra_int(__pytra_getIndex(__pytra_as_list(__pytra_getIndex(grid, ny)), nx)) == __pytra_int(Int64(1)))) {
                if (__pytra_int(dx) == __pytra_int(Int64(2))) {
                    candidates.append([nx, ny, (x + Int64(1)), y])
                } else {
                    if (__pytra_int(dx) == __pytra_int(-Int64(2))) {
                        candidates.append([nx, ny, (x - Int64(1)), y])
                    } else {
                        if (__pytra_int(dy) == __pytra_int(Int64(2))) {
                            candidates.append([nx, ny, x, (y + Int64(1))])
                        } else {
                            candidates.append([nx, ny, x, (y - Int64(1))])
                        }
                    }
                }
            }
            k += 1
        }
        if (__pytra_int(__pytra_len(candidates)) == __pytra_int(Int64(0))) {
            stack = __pytra_pop_last(__pytra_as_list(stack))
        } else {
            var sel: [Any] = __pytra_as_list(__pytra_getIndex(candidates, (__pytra_int(((x * Int64(17)) + (y * Int64(29))) + (__pytra_len(stack) * Int64(13))) % __pytra_len(candidates))))
            let __tuple_3 = __pytra_as_list(sel)
            var nx: Int64 = __pytra_int(__tuple_3[0])
            var ny: Int64 = __pytra_int(__tuple_3[1])
            var wx: Int64 = __pytra_int(__tuple_3[2])
            var wy: Int64 = __pytra_int(__tuple_3[3])
            __pytra_setIndex(__pytra_as_list(__pytra_getIndex(grid, wy)), wx, Int64(0))
            __pytra_setIndex(__pytra_as_list(__pytra_getIndex(grid, ny)), nx, Int64(0))
            stack.append([nx, ny])
        }
        if (__pytra_int(step % capture_every) == __pytra_int(Int64(0))) {
            frames.append(capture(grid, cell_w, cell_h, scale))
        }
        step += Int64(1)
    }
    frames.append(capture(grid, cell_w, cell_h, scale))
    __pytra_noop(out_path, (cell_w * scale), (cell_h * scale), frames, [])
    var elapsed: Double = (__pytra_perf_counter() - start)
    __pytra_print("output:", out_path)
    __pytra_print("frames:", __pytra_len(frames))
    __pytra_print("elapsed_sec:", elapsed)
}

@main
struct Main {
    static func main() {
        run_13_maze_generation_steps()
    }
}
