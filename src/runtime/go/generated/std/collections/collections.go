package main

type DequeLike interface {
    append(value int64)
    appendleft(value int64)
    pop() int64
    popleft() int64
    __len__() int64
    clear()
}


func __pytra_is_Deque(v any) bool {
    _, ok := v.(*Deque)
    return ok
}

func __pytra_as_Deque(v any) *Deque {
    if t, ok := v.(*Deque); ok {
        return t
    }
    return nil
}

type Deque struct {
    _items []any
}

func NewDeque() *Deque {
    self := &Deque{}
    self.Init()
    return self
}

func (self *Deque) Init() {
    self._items = []any{}
}

func (self *Deque) append(value int64) {
    self._items = append(self._items, value)
}

func (self *Deque) appendleft(value int64) {
    self._items.insert(int64(0), value)
}

func (self *Deque) pop() int64 {
    if (__pytra_len(self._items) == int64(0)) {
        panic(__pytra_str(IndexError("pop from empty deque")))
    }
    return __pytra_int(self._items.pop())
}

func (self *Deque) popleft() int64 {
    if (__pytra_len(self._items) == int64(0)) {
        panic(__pytra_str(IndexError("pop from empty deque")))
    }
    var item int64 = __pytra_int(__pytra_get_index(self._items, int64(0)))
    self._items = __pytra_slice(self._items, int64(1), __pytra_len(self._items))
    return item
}

func (self *Deque) __len__() int64 {
    return __pytra_len(self._items)
}

func (self *Deque) clear() {
    self._items = []any{}
}

func main() {
}
