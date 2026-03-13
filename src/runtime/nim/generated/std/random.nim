# AUTO-GENERATED FILE. DO NOT EDIT.
# source: src/pytra/std/random.py
# generated-by: tools/gen_runtime_from_manifest.py

include "py_runtime.nim"

import std/os, std/times, std/tables, std/strutils, std/math, std/sequtils

discard "pytra.std.random: minimal deterministic random helpers.\n\nThis module is intentionally self-contained and avoids Python stdlib imports,\nso it can be transpiled to target runtimes.\n"
var vstate_box: seq[int] = @[2463534242]
var vgauss_has_spare: seq[int] = @[0]
var vgauss_spare: seq[float] = @[0.0]
proc seed*(value: int) =
  var v: int = 0
  v = (value and 2147483647)
  if (v == 0):
    v = 1
  vstate_box[0] = v
  vgauss_has_spare[0] = 0

proc vnext_u31*(): auto =
  var s = vstate_box[0]
  s = (((1103515245 * s) + 12345) and 2147483647)
  vstate_box[0] = s
  return s

proc random*(): float =
  return (float(vnext_u31()) / float(2147483648.0))

proc randint*(a: int, b: int): int =
  var hi: int = 0
  var lo: int = 0
  var span: int = 0
  lo = a
  hi = b
  if (hi < lo):
    var __swap_0 = lo
    lo = hi
    hi = __swap_0
  span = ((hi - lo) + 1)
  return (lo + int((float(random()) * float(span))))

proc choices*(population: seq[int], weights: seq[float], k: int): seq[auto] =
  var `out`: seq[int] = @[]
  var acc: float = 0.0
  var draws: int = 0
  var n: int = 0
  var picked_i: int = 0
  var r: float = 0.0
  var total: float = 0.0
  var w: float = 0.0
  var weight_vals: seq[float] = @[]
  n = population.len
  if (n <= 0):
    return @[]
  draws = k
  if (draws < 0):
    draws = 0
  weight_vals = @[] # seq[float]
  for w in weights:
    weight_vals.add(w)
  `out` = @[] # seq[int]
  if (weight_vals.len == n):
    total = 0.0
    for w in weight_vals:
      if (w > 0.0):
        total += w
    if (total > 0.0):
      for v in 0 ..< draws:
        r = (float(random()) * float(total))
        acc = 0.0
        picked_i = (n - 1)
        for i in 0 ..< n:
          w = weight_vals[i]
          if (w > 0.0):
            acc += w
          if (r < acc):
            picked_i = i
            break
        `out`.add(population[picked_i])
      return `out`
  for v in 0 ..< draws:
    `out`.add(population[randint(0, (n - 1))])
  return `out`

proc gauss*(mu: float, sigma: float): float =
  var mag: float = 0.0
  var u1: float = 0.0
  var u2: float = 0.0
  var z0: float = 0.0
  var z1: float = 0.0
  if (vgauss_has_spare[0] != 0):
    vgauss_has_spare[0] = 0
    return (mu + (sigma * vgauss_spare[0]))
  u1 = 0.0
  while (u1 <= 1e-12):
    u1 = random()
  u2 = random()
  mag = math.sqrt(float((float((-2.0)) * float(vmath.log(u1)))))
  z0 = (float(mag) * float(vmath.cos(((2.0 * PI) * u2))))
  z1 = (float(mag) * float(vmath.sin(((2.0 * PI) * u2))))
  vgauss_spare[0] = z1
  vgauss_has_spare[0] = 1
  return (float(mu) + float((float(sigma) * float(z0))))

proc shuffle*(xs: seq[int]) =
  var i: int = 0
  var j: int = 0
  var tmp: int = 0
  i = (xs.len - 1)
  while (i > 0):
    j = randint(0, i)
    if (j != i):
      tmp = xs[i]
      xs[i] = xs[j]
      xs[j] = tmp
    i -= 1
