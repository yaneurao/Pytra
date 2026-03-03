require_relative "py_runtime"


# 17: Sample that scans a large grid using integer arithmetic only and computes a checksum.
# It avoids floating-point error effects, making cross-language comparisons easier.

def run_integer_grid_checksum(width, height, seed)
  mod_main = 2147483647
  mod_out = 1000000007
  acc = seed % mod_out
  y = 0
  while y < height
    row_sum = 0
    x = 0
    while x < width
      v = (((x * 37 + y * 73) + seed) % mod_main)
      v = ((v * 48271 + 1) % mod_main)
      row_sum += v % 256
      x += 1
    end
    acc = ((acc + (row_sum * (y + 1))) % mod_out)
    y += 1
  end
  return acc
end

def run_integer_benchmark()
  width = 7600
  height = 5000
  start = __pytra_perf_counter()
  checksum = run_integer_grid_checksum(width, height, 123456789)
  elapsed = __pytra_perf_counter() - start
  __pytra_print("pixels:", width * height)
  __pytra_print("checksum:", checksum)
  __pytra_print("elapsed_sec:", elapsed)
end

if __FILE__ == $PROGRAM_NAME
  run_integer_benchmark()
end
