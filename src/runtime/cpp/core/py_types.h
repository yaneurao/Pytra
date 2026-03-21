#ifndef PYTRA_BUILT_IN_PY_TYPES_H
#define PYTRA_BUILT_IN_PY_TYPES_H

#include <algorithm>
#include <any>
#include <cctype>
#include <deque>
#include <optional>
#include <stdexcept>
#include <string>
#include <tuple>
#include <type_traits>
#include <unordered_map>
#include <unordered_set>
#include <utility>
#include <variant>
#include <vector>

#include "core/py_scalar_types.h"
#include "core/gc.h"
#include "core/io.h"

using RcObject = pytra::gc::RcObject;

template <class T>
using rc = pytra::gc::RcHandle<T>;

// Forward declarations needed by object.
template <class T, pytra_type_id TID> struct PyBoxed;
class str;

// object: tagged value = type_id + boxed data.
// All tagged unions, Any, and dynamic values use this single type.
struct object {
    pytra_type_id tag;
    rc<RcObject> _rc;

    object() : tag(PYTRA_TID_NONE), _rc() {}

    // From rc<RcObject> (backward compat)
    object(const rc<RcObject>& v) : tag(v ? v->py_type_id() : PYTRA_TID_NONE), _rc(v) {}
    object(rc<RcObject>&& v) : tag(v ? v->py_type_id() : PYTRA_TID_NONE), _rc(::std::move(v)) {}

    // From raw pointer (adopt)
    object(RcObject* raw) : tag(raw ? raw->py_type_id() : PYTRA_TID_NONE), _rc(rc<RcObject>::adopt(raw)) {}

    // Implicit box for POD types
    object(const str& v);   // defined after str is complete
    object(const char* v);  // defined after str is complete
    object(int64 v);
    object(int v);
    explicit object(float64 v);
    explicit object(bool v);

    // From rc<T> (class upcast)
    template <class T, ::std::enable_if_t<::std::is_base_of_v<RcObject, T>, int> = 0>
    object(const rc<T>& v) : tag(v ? v->py_type_id() : PYTRA_TID_NONE), _rc(v) {}

    // monostate = None
    object(::std::monostate) : tag(PYTRA_TID_NONE), _rc() {}

    // Backward compat: implicit conversion to rc<RcObject>
    operator const rc<RcObject>&() const { return _rc; }
    operator rc<RcObject>&() { return _rc; }

    // rc<RcObject> interface delegation
    RcObject* get() const { return _rc.get(); }
    RcObject& operator*() const { return *_rc; }
    RcObject* operator->() const { return _rc.get(); }
    explicit operator bool() const { return tag != PYTRA_TID_NONE && _rc.get() != nullptr; }

    // Tagged value API
    bool is(pytra_type_id expected) const { return tag == expected; }

    template <class T, pytra_type_id TID>
    const T& unbox() const { return static_cast<PyBoxed<T, TID>*>(_rc.get())->value; }

    template <class T>
    T* as_ptr() const { return static_cast<T*>(_rc.get()); }

    template <class T>
    rc<T> as() const {
        T* raw = static_cast<T*>(_rc.get());
        if (raw) pytra::gc::incref(reinterpret_cast<RcObject*>(raw));
        return rc<T>::adopt(raw);
    }
};

template <class T, class... Args>
static inline rc<T> rc_new(Args&&... args) {
    return rc<T>::adopt(pytra::gc::rc_new<T>(::std::forward<Args>(args)...));
}

class str;
template <class T> class list;
template <class K, class V> class dict;

#include "core/str.h"
#include "core/list.h"
#include "core/dict.h"
#include "core/set.h"

template <class T>
struct py_is_rc_list_handle : ::std::false_type {};

template <class T>
struct py_is_rc_list_handle<rc<list<T>>> : ::std::true_type {
    using item_type = T;
};

// Legacy rc<list<T>> overloads (backward compat during migration).
template <class T>
static inline list<T>& rc_list_ref(rc<list<T>>& values) {
    if (!values) throw ::std::runtime_error("rc_list_ref: null list handle");
    return *values;
}

template <class T>
static inline const list<T>& rc_list_ref(const rc<list<T>>& values) {
    if (!values) throw ::std::runtime_error("rc_list_ref: null list handle");
    return *values;
}

// Object<T> support — include after list/dict/set are complete.
#include "core/object.h"

// Object<list<T>> based list helpers (requires Object<T> to be defined).

template <class T>
static inline Object<list<T>> rc_list_new() {
    return make_object<list<T>>(PYTRA_TID_LIST);
}

template <class T>
static inline Object<list<T>> rc_list_from_value(list<T> values) {
    return make_object<list<T>>(PYTRA_TID_LIST, ::std::move(values));
}

template <class T>
static inline list<T>& rc_list_ref(Object<list<T>>& values) {
    return *values;
}

template <class T>
static inline const list<T>& rc_list_ref(const Object<list<T>>& values) {
    return *values;
}

template <class T>
static inline list<T> rc_list_copy_value(const Object<list<T>>& values) {
    if (!values) {
        return list<T>{};
    }
    return *values;
}

#endif  // PYTRA_BUILT_IN_PY_TYPES_H
