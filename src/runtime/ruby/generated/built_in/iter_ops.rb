# AUTO-GENERATED FILE. DO NOT EDIT.
# source: src/pytra/built_in/iter_ops.py
# generated-by: tools/gen_runtime_from_manifest.py

require_relative "py_runtime"


def py_reversed_object(values)
  out = []
  for value in __pytra_as_list(values)
    out.append(value)
  end
  return reversed(out)
end

def py_enumerate_object(values, start)
  out = []
  i = start
  for value in __pytra_as_list(values)
    out.append([i, value])
    i += 1
  end
  return out
end

if __FILE__ == $PROGRAM_NAME
end
