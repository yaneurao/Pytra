import kotlin.math.*


// 15: Sample that renders wave interference animation and writes a GIF.

fun run_15_wave_interference_loop() {
    var w: Long = 320L
    var h: Long = 240L
    var frames_n: Long = 96L
    var out_path: String = "sample/out/15_wave_interference_loop.gif"
    var start: Double = __pytra_perf_counter()
    var frames: MutableList<Any?> = __pytra_as_list(mutableListOf<Any?>())
    var t = __pytra_int(0L)
    while (t < __pytra_int(frames_n)) {
        var frame: MutableList<Any?> = __pytra_as_list(__pytra_bytearray((w * h)))
        var phase: Double = (__pytra_float(t) * 0.12)
        var y = __pytra_int(0L)
        while (y < __pytra_int(h)) {
            var row_base: Long = (y * w)
            var x = __pytra_int(0L)
            while (x < __pytra_int(w)) {
                var dx: Long = (x - 160L)
                var dy: Long = (y - 120L)
                var v: Double = __pytra_float(((kotlin.math.sin(__pytra_float((__pytra_float(x) + (__pytra_float(t) * 1.5)) * 0.045)) + kotlin.math.sin(__pytra_float((__pytra_float(y) - (__pytra_float(t) * 1.2)) * 0.04))) + kotlin.math.sin(__pytra_float((__pytra_float(x + y) * 0.02) + phase))) + kotlin.math.sin(__pytra_float((kotlin.math.sqrt(__pytra_float((dx * dx) + (dy * dy))) * 0.08) - (phase * 1.3))))
                var c: Long = __pytra_int((v + 4.0) * (255.0 / 8.0))
                if ((__pytra_int(c) < __pytra_int(0L))) {
                    c = 0L
                }
                if ((__pytra_int(c) > __pytra_int(255L))) {
                    c = 255L
                }
                __pytra_set_index(frame, (row_base + x), c)
                x += 1L
            }
            y += 1L
        }
        frames.add(__pytra_bytes(frame))
        t += 1L
    }
    __pytra_noop(out_path, w, h, frames, mutableListOf<Any?>())
    var elapsed: Double = (__pytra_perf_counter() - start)
    __pytra_print("output:", out_path)
    __pytra_print("frames:", frames_n)
    __pytra_print("elapsed_sec:", elapsed)
}

fun main(args: Array<String>) {
    run_15_wave_interference_loop()
}
