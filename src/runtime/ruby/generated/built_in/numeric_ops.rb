# AUTO-GENERATED FILE. DO NOT EDIT.
# source: src/pytra/built_in/numeric_ops.py
# generated-by: tools/gen_runtime_from_manifest.py

require_relative "py_runtime"


def sum(values)
  if __pytra_len(values) == 0
    return 0
  end
  acc = __pytra_get_index(values, 0) - __pytra_get_index(values, 0)
  i = 0
  n = __pytra_len(values)
  while i < n
    acc += __pytra_get_index(values, i)
    i += 1
  end
  return acc
end

def py_min(a, b)
  if a < b
    return a
  end
  return b
end

def py_max(a, b)
  if a > b
    return a
  end
  return b
end

if __FILE__ == $PROGRAM_NAME
end
