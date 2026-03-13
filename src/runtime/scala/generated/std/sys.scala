// AUTO-GENERATED FILE. DO NOT EDIT.
// source: src/pytra/std/sys.py
// generated-by: tools/gen_runtime_from_manifest.py

import scala.collection.mutable
import scala.util.boundary, boundary.break
import java.nio.file.{Files, Paths}


def exit(code: Long): Unit = {
    __s.exit(code)
}

def set_argv(values: mutable.ArrayBuffer[String]): Unit = {
    argv.clear()
    val __iter_0 = __pytra_as_list(values)
    var __i_1: Long = 0L
    while (__i_1 < __iter_0.size.toLong) {
        val v: String = __pytra_str(__iter_0(__i_1.toInt))
        argv = __pytra_as_list(argv); argv.append(v)
        __i_1 += 1L
    }
}

def set_path(values: mutable.ArrayBuffer[String]): Unit = {
    path.clear()
    val __iter_0 = __pytra_as_list(values)
    var __i_1: Long = 0L
    while (__i_1 < __iter_0.size.toLong) {
        val v: String = __pytra_str(__iter_0(__i_1.toInt))
        path = __pytra_as_list(path); path.append(v)
        __i_1 += 1L
    }
}

def write_stderr(text: String): Unit = {
    __s.stderr.write(text)
}

def write_stdout(text: String): Unit = {
    __s.stdout.write(text)
}
