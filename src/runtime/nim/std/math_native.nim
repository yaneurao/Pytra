# Native implementation of pytra.std.math for Nim.
#
# This file is copied over the linker-generated math/east.nim at emit time.
# The generated module body references the Python `math` module which is
# invalid in Nim; this native seam re-exports std/math and adds pi/e constants.
#
# source: src/pytra/std/math.py

import std/math
export math

let pi* = PI
let e* = E

# fabs is not in std/math; delegate to abs.
proc fabs*(x: float): float = abs(x)
