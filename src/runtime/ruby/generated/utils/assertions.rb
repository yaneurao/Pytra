# AUTO-GENERATED FILE. DO NOT EDIT.
# source: src/pytra/utils/assertions.py
# generated-by: tools/gen_runtime_from_manifest.py

require_relative "py_runtime"


def _eq_any(actual, expected)
  return (py_to_string(actual) == py_to_string(expected))
  return (actual == expected)
end

def py_assert_true(cond, label)
  if cond
    return true
  end
  if label != ""
    __pytra_print(nil)
  else
    __pytra_print("[assert_true] False")
  end
  return false
end

def py_assert_eq(actual, expected, label)
  ok = _eq_any(actual, expected)
  if ok
    return true
  end
  if label != ""
    __pytra_print(nil)
  else
    __pytra_print(nil)
  end
  return false
end

def py_assert_all(results, label)
  for v in __pytra_as_list(results)
    if !v
      if label != ""
        __pytra_print(nil)
      else
        __pytra_print("[assert_all] False")
      end
      return false
    end
  end
  return true
end

def py_assert_stdout(expected_lines, fn)
  return true
end

if __FILE__ == $PROGRAM_NAME
end
