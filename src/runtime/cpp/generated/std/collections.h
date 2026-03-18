// AUTO-GENERATED FILE. DO NOT EDIT.
// source: src/pytra/std/collections.py
// generated-by: src/backends/cpp/cli.py

#ifndef PYTRA_GENERATED_STD_COLLECTIONS_H
#define PYTRA_GENERATED_STD_COLLECTIONS_H

#include "runtime/cpp/native/core/py_runtime.h"

namespace pytra::std::collections {

struct deque;

    struct deque {
        rc<list<int64>> _items;
        
        deque();
        void append(int64 value);
        void appendleft(int64 value);
        int64 pop() const;
        int64 popleft();
        int64 __len__() const;
        void clear();
    };


}  // namespace pytra::std::collections

#endif  // PYTRA_GENERATED_STD_COLLECTIONS_H
