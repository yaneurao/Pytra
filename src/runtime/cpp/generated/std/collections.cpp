// AUTO-GENERATED FILE. DO NOT EDIT.
// source: src/pytra/std/collections.py
// generated-by: src/backends/cpp/cli.py
#include "runtime/cpp/native/core/py_runtime.h"

#include "runtime/cpp/generated/std/collections.h"

namespace pytra::std::collections {

    /* Pytra collections module — list-based deque implementation.

Provides a deque compatible with all transpilation targets.
Backends with native deque (C++ std::deque, Rust VecDeque, etc.)
can override this with emitter-level optimization.
 */
    

    deque::deque() {
            this->_items = rc_list_from_value(list<int64>{});
    }

    void deque::append(int64 value) {
            rc_list_ref(this->_items).append(value);
    }

    void deque::appendleft(int64 value) {
            this->_items.insert(0, value);
    }

    int64 deque::pop() const {
            if ((rc_list_ref(this->_items)).empty())
                throw IndexError("pop from empty deque");
            return rc_list_ref(this->_items).pop();
    }

    int64 deque::popleft() {
            if ((rc_list_ref(this->_items)).empty())
                throw IndexError("pop from empty deque");
            int64 item = py_list_at_ref(rc_list_ref(this->_items), 0);
            this->_items = rc_list_from_value(py_list_slice_copy(rc_list_ref(this->_items), 1, int64(rc_list_ref(this->_items).size())));
            return item;
    }

    int64 deque::__len__() const {
            return (rc_list_ref(this->_items)).size();
    }

    void deque::clear() {
            this->_items = object_new<PyListObj>(list<object>{});
    }
    
}  // namespace pytra::std::collections
