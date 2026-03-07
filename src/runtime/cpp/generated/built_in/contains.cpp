// AUTO-GENERATED FILE. DO NOT EDIT.
// source: src/pytra/built_in/contains.py
// generated-by: src/backends/cpp/cli.py
#include "runtime/cpp/core/py_runtime.h"

#include "runtime/cpp/generated/built_in/contains.h"


/* Pure-Python source-of-truth for containment helpers. */

bool py_contains_dict_object(const object& values, const object& key) {
    str needle = py_to_string(key);
    for (object cur : py_dyn_range(values)) {
        if (cur == needle)
            return true;
    }
    return false;
}

bool py_contains_list_object(const object& values, const object& key) {
    for (object cur : py_dyn_range(values)) {
        if (cur == key)
            return true;
    }
    return false;
}

bool py_contains_set_object(const object& values, const object& key) {
    for (object cur : py_dyn_range(values)) {
        if (cur == key)
            return true;
    }
    return false;
}

bool py_contains_str_object(const object& values, const object& key) {
    str needle = py_to_string(key);
    int64 n = py_len(values);
    int64 m = py_len(needle);
    if (m == 0)
        return true;
    int64 i = 0;
    int64 last = n - m;
    while (i <= last) {
        int64 j = 0;
        bool ok = true;
        while (j < m) {
            if (py_at(values, py_to<int64>(i + j)) != needle[j]) {
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
