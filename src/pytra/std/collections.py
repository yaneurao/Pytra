"""Pytra collections module — list-based deque implementation.

Provides a deque compatible with all transpilation targets.
Backends with native deque (C++ std::deque, Rust VecDeque, etc.)
can override this with emitter-level optimization.
"""



class deque:
    """Double-ended queue backed by a list."""

    _items: list[int]

    def __init__(self) -> None:
        self._items: list[int] = []

    def append(self, value: int) -> None:
        self._items.append(value)

    def appendleft(self, value: int) -> None:
        self._items.insert(0, value)

    def pop(self) -> int:
        if len(self._items) == 0:
            raise IndexError("pop from empty deque")
        return self._items.pop()

    def popleft(self) -> int:
        if len(self._items) == 0:
            raise IndexError("pop from empty deque")
        item: int = self._items[0]
        self._items = self._items[1:]
        return item

    def __len__(self) -> int:
        return len(self._items)

    def clear(self) -> None:
        self._items = []
