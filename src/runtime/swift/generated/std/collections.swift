import Foundation


func __pytra_is_deque(_ v: Any?) -> Bool {
    return v is deque
}

class deque {
    var _items: [Any] = []

    init() {
        self._items = []
    }

    func append(_ value: Int64) {
        self._items = __pytra_as_list(self._items); self._items.append(value)
    }

    func appendleft(_ value: Int64) {
        self._items.insert(Int64(0), value)
    }

    func pop() -> Int64 {
        if (__pytra_int(__pytra_len(self._items)) == __pytra_int(Int64(0))) {
            fatalError("pytra raise")
        }
        return __pytra_int(self._items.pop())
    }

    func popleft() -> Int64 {
        if (__pytra_int(__pytra_len(self._items)) == __pytra_int(Int64(0))) {
            fatalError("pytra raise")
        }
        var item: Int64 = __pytra_int(__pytra_getIndex(self._items, Int64(0)))
        self._items = __pytra_slice(self._items, Int64(1), __pytra_len(self._items))
        return item
    }

    func __len__() -> Int64 {
        return __pytra_len(self._items)
    }

    func clear() {
        self._items = []
    }
}

@main
struct Main {
    static func main() {
    }
}
