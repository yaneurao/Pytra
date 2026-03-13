# AUTO-GENERATED FILE. DO NOT EDIT.
# source: src/pytra/built_in/iter_ops.py
# generated-by: tools/gen_runtime_from_manifest.py

require_relative "py_runtime"


def py_reversed_object(values)
  out = []
  i = (__pytra_len(values) - 1)
  while i >= 0
    out.append(__pytra_get_index(values, i))
    i -= 1
  end
  return out
end

def py_enumerate_object(values, start)
  out = []
  i = 0
  n = __pytra_len(values)
  while i < n
    out.append([start + i, __pytra_get_index(values, i)])
    i += 1
  end
  return out
end

if __FILE__ == $PROGRAM_NAME
end
