# Auto-generated Pytra Ruby native source from EAST3.
# Runtime helpers are provided by py_runtime.rb in the same directory.
require_relative "py_runtime"


# 17: Sample that scans a large grid using integer arithmetic only and computes a checksum.
# It avoids floating-point error effects, making cross-language comparisons easier.

def run_integer_grid_checksum(width, height, seed)
  mod_main = 2147483647
  mod_out = 1000000007
  acc = (seed % mod_out)
  __step_0 = __pytra_int(1)
  y = __pytra_int(0)
  while ((__step_0 >= 0 && y < __pytra_int(height)) || (__step_0 < 0 && y > __pytra_int(height)))
    row_sum = 0
    __step_1 = __pytra_int(1)
    x = __pytra_int(0)
    while ((__step_1 >= 0 && x < __pytra_int(width)) || (__step_1 < 0 && x > __pytra_int(width)))
      v = ((((x * 37) + (y * 73)) + seed) % mod_main)
      v = (((v * 48271) + 1) % mod_main)
      row_sum += (v % 256)
      x += __step_1
    end
    acc = ((acc + (row_sum * (y + 1))) % mod_out)
    y += __step_0
  end
  return acc
end

def run_integer_benchmark()
  width = 7600
  height = 5000
  start = __pytra_perf_counter()
  checksum = run_integer_grid_checksum(width, height, 123456789)
  elapsed = (__pytra_perf_counter() - start)
  __pytra_print("pixels:", (width * height))
  __pytra_print("checksum:", checksum)
  __pytra_print("elapsed_sec:", elapsed)
end

if __FILE__ == $PROGRAM_NAME
  run_integer_benchmark()
end
