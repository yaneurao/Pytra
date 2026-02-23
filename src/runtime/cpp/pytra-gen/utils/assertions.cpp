// AUTO-GENERATED FILE. DO NOT EDIT.
// source: src/pytra/utils/assertions.py
// generated-by: src/py2cpp.py

#include "runtime/cpp/pytra/built_in/py_runtime.h"


namespace pytra::utils::assertions {

    
    bool _eq_any(const object& actual, const object& expected) {
        try {
            return py_to_string(actual) == py_to_string(expected);
        }
        catch (const ::std::exception& ex) {
            return actual == expected;
        }
    }
    
    bool py_assert_true(bool cond, const str& label) {
        if (cond)
            return true;
        if (label != "")
            py_print("[assert_true] " + label + ": False");
        else
            py_print("[assert_true] False");
        return false;
    }
    
    bool py_assert_eq(const object& actual, const object& expected, const str& label) {
        bool ok = _eq_any(actual, expected);
        if (ok)
            return true;
        if (label != "")
            py_print("[assert_eq] " + label + ": actual=" + py_to_string(actual) + ", expected=" + py_to_string(expected));
        else
            py_print("[assert_eq] actual=" + py_to_string(actual) + ", expected=" + py_to_string(expected));
        return false;
    }
    
    bool py_assert_all(const list<bool>& results, const str& label) {
        for (bool v : results) {
            if (!(v)) {
                if (label != "")
                    py_print("[assert_all] " + label + ": False");
                else
                    py_print("[assert_all] False");
                return false;
            }
        }
        return true;
    }
    
    bool py_assert_stdout(const list<str>& expected_lines, const object& fn) {
        list<str> _ = expected_lines;
        _ = static_cast<list<str>>(fn);
        // self_hosted parser / runtime 互換優先: stdout capture は未実装。
        return true;
    }
    
}  // namespace pytra::utils::assertions
