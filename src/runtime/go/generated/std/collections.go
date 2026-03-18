package main

type dequeLike interface {
    append(value int64)
    appendleft(value int64)
    pop() int64
    popleft() int64
    __len__() int64
    clear()
}


func __pytra_is_deque(v any) bool {
    _, ok := v.(*deque)
    return ok
}

func __pytra_as_deque(v any) *deque {
    if t, ok := v.(*deque); ok {
        return t
    }
    return nil
}

type deque struct {
    _items []any
}

func Newdeque() *deque {
    self := &deque{}
    self.Init()
    return self
}

func (self *deque) Init() {
    self._items = []any{}
}

func (self *deque) append(value int64) {
    self._items = append(self._items, value)
}

func (self *deque) appendleft(value int64) {
    self._items.insert(int64(0), value)
}

func (self *deque) pop() int64 {
    if (__pytra_len(self._items) == int64(0)) {
        panic(__pytra_str(IndexError("pop from empty deque")))
    }
    return __pytra_int(self._items.pop())
}

func (self *deque) popleft() int64 {
    if (__pytra_len(self._items) == int64(0)) {
        panic(__pytra_str(IndexError("pop from empty deque")))
    }
    var item int64 = __pytra_int(__pytra_get_index(self._items, int64(0)))
    self._items = __pytra_slice(self._items, int64(1), __pytra_len(self._items))
    return item
}

func (self *deque) __len__() int64 {
    return __pytra_len(self._items)
}

func (self *deque) clear() {
    self._items = []any{}
}

func main() {
}
