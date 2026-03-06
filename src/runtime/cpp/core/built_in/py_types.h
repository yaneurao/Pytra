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

#include "py_scalar_types.h"
#include "gc.h"
#include "io.h"

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

#include "str.h"
#include "list.h"
#include "dict.h"
#include "set.h"

#endif  // PYTRA_BUILT_IN_PY_TYPES_H
