# AUTO-GENERATED FILE. DO NOT EDIT.
# source: src/pytra/built_in/string_ops.py
# generated-by: tools/gen_runtime_from_manifest.py

require_relative "py_runtime"


def _is_space(ch)
  return ((ch == " ") || (ch == "	") || (ch == "\n") || (ch == ""))
end

def _contains_char(chars, ch)
  i = 0
  n = __pytra_len(chars)
  while i < n
    if __pytra_get_index(chars, i) == ch
      return true
    end
    i += 1
  end
  return false
end

def _normalize_index(idx, n)
  out = idx
  if out < 0
    out += n
  end
  if out < 0
    out = 0
  end
  if out > n
    out = n
  end
  return out
end

def py_join(sep, parts)
  n = __pytra_len(parts)
  if n == 0
    return ""
  end
  out = ""
  i = 0
  while i < n
    if i > 0
      out += sep
    end
    out += __pytra_get_index(parts, i)
    i += 1
  end
  return out
end

def py_split(s, sep, maxsplit)
  out = []
  if sep == ""
    out.append(s)
    return out
  end
  pos = 0
  splits = 0
  n = __pytra_len(s)
  m = __pytra_len(sep)
  unlimited = (maxsplit < 0)
  while true
    if (!unlimited) && (splits >= maxsplit)
      break
    end
    at = py_find_window(s, sep, pos, n)
    if at < 0
      break
    end
    out.append(__pytra_slice(s, pos, at))
    pos = at + m
    splits += 1
  end
  out.append(__pytra_slice(s, pos, n))
  return out
end

def py_splitlines(s)
  out = []
  n = __pytra_len(s)
  start = 0
  i = 0
  while i < n
    ch = __pytra_get_index(s, i)
    if (ch == "\n") || (ch == "")
      out.append(__pytra_slice(s, start, i))
      if (ch == "") && (i + 1 < n) && (__pytra_get_index(s, i + 1) == "\n")
        i += 1
      end
      i += 1
      start = i
      next
    end
    i += 1
  end
  if start < n
    out.append(__pytra_slice(s, start, n))
  else
    if n > 0
      last = __pytra_get_index(s, n - 1)
      if (last == "\n") || (last == "")
        out.append("")
      end
    end
  end
  return out
end

def py_count(s, needle)
  if needle == ""
    return __pytra_len(s) + 1
  end
  out = 0
  pos = 0
  n = __pytra_len(s)
  m = __pytra_len(needle)
  while true
    at = py_find_window(s, needle, pos, n)
    if at < 0
      return out
    end
    out += 1
    pos = at + m
  end
end

def py_lstrip(s)
  i = 0
  n = __pytra_len(s)
  while (i < n) && _is_space(__pytra_get_index(s, i))
    i += 1
  end
  return __pytra_slice(s, i, n)
end

def py_lstrip_chars(s, chars)
  i = 0
  n = __pytra_len(s)
  while (i < n) && _contains_char(chars, __pytra_get_index(s, i))
    i += 1
  end
  return __pytra_slice(s, i, n)
end

def py_rstrip(s)
  n = __pytra_len(s)
  i = n - 1
  while (i >= 0) && _is_space(__pytra_get_index(s, i))
    i -= 1
  end
  return __pytra_slice(s, 0, i + 1)
end

def py_rstrip_chars(s, chars)
  n = __pytra_len(s)
  i = n - 1
  while (i >= 0) && _contains_char(chars, __pytra_get_index(s, i))
    i -= 1
  end
  return __pytra_slice(s, 0, i + 1)
end

def py_strip(s)
  return py_rstrip(py_lstrip(s))
end

def py_strip_chars(s, chars)
  return py_rstrip_chars(py_lstrip_chars(s, chars), chars)
end

def py_startswith(s, prefix)
  n = __pytra_len(s)
  m = __pytra_len(prefix)
  if m > n
    return false
  end
  i = 0
  while i < m
    if __pytra_get_index(s, i) != __pytra_get_index(prefix, i)
      return false
    end
    i += 1
  end
  return true
end

def py_endswith(s, suffix)
  n = __pytra_len(s)
  m = __pytra_len(suffix)
  if m > n
    return false
  end
  i = 0
  base = n - m
  while i < m
    if __pytra_get_index(s, base + i) != __pytra_get_index(suffix, i)
      return false
    end
    i += 1
  end
  return true
end

def py_find(s, needle)
  return py_find_window(s, needle, 0, __pytra_len(s))
end

def py_find_window(s, needle, start, end_)
  n = __pytra_len(s)
  m = __pytra_len(needle)
  lo = _normalize_index(start, n)
  up = _normalize_index(end_, n)
  if up < lo
    return (-1)
  end
  if m == 0
    return lo
  end
  i = lo
  last = up - m
  while i <= last
    j = 0
    ok = true
    while j < m
      if __pytra_get_index(s, i + j) != __pytra_get_index(needle, j)
        ok = false
        break
      end
      j += 1
    end
    if ok
      return i
    end
    i += 1
  end
  return (-1)
end

def py_rfind(s, needle)
  return py_rfind_window(s, needle, 0, __pytra_len(s))
end

def py_rfind_window(s, needle, start, end_)
  n = __pytra_len(s)
  m = __pytra_len(needle)
  lo = _normalize_index(start, n)
  up = _normalize_index(end_, n)
  if up < lo
    return (-1)
  end
  if m == 0
    return up
  end
  i = up - m
  while i >= lo
    j = 0
    ok = true
    while j < m
      if __pytra_get_index(s, i + j) != __pytra_get_index(needle, j)
        ok = false
        break
      end
      j += 1
    end
    if ok
      return i
    end
    i -= 1
  end
  return (-1)
end

def py_replace(s, oldv, newv)
  if oldv == ""
    return s
  end
  out = ""
  n = __pytra_len(s)
  m = __pytra_len(oldv)
  i = 0
  while i < n
    if (i + m <= n) && (py_find_window(s, oldv, i, i + m) == i)
      out += newv
      i += m
    else
      out += __pytra_get_index(s, i)
      i += 1
    end
  end
  return out
end

if __FILE__ == $PROGRAM_NAME
end
