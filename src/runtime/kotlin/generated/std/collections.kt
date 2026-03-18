

fun __pytra_is_deque(v: Any?): Boolean {
    return v is deque
}

fun __pytra_as_deque(v: Any?): deque {
    return if (v is deque) v else deque()
}

open class deque() {
    var _items: MutableList<Any?> = mutableListOf()

    init {
        this._items = mutableListOf<Any?>()
    }

    open fun append(value: Long) {
        this._items = __pytra_as_list(this._items); this._items.add(value)
    }

    open fun appendleft(value: Long) {
        this._items.insert(0L, value)
    }

    open fun pop(): Long {
        if ((__pytra_int(__pytra_len(this._items)) == __pytra_int(0L))) {
            throw RuntimeException(__pytra_str(IndexError("pop from empty deque")))
        }
        return __pytra_int(this._items.pop())
    }

    open fun popleft(): Long {
        if ((__pytra_int(__pytra_len(this._items)) == __pytra_int(0L))) {
            throw RuntimeException(__pytra_str(IndexError("pop from empty deque")))
        }
        var item: Long = __pytra_int(__pytra_get_index(this._items, 0L))
        this._items = __pytra_slice(this._items, 1L, __pytra_len(this._items))
        return item
    }

    open fun __len__(): Long {
        return __pytra_len(this._items)
    }

    open fun clear() {
        this._items = mutableListOf<Any?>()
    }
}

fun main(args: Array<String>) {
}
