# AUTO-GENERATED FILE. DO NOT EDIT.
# source: src/pytra/std/pathlib.py
# generated-by: tools/gen_runtime_from_manifest.py

require_relative "py_runtime"


class Path
  attr_accessor :_value

  def initialize(value)
    self._value = value
  end

  def __str__()
    return self._value
  end

  def __repr__()
    return ("Path(" + self._value + ")")
  end

  def __fspath__()
    return self._value
  end

  def __truediv__(rhs)
    return Path.new(path.join(self._value, rhs))
  end

  def parent()
    parent_txt = path.dirname(self._value)
    if parent_txt == ""
      parent_txt = "."
    end
    return Path.new(parent_txt)
  end

  def parents()
    out = []
    current = path.dirname(self._value)
    while true
      if current == ""
        current = "."
      end
      out.append(Path.new(current))
      next_current = path.dirname(current)
      if next_current == ""
        next_current = "."
      end
      if next_current == current
        break
      end
      current = next_current
    end
    return out
  end

  def name()
    return path.basename(self._value)
  end

  def suffix()
    __tuple_0 = __pytra_as_list(path.splitext(path.basename(self._value)))
    _ = __tuple_0[0]
    ext = __tuple_0[1]
    return ext
  end

  def stem()
    __tuple_0 = __pytra_as_list(path.splitext(path.basename(self._value)))
    root = __tuple_0[0]
    _ = __tuple_0[1]
    return root
  end

  def resolve()
    return Path.new(path.abspath(self._value))
  end

  def exists()
    return path.exists(self._value)
  end

  def mkdir(parents, exist_ok)
    if parents
      os.makedirs(self._value)
      return nil
    end
    if exist_ok && __pytra_truthy(path.exists(self._value))
      return nil
    end
    os.mkdir(self._value)
  end

  def read_text(encoding)
    f = open(self._value, "r")
    return f.read()
    f.close()
  end

  def write_text(text, encoding)
    f = open(self._value, "w")
    return f.write(text)
    f.close()
  end

  def glob(pattern)
    paths = py_glob.glob(path.join(self._value, pattern))
    out = []
    for p in __pytra_as_list(paths)
      out.append(Path.new(p))
    end
    return out
  end

  def cwd()
    return Path.new(os.getcwd())
  end
end

if __FILE__ == $PROGRAM_NAME
end
