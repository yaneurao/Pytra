import std/os, std/times, std/tables, std/strutils, std/math

# from time import ...
# from pytra.runtime import ...
proc escape_count*(cx: float, cy: float, max_iter: int) =
  x = 0.0 # float
  y = 0.0 # float
  for i in 0 ..< max_iter:
    x2 = (x * x) # float
    y2 = (y * y) # float
    if ((x2 + y2) > 4.0):
      return i
    y = (((2.0 * x) * y) + cy)
    x = ((x2 - y2) + cx)
  return max_iter

proc color_map*(iter_count: int, max_iter: int) =
  if (iter_count >= max_iter):
    return (0, 0, 0)
  t = (iter_count / max_iter) # float
  r = int((255.0 * (t * t))) # int
  g = int((255.0 * t)) # int
  b = int((255.0 * (1.0 - t))) # int
  return (r, g, b)

proc render_mandelbrot*(width: int, height: int, max_iter: int, x_min: float, x_max: float, y_min: float, y_max: float) =
  pixels = newSeq[uint8]() # seq[uint8]
  __hoisted_cast_1 = float((height - 1)) # float
  __hoisted_cast_2 = float((width - 1)) # float
  __hoisted_cast_3 = float(max_iter) # float
  for y in 0 ..< height:
    py = (y_min + ((y_max - y_min) * (y / __hoisted_cast_1))) # float
    for x in 0 ..< width:
      px = (x_min + ((x_max - x_min) * (x / __hoisted_cast_2))) # float
      it = escape_count(px, py, max_iter) # int
      var r: int # local decl
      var g: int # local decl
      var b: int # local decl
      if (it >= max_iter):
        r = 0
        g = 0
        b = 0
      else:
        t = (it / __hoisted_cast_3) # float
        r = int((255.0 * (t * t)))
        g = int((255.0 * t))
        b = int((255.0 * (1.0 - t)))
      discard pixels.add(r)
      discard pixels.add(g)
      discard pixels.add(b)
  return pixels

proc run_mandelbrot*() =
  width = 1600 # int
  height = 1200 # int
  max_iter = 1000 # int
  out_path = "sample/out/01_mandelbrot.png" # string
  start = epochTime() # float
  pixels = render_mandelbrot(width, height, max_iter, (-2.2), 1.0, (-1.2), 1.2) # seq[uint8]
  discard write_rgb_png(out_path, width, height, pixels)
  elapsed = (epochTime() - start) # float
  echo "output:", out_path
  echo "size:", width, "x", height
  echo "max_iter:", max_iter
  echo "elapsed_sec:", elapsed


if isMainModule:
  discard run_mandelbrot()
