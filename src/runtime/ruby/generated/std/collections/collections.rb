require_relative "py_runtime"


class Deque
  attr_accessor :_items

  def initialize()
    self._items = []
  end

  def append(value)
    self._items.append(value)
  end

  def appendleft(value)
    self._items.insert(0, value)
  end

  def pop()
    if __pytra_len(self._items) == 0
      raise RuntimeError, __pytra_str(IndexError("pop from empty deque"))
    end
    return self._items.pop()
  end

  def popleft()
    if __pytra_len(self._items) == 0
      raise RuntimeError, __pytra_str(IndexError("pop from empty deque"))
    end
    item = __pytra_get_index(self._items, 0)
    self._items = __pytra_slice(self._items, 1, __pytra_len(self._items))
    return item
  end

  def __len__()
    return __pytra_len(self._items)
  end

  def clear()
    self._items = []
  end
end

if __FILE__ == $PROGRAM_NAME
end
