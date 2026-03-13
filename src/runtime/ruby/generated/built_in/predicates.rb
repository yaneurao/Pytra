# AUTO-GENERATED FILE. DO NOT EDIT.
# source: src/pytra/built_in/predicates.py
# generated-by: tools/gen_runtime_from_manifest.py

require_relative "py_runtime"


def py_any(values)
  for value in __pytra_as_list(values)
    if __pytra_truthy(value)
      return true
    end
  end
  return false
end

def py_all(values)
  for value in __pytra_as_list(values)
    if !__pytra_truthy(value)
      return false
    end
  end
  return true
end

if __FILE__ == $PROGRAM_NAME
end
