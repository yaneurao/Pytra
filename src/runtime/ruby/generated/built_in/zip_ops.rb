# AUTO-GENERATED FILE. DO NOT EDIT.
# source: src/pytra/built_in/zip_ops.py
# generated-by: tools/gen_runtime_from_manifest.py

require_relative "py_runtime"


def zip(lhs, rhs)
  out = []
  i = 0
  n = __pytra_len(lhs)
  if __pytra_len(rhs) < n
    n = __pytra_len(rhs)
  end
  while i < n
    out.append([__pytra_get_index(lhs, i), __pytra_get_index(rhs, i)])
    i += 1
  end
  return out
end

if __FILE__ == $PROGRAM_NAME
end
