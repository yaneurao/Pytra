import kotlin.math.*


// 15: Sample that renders wave interference animation and writes a GIF.

fun run_15_wave_interference_loop() {
    var w: Long = __pytra_int(320L)
    var h: Long = __pytra_int(240L)
    var frames_n: Long = __pytra_int(96L)
    var out_path: String = __pytra_str("sample/out/15_wave_interference_loop.gif")
    var start: Double = __pytra_float(__pytra_perf_counter())
    var frames: MutableList<Any?> = __pytra_as_list(mutableListOf<Any?>())
    val __step_0 = __pytra_int(1L)
    var t = __pytra_int(0L)
    while ((__step_0 >= 0L && t < __pytra_int(frames_n)) || (__step_0 < 0L && t > __pytra_int(frames_n))) {
        var frame: MutableList<Any?> = __pytra_as_list(__pytra_bytearray((__pytra_int(w) * __pytra_int(h))))
        var phase: Double = __pytra_float((__pytra_float(t) * __pytra_float(0.12)))
        val __step_1 = __pytra_int(1L)
        var y = __pytra_int(0L)
        while ((__step_1 >= 0L && y < __pytra_int(h)) || (__step_1 < 0L && y > __pytra_int(h))) {
            var row_base: Long = __pytra_int((__pytra_int(y) * __pytra_int(w)))
            val __step_2 = __pytra_int(1L)
            var x = __pytra_int(0L)
            while ((__step_2 >= 0L && x < __pytra_int(w)) || (__step_2 < 0L && x > __pytra_int(w))) {
                var dx: Long = __pytra_int((__pytra_int(x) - __pytra_int(160L)))
                var dy: Long = __pytra_int((__pytra_int(y) - __pytra_int(120L)))
                var v: Double = __pytra_float((((kotlin.math.sin(__pytra_float((__pytra_float((__pytra_float(x) + __pytra_float((__pytra_float(t) * __pytra_float(1.5))))) * __pytra_float(0.045)))) + kotlin.math.sin(__pytra_float((__pytra_float((__pytra_float(y) - __pytra_float((__pytra_float(t) * __pytra_float(1.2))))) * __pytra_float(0.04))))) + kotlin.math.sin(__pytra_float((__pytra_float((__pytra_float((__pytra_int(x) + __pytra_int(y))) * __pytra_float(0.02))) + __pytra_float(phase))))) + kotlin.math.sin(__pytra_float(((kotlin.math.sqrt(__pytra_float((__pytra_int((__pytra_int(dx) * __pytra_int(dx))) + __pytra_int((__pytra_int(dy) * __pytra_int(dy)))))) * 0.08) - (__pytra_float(phase) * __pytra_float(1.3)))))))
                var c: Long = __pytra_int(__pytra_int(((v + 4.0) * (__pytra_float(255.0) / __pytra_float(8.0)))))
                if ((__pytra_int(c) < __pytra_int(0L))) {
                    c = __pytra_int(0L)
                }
                if ((__pytra_int(c) > __pytra_int(255L))) {
                    c = __pytra_int(255L)
                }
                __pytra_set_index(frame, (__pytra_int(row_base) + __pytra_int(x)), c)
                x += __step_2
            }
            y += __step_1
        }
        frames = __pytra_as_list(frames); frames.add(__pytra_bytes(frame))
        t += __step_0
    }
    __pytra_noop(out_path, w, h, frames, mutableListOf<Any?>())
    var elapsed: Double = __pytra_float((__pytra_float(__pytra_perf_counter()) - __pytra_float(start)))
    __pytra_print("output:", out_path)
    __pytra_print("frames:", frames_n)
    __pytra_print("elapsed_sec:", elapsed)
}

fun main(args: Array<String>) {
    run_15_wave_interference_loop()
}
