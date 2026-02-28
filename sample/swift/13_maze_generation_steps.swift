// Auto-generated Pytra Swift native source from EAST3.
import Foundation

// Runtime helpers are provided by py_runtime.swift in the same module.


// 13: Sample that outputs DFS maze-generation progress as a GIF.

func capture(grid: [Any], w: Int64, h: Int64, scale: Int64) -> [Any] {
    var width: Int64 = __pytra_int((__pytra_int(w) * __pytra_int(scale)))
    var height: Int64 = __pytra_int((__pytra_int(h) * __pytra_int(scale)))
    var frame: [Any] = __pytra_as_list(__pytra_bytearray((__pytra_int(width) * __pytra_int(height))))
    let __step_0 = __pytra_int(Int64(1))
    var y = __pytra_int(Int64(0))
    while ((__step_0 >= 0 && y < __pytra_int(h)) || (__step_0 < 0 && y > __pytra_int(h))) {
        let __step_1 = __pytra_int(Int64(1))
        var x = __pytra_int(Int64(0))
        while ((__step_1 >= 0 && x < __pytra_int(w)) || (__step_1 < 0 && x > __pytra_int(w))) {
            var v: Int64 = __pytra_int(__pytra_ifexp((__pytra_int(__pytra_int(__pytra_getIndex(__pytra_as_list(__pytra_getIndex(grid, y)), x))) == __pytra_int(Int64(0))), Int64(255), Int64(40)))
            let __step_2 = __pytra_int(Int64(1))
            var yy = __pytra_int(Int64(0))
            while ((__step_2 >= 0 && yy < __pytra_int(scale)) || (__step_2 < 0 && yy > __pytra_int(scale))) {
                var base: Int64 = __pytra_int((__pytra_int((__pytra_int((__pytra_int((__pytra_int(y) * __pytra_int(scale))) + __pytra_int(yy))) * __pytra_int(width))) + __pytra_int((__pytra_int(x) * __pytra_int(scale)))))
                let __step_3 = __pytra_int(Int64(1))
                var xx = __pytra_int(Int64(0))
                while ((__step_3 >= 0 && xx < __pytra_int(scale)) || (__step_3 < 0 && xx > __pytra_int(scale))) {
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

func run_13_maze_generation_steps() {
    var cell_w: Int64 = __pytra_int(Int64(89))
    var cell_h: Int64 = __pytra_int(Int64(67))
    var scale: Int64 = __pytra_int(Int64(5))
    var capture_every: Int64 = __pytra_int(Int64(20))
    var out_path: String = __pytra_str("sample/out/13_maze_generation_steps.gif")
    var start: Double = __pytra_float(__pytra_perf_counter())
    var grid: [Any] = __pytra_as_list(({ () -> [Any] in var __out: [Any] = []; let __step = __pytra_int(Int64(1)); var __lc_i = __pytra_int(Int64(0)); while ((__step >= 0 && __lc_i < __pytra_int(cell_h)) || (__step < 0 && __lc_i > __pytra_int(cell_h))) { __out.append(__pytra_list_repeat(Int64(1), cell_w)); __lc_i += __step }; return __out })())
    var stack: [Any] = __pytra_as_list([[Int64(1), Int64(1)]])
    __pytra_setIndex(__pytra_as_list(__pytra_getIndex(grid, Int64(1))), Int64(1), Int64(0))
    var dirs: [Any] = __pytra_as_list([[Int64(2), Int64(0)], [(-Int64(2)), Int64(0)], [Int64(0), Int64(2)], [Int64(0), (-Int64(2))]])
    var frames: [Any] = __pytra_as_list([])
    var step: Int64 = __pytra_int(Int64(0))
    while (__pytra_len(stack) != 0) {
        let __tuple_0 = __pytra_as_list(__pytra_as_list(__pytra_getIndex(stack, (-Int64(1)))))
        x = __pytra_int(__tuple_0[0])
        y = __pytra_int(__tuple_0[1])
        var candidates: [Any] = __pytra_as_list([])
        let __step_1 = __pytra_int(Int64(1))
        var k = __pytra_int(Int64(0))
        while ((__step_1 >= 0 && k < __pytra_int(Int64(4))) || (__step_1 < 0 && k > __pytra_int(Int64(4)))) {
            let __tuple_2 = __pytra_as_list(__pytra_as_list(__pytra_getIndex(dirs, k)))
            dx = __pytra_int(__tuple_2[0])
            dy = __pytra_int(__tuple_2[1])
            var nx: Any = (x + dx)
            var ny: Any = (y + dy)
            if ((__pytra_int(nx) >= __pytra_int(Int64(1))) && (__pytra_int(nx) < __pytra_int((__pytra_int(cell_w) - __pytra_int(Int64(1))))) && (__pytra_int(ny) >= __pytra_int(Int64(1))) && (__pytra_int(ny) < __pytra_int((__pytra_int(cell_h) - __pytra_int(Int64(1))))) && (__pytra_int(__pytra_int(__pytra_getIndex(__pytra_as_list(__pytra_getIndex(grid, ny)), nx))) == __pytra_int(Int64(1)))) {
                if (__pytra_int(dx) == __pytra_int(Int64(2))) {
                    candidates = __pytra_as_list(candidates); candidates.append([nx, ny, (x + Int64(1)), y])
                } else {
                    if (__pytra_int(dx) == __pytra_int((-Int64(2)))) {
                        candidates = __pytra_as_list(candidates); candidates.append([nx, ny, (x - Int64(1)), y])
                    } else {
                        if (__pytra_int(dy) == __pytra_int(Int64(2))) {
                            candidates = __pytra_as_list(candidates); candidates.append([nx, ny, x, (y + Int64(1))])
                        } else {
                            candidates = __pytra_as_list(candidates); candidates.append([nx, ny, x, (y - Int64(1))])
                        }
                    }
                }
            }
            k += __step_1
        }
        if (__pytra_int(__pytra_len(candidates)) == __pytra_int(Int64(0))) {
            stack = __pytra_pop_last(__pytra_as_list(stack))
        } else {
            var sel: [Any] = __pytra_as_list(__pytra_as_list(__pytra_getIndex(candidates, (__pytra_int((((x * Int64(17)) + (y * Int64(29))) + (__pytra_int(__pytra_len(stack)) * __pytra_int(Int64(13))))) % __pytra_int(__pytra_len(candidates))))))
            let __tuple_3 = __pytra_as_list(sel)
            var nx: Int64 = __pytra_int(__tuple_3[0])
            var ny: Int64 = __pytra_int(__tuple_3[1])
            var wx: Int64 = __pytra_int(__tuple_3[2])
            var wy: Int64 = __pytra_int(__tuple_3[3])
            __pytra_setIndex(__pytra_as_list(__pytra_getIndex(grid, wy)), wx, Int64(0))
            __pytra_setIndex(__pytra_as_list(__pytra_getIndex(grid, ny)), nx, Int64(0))
            stack = __pytra_as_list(stack); stack.append([nx, ny])
        }
        if (__pytra_int((__pytra_int(step) % __pytra_int(capture_every))) == __pytra_int(Int64(0))) {
            frames = __pytra_as_list(frames); frames.append(capture(grid, cell_w, cell_h, scale))
        }
        step += Int64(1)
    }
    frames = __pytra_as_list(frames); frames.append(capture(grid, cell_w, cell_h, scale))
    __pytra_noop(out_path, (__pytra_int(cell_w) * __pytra_int(scale)), (__pytra_int(cell_h) * __pytra_int(scale)), frames, [])
    var elapsed: Double = __pytra_float((__pytra_float(__pytra_perf_counter()) - __pytra_float(start)))
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
