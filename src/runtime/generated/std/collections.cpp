#include "core/py_runtime.h"
#include "core/process_runtime.h"

/* Pytra collections module — list-based deque implementation.

Provides a deque compatible with all transpilation targets.
Backends with native deque (C++ std::deque, Rust VecDeque, etc.)
can override this with emitter-level optimization.
 */

struct deque {
    rc<list<int64>> _items;
    
    deque() {
        this->_items = rc_list_from_value(list<int64>{});
    }
    void append(int64 value) {
        rc_list_ref(this->_items).append(value);
    }
    void appendleft(int64 value) {
        this->_items.insert(0, value);
    }
    int64 pop() const {
        if ((rc_list_ref(this->_items)).empty())
            throw IndexError("pop from empty deque");
        return rc_list_ref(this->_items).pop();
    }
    int64 popleft() {
        if ((rc_list_ref(this->_items)).empty())
            throw IndexError("pop from empty deque");
        int64 item = py_list_at_ref(rc_list_ref(this->_items), 0);
        this->_items = rc_list_from_value(py_list_slice_copy(rc_list_ref(this->_items), 1, int64(rc_list_ref(this->_items).size())));
        return item;
    }
    int64 __len__() const {
        return (rc_list_ref(this->_items)).size();
    }
    void clear() {
        this->_items = object_new<PyListObj>(list<object>{});
    }
};
