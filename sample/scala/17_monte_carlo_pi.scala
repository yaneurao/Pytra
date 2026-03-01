// Auto-generated Pytra Scala 3 native source from EAST3.
import scala.collection.mutable
import scala.util.boundary, boundary.break
import scala.math.*
import java.nio.file.{Files, Paths}

def __pytra_perf_counter(): Double = {
    System.nanoTime().toDouble / 1_000_000_000.0
}

def __pytra_int(v: Any): Long = {
    if (v == null) return 0L
    v match {
        case l: Long => l
        case i: Int => i.toLong
        case d: Double => d.toLong
        case f: Float => f.toLong
        case b: Boolean => if (b) 1L else 0L
        case s: String =>
            try s.toLong
            catch { case _: NumberFormatException => 0L }
        case _ => 0L
    }
}

def __pytra_str(v: Any): String = {
    if (v == null) return "None"
    v match {
        case b: Boolean => if (b) "True" else "False"
        case _ => v.toString
    }
}

def __pytra_print(args: Any*): Unit = {
    if (args.isEmpty) {
        println()
        return
    }
    println(args.map(__pytra_str).mkString(" "))
}


// 17: Sample that scans a large grid using integer arithmetic only and computes a checksum.
// It avoids floating-point error effects, making cross-language comparisons easier.

def run_integer_grid_checksum(width: Long, height: Long, seed: Long): Long = {
    var mod_main: Long = 2147483647L
    var mod_out: Long = 1000000007L
    var acc: Long = (seed % mod_out)
    var y: Long = __pytra_int(0L)
    boundary:
        given __breakLabel_0: boundary.Label[Unit] = summon[boundary.Label[Unit]]
        while (y < __pytra_int(height)) {
            boundary:
                given __continueLabel_1: boundary.Label[Unit] = summon[boundary.Label[Unit]]
                var row_sum: Long = 0L
                var x: Long = __pytra_int(0L)
                boundary:
                    given __breakLabel_3: boundary.Label[Unit] = summon[boundary.Label[Unit]]
                    while (x < __pytra_int(width)) {
                        boundary:
                            given __continueLabel_4: boundary.Label[Unit] = summon[boundary.Label[Unit]]
                            var v: Long = ((((x * 37L) + (y * 73L)) + seed) % mod_main)
                            v = (((v * 48271L) + 1L) % mod_main)
                            row_sum += (v % 256L)
                        x += 1L
                    }
                acc = ((acc + (row_sum * (y + 1L))) % mod_out)
            y += 1L
        }
    return acc
}

def run_integer_benchmark(): Unit = {
    var width: Long = 7600L
    var height: Long = 5000L
    var start: Double = __pytra_perf_counter()
    var checksum: Long = __pytra_int(run_integer_grid_checksum(width, height, 123456789L))
    var elapsed: Double = (__pytra_perf_counter() - start)
    __pytra_print("pixels:", (width * height))
    __pytra_print("checksum:", checksum)
    __pytra_print("elapsed_sec:", elapsed)
}

def main(args: Array[String]): Unit = {
    run_integer_benchmark()
}
