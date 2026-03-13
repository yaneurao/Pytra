// AUTO-GENERATED FILE. DO NOT EDIT.
// source: src/pytra/std/os_path.py
// generated-by: tools/gen_runtime_from_manifest.py

import scala.collection.mutable
import scala.util.boundary, boundary.break
import java.nio.file.{Files, Paths}


def join(a: String, b: String): String = {
    return __pytra_str(__path.join(a, b))
}

def dirname(p: String): String = {
    return __pytra_str(__path.dirname(p))
}

def basename(p: String): String = {
    return __pytra_str(__path.basename(p))
}

def splitext(p: String): mutable.ArrayBuffer[String] = {
    return __pytra_as_list(__path.splitext(p)).asInstanceOf[mutable.ArrayBuffer[String]]
}

def abspath(p: String): String = {
    return __pytra_str(__path.abspath(p))
}

def exists(p: String): Boolean = {
    return __pytra_truthy(__path.exists(p))
}
