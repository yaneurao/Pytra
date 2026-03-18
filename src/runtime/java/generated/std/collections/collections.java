public final class collections {
    private collections() {
    }


    public static class Deque {
        public java.util.ArrayList<Long> _items;

        public Deque() {
            this._items = new java.util.ArrayList<Object>();
        }

        public void append(long value) {
            this._items.add(value);
        }

        public void appendleft(long value) {
            this._items.insert(0L, value);
        }

        public long pop() {
            if (((((long)(this._items.size()))) == (0L))) {
                throw new RuntimeException(PyRuntime.pyToString(new IndexError("pop from empty deque")));
            }
            return this._items.remove(this._items.size() - 1);
        }

        public long popleft() {
            if (((((long)(this._items.size()))) == (0L))) {
                throw new RuntimeException(PyRuntime.pyToString(new IndexError("pop from empty deque")));
            }
            long item = ((Long)(this._items.get((int)((((0L) < 0L) ? (((long)(this._items.size())) + (0L)) : (0L))))));
            this._items = PyRuntime.__pytra_list_slice(this._items, (((1L) < 0L) ? (((long)(this._items.size())) + (1L)) : (1L)), (((((long)(this._items.size()))) < 0L) ? (((long)(this._items.size())) + (((long)(this._items.size())))) : (((long)(this._items.size())))));
            return item;
        }

        public long __len__() {
            return ((long)(this._items.size()));
        }

        public void clear() {
            this._items = new java.util.ArrayList<Object>();
        }
    }

    public static void main(String[] args) {
    }
}
