# AUTO-GENERATED FILE. DO NOT EDIT.
# source: src/pytra/built_in/contains.py
# generated-by: tools/gen_runtime_from_manifest.py

require_relative "py_runtime"


def py_contains_dict_object(values, key)
  needle = __pytra_str(key)
  for cur in __pytra_as_list(values)
    if cur == needle
      return true
    end
  end
  return false
end

def py_contains_list_object(values, key)
  for cur in __pytra_as_list(values)
    if cur == key
      return true
    end
  end
  return false
end

def py_contains_set_object(values, key)
  for cur in __pytra_as_list(values)
    if cur == key
      return true
    end
  end
  return false
end

def py_contains_str_object(values, key)
  needle = __pytra_str(key)
  haystack = __pytra_str(values)
  n = __pytra_len(haystack)
  m = __pytra_len(needle)
  if m == 0
    return true
  end
  i = 0
  last = n - m
  while i <= last
    j = 0
    ok = true
    while j < m
      if __pytra_get_index(haystack, i + j) != __pytra_get_index(needle, j)
        ok = false
        break
      end
      j += 1
    end
    if ok
      return true
    end
    i += 1
  end
  return false
end

if __FILE__ == $PROGRAM_NAME
end
