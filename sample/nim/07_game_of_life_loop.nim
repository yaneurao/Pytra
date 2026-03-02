include "py_runtime.nim"

import std/os, std/times, std/tables, std/strutils, std/math

proc next_state*(grid: seq[seq[int]], w: int, h: int): auto =
  var nxt: seq[seq[int]] = @[]
  for y in 0 ..< h:
    var row: seq[int] = @[]
    for x in 0 ..< w:
      var cnt = 0
      for dy in (-1) ..< 2:
        for dx in (-1) ..< 2:
          if py_truthy(((dx != 0) {op} (dy != 0))):
            var nx = py_mod(((x + dx) + w), w)
            var ny = py_mod(((y + dy) + h), h)
            cnt += grid[ny][nx]
      var alive = grid[y][x]
      if py_truthy(((alive == 1) {op} py_truthy(((cnt == 2) {op} (cnt == 3))))):
        row.add(1)
      elif py_truthy(((alive == 0) {op} (cnt == 3))):
        row.add(1)
      else:
        row.add(0)
    nxt.add(row)
  return nxt

proc render*(grid: seq[seq[int]], w: int, h: int, cell: int): auto =
  var width = (w * cell)
  var height = (h * cell)
  var frame = newSeq[uint8]()
  for y in 0 ..< h:
    for x in 0 ..< w:
      var v = /* unknown expr IfExp */
      for yy in 0 ..< cell:
        var base = ((((y * cell) + yy) * width) + (x * cell))
        for xx in 0 ..< cell:
          frame[(base + xx)] = v
  return bytes(frame)

proc run_07_game_of_life_loop*(): auto =
  var w = 144
  var h = 108
  var cell = 4
  var steps = 105
  var out_path = "sample/out/07_game_of_life_loop.gif"
  var start = epochTime()
  var grid: seq[seq[int]] = (block: var res: seq[auto] = @[]; for v in /* unknown expr RangeExpr */: res.add((@[0] * w)); res)
  for y in 0 ..< h:
    for x in 0 ..< w:
      var noise = py_mod(((((x * 37) + (y * 73)) + py_mod((x * y), 19)) + py_mod((x + y), 11)), 97)
      if (noise < 3):
        grid[y][x] = 1
  var glider = @[@[0, 1, 0], @[0, 0, 1], @[1, 1, 1]]
  var r_pentomino = @[@[0, 1, 1], @[1, 1, 0], @[0, 1, 0]]
  var lwss = @[@[0, 1, 1, 1, 1], @[1, 0, 0, 0, 1], @[0, 0, 0, 0, 1], @[1, 0, 0, 1, 0]]
  for gy in 8 ..< (h - 8):
    for gx in 8 ..< (w - 8):
      var kind = py_mod(((gx * 7) + (gy * 11)), 3)
      if (kind == 0):
        var ph = glider.len
        for py in 0 ..< ph:
          var pw = glider[py].len
          for px in 0 ..< pw:
            if (glider[py][px] == 1):
              grid[py_mod((gy + py), h)][py_mod((gx + px), w)] = 1
      elif (kind == 1):
        ph = r_pentomino.len
        for py in 0 ..< ph:
          pw = r_pentomino[py].len
          for px in 0 ..< pw:
            if (r_pentomino[py][px] == 1):
              grid[py_mod((gy + py), h)][py_mod((gx + px), w)] = 1
      else:
        ph = lwss.len
        for py in 0 ..< ph:
          pw = lwss[py].len
          for px in 0 ..< pw:
            if (lwss[py][px] == 1):
              grid[py_mod((gy + py), h)][py_mod((gx + px), w)] = 1
  var frames: seq[auto] = @[]
  for v in 0 ..< steps:
    frames.add(render(grid, w, h, cell))
    grid = next_state(grid, w, h)
  discard save_gif(out_path, (w * cell), (h * cell), frames, grayscale_palette())
  var elapsed = (epochTime() - start)
  echo "output:", out_path
  echo "frames:", steps
  echo "elapsed_sec:", elapsed


if isMainModule:
  run_07_game_of_life_loop()
