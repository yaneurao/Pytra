import scala.collection.mutable
import scala.util.boundary, boundary.break
import java.nio.file.{Files, Paths}


def __pytra_is_deque(v: Any): Boolean = {
    v.isInstanceOf[deque]
}

def __pytra_as_deque(v: Any): deque = {
    v match {
        case obj: deque => obj
        case _ => new deque()
    }
}

class deque() {
    var _items: mutable.ArrayBuffer[Long] = mutable.ArrayBuffer[Long]()

    def __init__(): Unit = {
        this._items = mutable.ArrayBuffer[Any]()
    }

    def append(value: Long): Unit = {
        this._items = __pytra_as_list(this._items); this._items.append(value)
    }

    def appendleft(value: Long): Unit = {
        this._items.insert(0L, value)
    }

    def pop(): Long = {
        if (__pytra_len(this._items) == 0L) {
            throw new RuntimeException(__pytra_str(IndexError("pop from empty deque")))
        }
        return __pytra_int(this._items.pop())
    }

    def popleft(): Long = {
        if (__pytra_len(this._items) == 0L) {
            throw new RuntimeException(__pytra_str(IndexError("pop from empty deque")))
        }
        var item: Long = __pytra_int(__pytra_get_index(this._items, 0L))
        this._items = __pytra_slice(this._items, 1L, __pytra_len(this._items))
        return item
    }

    def __len__(): Long = {
        return __pytra_len(this._items)
    }

    def clear(): Unit = {
        this._items = mutable.ArrayBuffer[Any]()
    }
}

def main(args: Array[String]): Unit = {
}