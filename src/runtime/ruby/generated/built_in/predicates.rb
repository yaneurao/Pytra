# AUTO-GENERATED FILE. DO NOT EDIT.
# source: src/pytra/built_in/predicates.py
# generated-by: tools/gen_runtime_from_manifest.py

require_relative "py_runtime"


def py_any(values)
  i = 0
  n = __pytra_len(values)
  while i < n
    if __pytra_truthy(__pytra_get_index(values, i))
      return true
    end
    i += 1
  end
  return false
end

def py_all(values)
  i = 0
  n = __pytra_len(values)
  while i < n
    if !__pytra_truthy(__pytra_get_index(values, i))
      return false
    end
    i += 1
  end
  return true
end

if __FILE__ == $PROGRAM_NAME
end
