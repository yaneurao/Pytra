# Nim runtime for Pytra
import std/os
import std/times

proc py_perf_counter*(): float =
  epochTime()

proc echo_print*(args: varargs[string, `$`]) =
  echo args.join(" ")
