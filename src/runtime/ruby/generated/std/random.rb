# AUTO-GENERATED FILE. DO NOT EDIT.
# source: src/pytra/std/random.py
# generated-by: tools/gen_runtime_from_manifest.py

require_relative "py_runtime"


def seed(value)
  v = value & 2147483647
  if v == 0
    v = 1
  end
  __pytra_set_index(_state_box, 0, v)
  __pytra_set_index(_gauss_has_spare, 0, 0)
end

def _next_u31()
  s = __pytra_get_index(_state_box, 0)
  s = ((1103515245 * s + 12345) & 2147483647)
  __pytra_set_index(_state_box, 0, s)
  return s
end

def random()
  return __pytra_float(_next_u31()) / 2147483648.0
end

def randint(a, b)
  lo = a
  hi = b
  if hi < lo
    __swap_0 = lo
    lo = hi
    hi = __swap_0
  end
  span = (hi - lo + 1)
  return lo + __pytra_int(random() * span)
end

def choices(population, weights, k)
  n = __pytra_len(population)
  if n <= 0
    return []
  end
  draws = k
  if draws < 0
    draws = 0
  end
  weight_vals = []
  for w in __pytra_as_list(weights)
    weight_vals.append(w)
  end
  out = []
  if __pytra_len(weight_vals) == n
    total = 0.0
    for w in __pytra_as_list(weight_vals)
      if w > 0.0
        total += w
      end
    end
    if total > 0.0
      __loop_0 = 0
      while __loop_0 < draws
        r = random() * total
        acc = 0.0
        picked_i = n - 1
        i = 0
        while i < n
          w = __pytra_get_index(weight_vals, i)
          if w > 0.0
            acc += w
          end
          if r < acc
            picked_i = i
            break
          end
          i += 1
        end
        out.append(__pytra_get_index(population, picked_i))
        __loop_0 += 1
      end
      return out
    end
  end
  __loop_1 = 0
  while __loop_1 < draws
    out.append(__pytra_get_index(population, randint(0, n - 1)))
    __loop_1 += 1
  end
  return out
end

def gauss(mu, sigma)
  if __pytra_get_index(_gauss_has_spare, 0) != 0
    __pytra_set_index(_gauss_has_spare, 0, 0)
    return (mu + sigma * __pytra_get_index(_gauss_spare, 0))
  end
  u1 = 0.0
  while u1 <= 1e-12
    u1 = random()
  end
  u2 = random()
  mag = pyMathSqrt(((-2.0) * pyMathLog(u1)))
  z0 = mag * pyMathCos((2.0 * pyMathPi() * u2))
  z1 = mag * pyMathSin((2.0 * pyMathPi() * u2))
  __pytra_set_index(_gauss_spare, 0, z1)
  __pytra_set_index(_gauss_has_spare, 0, 1)
  return (mu + sigma * z0)
end

def shuffle(xs)
  i = __pytra_len(xs) - 1
  while i > 0
    j = randint(0, i)
    if j != i
      tmp = __pytra_get_index(xs, i)
      __pytra_set_index(xs, i, __pytra_get_index(xs, j))
      __pytra_set_index(xs, j, tmp)
    end
    i -= 1
  end
end

if __FILE__ == $PROGRAM_NAME
end
