#ifndef PYTRA_BUILT_IN_PY_TYPES_H
#define PYTRA_BUILT_IN_PY_TYPES_H

#include <algorithm>
#include <any>
#include <cctype>
#include <optional>
#include <stdexcept>
#include <string>
#include <tuple>
#include <type_traits>
#include <unordered_map>
#include <unordered_set>
#include <utility>
#include <vector>

#include "py_scalar_types.ext.h"
#include "gc.ext.h"
#include "io.ext.h"

using PyObj = pytra::gc::PyObj;

template <class T>
using rc = pytra::gc::RcHandle<T>;

using object = rc<PyObj>;

template <class T, class... Args>
static inline rc<T> rc_new(Args&&... args) {
    return rc<T>::adopt(pytra::gc::rc_new<T>(::std::forward<Args>(args)...));
}

class str;
class PyListObj;
template <class T> class list;
template <class K, class V> class dict;
str obj_to_str(const object& v);
dict<str, object> obj_to_dict(const object& v);
const dict<str, object>* obj_to_dict_ptr(const object& v);
const list<object>* obj_to_list_ptr(const object& v);
const list<object>* obj_to_set_ptr(const object& v);
template <class T> static inline object make_object(const T& v);
template <class T, class... Args> static inline object object_new(Args&&... args);

#include "str.ext.h"
#include "list.ext.h"
#include "dict.ext.h"
#include "set.ext.h"

template <class T>
struct py_is_rc_list_handle : ::std::false_type {};

template <class T>
struct py_is_rc_list_handle<rc<list<T>>> : ::std::true_type {
    using item_type = T;
};

template <class T>
static inline rc<list<T>> rc_list_new() {
    return rc<list<T>>::adopt(pytra::gc::rc_new<list<T>>());
}

template <class T>
static inline rc<list<T>> rc_list_from_value(list<T> values) {
    return rc<list<T>>::adopt(pytra::gc::rc_new<list<T>>(::std::move(values)));
}

template <class T>
static inline list<T>& rc_list_ref(rc<list<T>>& values) {
    if (!values) {
        throw ::std::runtime_error("rc_list_ref: null list handle");
    }
    return *values;
}

template <class T>
static inline const list<T>& rc_list_ref(const rc<list<T>>& values) {
    if (!values) {
        throw ::std::runtime_error("rc_list_ref: null list handle");
    }
    return *values;
}

template <class T>
static inline list<T> rc_list_copy_value(const rc<list<T>>& values) {
    if (!values) {
        return list<T>{};
    }
    return *values;
}

#endif  // PYTRA_BUILT_IN_PY_TYPES_H
