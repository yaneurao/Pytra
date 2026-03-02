include "py_runtime.nim"

import std/os, std/times, std/tables, std/strutils, std/math

proc capture*(grid: seq[seq[int]], w: int, h: int, scale: int): auto =
  var width = (w * scale)
  var height = (h * scale)
  var frame = newSeq[uint8]()
  for y in 0 ..< h:
    for x in 0 ..< w:
      var v = /* unknown expr IfExp */
      for yy in 0 ..< scale:
        var base = ((((y * scale) + yy) * width) + (x * scale))
        for xx in 0 ..< scale:
          frame[(base + xx)] = v
  return bytes(frame)

proc run_13_maze_generation_steps*(): auto =
  var cell_w = 89
  var cell_h = 67
  var scale = 5
  var capture_every = 20
  var out_path = "sample/out/13_maze_generation_steps.gif"
  var start = epochTime()
  var grid: seq[seq[int]] = (block: var res: seq[auto] = @[]; for v in /* unknown expr RangeExpr */: res.add((@[1] * cell_w)); res)
  var stack: seq[(int, int)] = @[(1, 1)]
  grid[1][1] = 0
  var dirs: seq[(int, int)] = @[(2, 0), ((-2), 0), (0, 2), (0, (-2))]
  var frames: seq[auto] = @[]
  var step = 0
  while py_truthy(stack):
    (x, y) = stack[(-1)]
    var candidates: seq[(int, int, int, int)] = @[]
    for k in 0 ..< 4:
      (dx, dy) = dirs[k]
      var nx = (x + dx)
      var ny = (y + dy)
      if py_truthy(((nx >= 1) {op} (nx < (cell_w - 1)) {op} (ny >= 1) {op} (ny < (cell_h - 1)) {op} (grid[ny][nx] == 1))):
        if (dx == 2):
          candidates.add((nx, ny, (x + 1), y))
        elif (dx == (-2)):
          candidates.add((nx, ny, (x - 1), y))
        elif (dy == 2):
          candidates.add((nx, ny, x, (y + 1)))
        else:
          candidates.add((nx, ny, x, (y - 1)))
    if (candidates.len == 0):
      discard stack.pop()
    else:
      var sel = candidates[py_mod((((x * 17) + (y * 29)) + (stack.len * 13)), candidates.len)]
      (nx, ny, wx, wy) = sel
      grid[wy][wx] = 0
      grid[ny][nx] = 0
      stack.add((nx, ny))
    if (py_mod(step, capture_every) == 0):
      frames.add(capture(grid, cell_w, cell_h, scale))
    step += 1
  frames.add(capture(grid, cell_w, cell_h, scale))
  discard save_gif(out_path, (cell_w * scale), (cell_h * scale), frames, grayscale_palette())
  var elapsed = (epochTime() - start)
  echo "output:", out_path
  echo "frames:", frames.len
  echo "elapsed_sec:", elapsed


if isMainModule:
  run_13_maze_generation_steps()
