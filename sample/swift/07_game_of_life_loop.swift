// Auto-generated Pytra Swift native source from EAST3.
import Foundation

func __pytra_noop(_ args: Any...) {}

func __pytra_any_default() -> Any {
    return Int64(0)
}

func __pytra_assert(_ args: Any...) -> String {
    _ = args
    return "True"
}

func __pytra_perf_counter() -> Double {
    return Date().timeIntervalSince1970
}

func __pytra_truthy(_ v: Any?) -> Bool {
    guard let value = v else { return false }
    if let b = value as? Bool { return b }
    if let i = value as? Int64 { return i != 0 }
    if let i = value as? Int { return i != 0 }
    if let d = value as? Double { return d != 0.0 }
    if let s = value as? String { return s != "" }
    if let a = value as? [Any] { return !a.isEmpty }
    if let m = value as? [AnyHashable: Any] { return !m.isEmpty }
    return true
}

func __pytra_int(_ v: Any?) -> Int64 {
    guard let value = v else { return 0 }
    if let i = value as? Int64 { return i }
    if let i = value as? Int { return Int64(i) }
    if let d = value as? Double { return Int64(d) }
    if let b = value as? Bool { return b ? 1 : 0 }
    if let s = value as? String { return Int64(s) ?? 0 }
    return 0
}

func __pytra_float(_ v: Any?) -> Double {
    guard let value = v else { return 0.0 }
    if let d = value as? Double { return d }
    if let f = value as? Float { return Double(f) }
    if let i = value as? Int64 { return Double(i) }
    if let i = value as? Int { return Double(i) }
    if let b = value as? Bool { return b ? 1.0 : 0.0 }
    if let s = value as? String { return Double(s) ?? 0.0 }
    return 0.0
}

func __pytra_str(_ v: Any?) -> String {
    guard let value = v else { return "" }
    if let s = value as? String { return s }
    return String(describing: value)
}

func __pytra_len(_ v: Any?) -> Int64 {
    guard let value = v else { return 0 }
    if let s = value as? String { return Int64(s.count) }
    if let a = value as? [Any] { return Int64(a.count) }
    if let m = value as? [AnyHashable: Any] { return Int64(m.count) }
    return 0
}

func __pytra_index(_ i: Int64, _ n: Int64) -> Int64 {
    if i < 0 {
        return i + n
    }
    return i
}

func __pytra_getIndex(_ container: Any?, _ index: Any?) -> Any {
    if let list = container as? [Any] {
        if list.isEmpty { return __pytra_any_default() }
        let i = __pytra_index(__pytra_int(index), Int64(list.count))
        if i < 0 || i >= Int64(list.count) { return __pytra_any_default() }
        return list[Int(i)]
    }
    if let dict = container as? [AnyHashable: Any] {
        let key = AnyHashable(__pytra_str(index))
        return dict[key] ?? __pytra_any_default()
    }
    if let s = container as? String {
        let chars = Array(s)
        if chars.isEmpty { return "" }
        let i = __pytra_index(__pytra_int(index), Int64(chars.count))
        if i < 0 || i >= Int64(chars.count) { return "" }
        return String(chars[Int(i)])
    }
    return __pytra_any_default()
}

func __pytra_setIndex(_ container: Any?, _ index: Any?, _ value: Any?) {
    if var list = container as? [Any] {
        if list.isEmpty { return }
        let i = __pytra_index(__pytra_int(index), Int64(list.count))
        if i < 0 || i >= Int64(list.count) { return }
        list[Int(i)] = value as Any
        return
    }
    if var dict = container as? [AnyHashable: Any] {
        let key = AnyHashable(__pytra_str(index))
        dict[key] = value
    }
}

func __pytra_slice(_ container: Any?, _ lower: Any?, _ upper: Any?) -> Any {
    if let s = container as? String {
        let chars = Array(s)
        let n = Int64(chars.count)
        var lo = __pytra_index(__pytra_int(lower), n)
        var hi = __pytra_index(__pytra_int(upper), n)
        if lo < 0 { lo = 0 }
        if hi < 0 { hi = 0 }
        if lo > n { lo = n }
        if hi > n { hi = n }
        if hi < lo { hi = lo }
        if lo >= hi { return "" }
        return String(chars[Int(lo)..<Int(hi)])
    }
    if let list = container as? [Any] {
        let n = Int64(list.count)
        var lo = __pytra_index(__pytra_int(lower), n)
        var hi = __pytra_index(__pytra_int(upper), n)
        if lo < 0 { lo = 0 }
        if hi < 0 { hi = 0 }
        if lo > n { lo = n }
        if hi > n { hi = n }
        if hi < lo { hi = lo }
        if lo >= hi { return [Any]() }
        return Array(list[Int(lo)..<Int(hi)])
    }
    return __pytra_any_default()
}

func __pytra_isdigit(_ v: Any?) -> Bool {
    let s = __pytra_str(v)
    if s.isEmpty { return false }
    return s.unicodeScalars.allSatisfy { CharacterSet.decimalDigits.contains($0) }
}

func __pytra_isalpha(_ v: Any?) -> Bool {
    let s = __pytra_str(v)
    if s.isEmpty { return false }
    return s.unicodeScalars.allSatisfy { CharacterSet.letters.contains($0) }
}

func __pytra_contains(_ container: Any?, _ value: Any?) -> Bool {
    if let list = container as? [Any] {
        let needle = __pytra_str(value)
        for item in list {
            if __pytra_str(item) == needle {
                return true
            }
        }
        return false
    }
    if let dict = container as? [AnyHashable: Any] {
        return dict[AnyHashable(__pytra_str(value))] != nil
    }
    if let s = container as? String {
        let needle = __pytra_str(value)
        return s.contains(needle)
    }
    return false
}

func __pytra_ifexp(_ cond: Bool, _ a: Any, _ b: Any) -> Any {
    return cond ? a : b
}

func __pytra_bytearray(_ initValue: Any?) -> [Any] {
    if let i = initValue as? Int64 {
        return Array(repeating: Int64(0), count: max(0, Int(i)))
    }
    if let i = initValue as? Int {
        return Array(repeating: Int64(0), count: max(0, i))
    }
    if let arr = initValue as? [Any] {
        return arr
    }
    return []
}

func __pytra_bytes(_ v: Any?) -> [Any] {
    if let arr = v as? [Any] {
        return arr
    }
    return []
}

func __pytra_list_repeat(_ value: Any, _ count: Any?) -> [Any] {
    var out: [Any] = []
    var i: Int64 = 0
    let n = __pytra_int(count)
    while i < n {
        out.append(value)
        i += 1
    }
    return out
}

func __pytra_as_list(_ v: Any?) -> [Any] {
    if let arr = v as? [Any] { return arr }
    return []
}

func __pytra_as_u8_list(_ v: Any?) -> [UInt8] {
    if let arr = v as? [UInt8] { return arr }
    return []
}

func __pytra_as_dict(_ v: Any?) -> [AnyHashable: Any] {
    if let dict = v as? [AnyHashable: Any] { return dict }
    return [:]
}

func __pytra_pop_last(_ v: [Any]) -> [Any] {
    if v.isEmpty { return v }
    return Array(v.dropLast())
}

func __pytra_print(_ args: Any...) {
    if args.isEmpty {
        Swift.print()
        return
    }
    Swift.print(args.map { String(describing: $0) }.joined(separator: " "))
}

func __pytra_min(_ a: Any?, _ b: Any?) -> Any {
    let af = __pytra_float(a)
    let bf = __pytra_float(b)
    if af < bf {
        if __pytra_is_float(a) || __pytra_is_float(b) { return af }
        return __pytra_int(a)
    }
    if __pytra_is_float(a) || __pytra_is_float(b) { return bf }
    return __pytra_int(b)
}

func __pytra_max(_ a: Any?, _ b: Any?) -> Any {
    let af = __pytra_float(a)
    let bf = __pytra_float(b)
    if af > bf {
        if __pytra_is_float(a) || __pytra_is_float(b) { return af }
        return __pytra_int(a)
    }
    if __pytra_is_float(a) || __pytra_is_float(b) { return bf }
    return __pytra_int(b)
}

func __pytra_is_int(_ v: Any?) -> Bool {
    return (v is Int) || (v is Int64)
}

func __pytra_is_float(_ v: Any?) -> Bool {
    return v is Double
}

func __pytra_is_bool(_ v: Any?) -> Bool {
    return v is Bool
}

func __pytra_is_str(_ v: Any?) -> Bool {
    return v is String
}

func __pytra_is_list(_ v: Any?) -> Bool {
    return v is [Any]
}

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
    var elapsed: Double = __pytra_float((__pytra_perf_counter() - start))
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
