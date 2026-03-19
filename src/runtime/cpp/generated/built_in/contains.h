// AUTO-GENERATED FILE. DO NOT EDIT.
// source: src/pytra/built_in/contains.py
// generated-by: tools/gen_runtime_from_manifest.py

#ifndef PYTRA_GEN_BUILT_IN_CONTAINS_H
#define PYTRA_GEN_BUILT_IN_CONTAINS_H

// forward declarations
bool py_contains_dict_object(const object& values, const object& key);
bool py_contains_list_object(const object& values, const object& key);
bool py_contains_set_object(const object& values, const object& key);
bool py_contains_str_object(const object& values, const object& key);

/* Pure-Python source-of-truth for containment helpers. */

bool py_contains_dict_object(const object& values, const object& key) {
    str needle = py_to_string(key);
    {
        object __iter_obj_1 = ([&]() -> object { object __obj = values; if (!__obj) throw TypeError("NoneType is not iterable"); return __obj->py_iter_or_raise(); }());
        while (true) {
            ::std::optional<object> __next_2 = ([&]() -> ::std::optional<object> { object __iter = __iter_obj_1; if (!__iter) throw TypeError("NoneType is not an iterator"); return __iter->py_next_or_stop(); }());
            if (!__next_2.has_value()) break;
            object cur = *__next_2;
            if (cur == needle)
                return true;
        }
    }
    return false;
}

bool py_contains_list_object(const object& values, const object& key) {
    {
        object __iter_obj_3 = ([&]() -> object { object __obj = values; if (!__obj) throw TypeError("NoneType is not iterable"); return __obj->py_iter_or_raise(); }());
        while (true) {
            ::std::optional<object> __next_4 = ([&]() -> ::std::optional<object> { object __iter = __iter_obj_3; if (!__iter) throw TypeError("NoneType is not an iterator"); return __iter->py_next_or_stop(); }());
            if (!__next_4.has_value()) break;
            object cur = *__next_4;
            if (cur == key)
                return true;
        }
    }
    return false;
}

bool py_contains_set_object(const object& values, const object& key) {
    {
        object __iter_obj_5 = ([&]() -> object { object __obj = values; if (!__obj) throw TypeError("NoneType is not iterable"); return __obj->py_iter_or_raise(); }());
        while (true) {
            ::std::optional<object> __next_6 = ([&]() -> ::std::optional<object> { object __iter = __iter_obj_5; if (!__iter) throw TypeError("NoneType is not an iterator"); return __iter->py_next_or_stop(); }());
            if (!__next_6.has_value()) break;
            object cur = *__next_6;
            if (cur == key)
                return true;
        }
    }
    return false;
}

bool py_contains_str_object(const object& values, const object& key) {
    str needle = py_to_string(key);
    str haystack = py_to_string(values);
    int64 n = haystack.size();
    int64 m = needle.size();
    if (m == 0)
        return true;
    int64 i = 0;
    int64 last = n - m;
    while (i <= last) {
        int64 j = 0;
        bool ok = true;
        while (j < m) {
            if (haystack[i + j] != needle[j]) {
                ok = false;
                break;
            }
            j++;
        }
        if (ok)
            return true;
        i++;
    }
    return false;
}

#endif  // PYTRA_GEN_BUILT_IN_CONTAINS_H
