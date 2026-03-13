// AUTO-GENERATED FILE. DO NOT EDIT.
// source: src/pytra/std/glob.py
// generated-by: tools/gen_runtime_from_manifest.py

import scala.collection.mutable
import scala.util.boundary, boundary.break
import java.nio.file.{Files, Paths}


def glob(pattern: String): mutable.ArrayBuffer[String] = {
    return __pytra_as_list(__glob.glob(pattern)).asInstanceOf[mutable.ArrayBuffer[String]]
}
