# AUTO-GENERATED FILE. DO NOT EDIT.
# source: src/pytra/built_in/sequence.py
# generated-by: tools/gen_runtime_from_manifest.py

require_relative "py_runtime"


def py_range(start, stop, step)
  out = []
  if step == 0
    return out
  end
  if step > 0
    i = start
    while i < stop
      out.append(i)
      i += step
    end
  else
    i = start
    while i > stop
      out.append(i)
      i += step
    end
  end
  return out
end

def py_repeat(v, n)
  if n <= 0
    return ""
  end
  out = ""
  i = 0
  while i < n
    out += v
    i += 1
  end
  return out
end

if __FILE__ == $PROGRAM_NAME
end
