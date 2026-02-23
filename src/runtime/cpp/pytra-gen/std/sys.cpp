#include "runtime/cpp/pytra/built_in/py_runtime.h"

#include "pytra/std/sys.h"
#include "pytra/std/typing.h"

namespace pytra::std::sys {

    /* Minimal sys shim for Pytra.

Python 実行時は `list` を保持する軽量実装として振る舞い、
トランスパイル時は `py_runtime_*` ランタイム関数へ接続される。
 */
    
    
    
    
    list<str> argv = list<str>{};
    
    list<str> path = list<str>{};
    
    object stderr = object{};
    
    object stdout = object{};
    
    
    
    
    
    void exit(int64 code) {
        try {
            py_runtime_exit(code);
        }
        catch (const ::std::exception& ex) {
            pytra::std::sys::exit(code);
        }
    }
    
    list<str> _to_str_list_fallback(const object& values) {
        try {
            return static_cast<list<str>>(py_to_str_list_from_object(values));
        }
        catch (const ::std::exception& ex) {
            /* pass */
        }
        list<str> out = list<str>{};
        if (py_is_list(values)) {
            list<object> src = list<object>(values);
            for (::std::any v : src)
                out.append(str(py_to_string(v)));
        }
        return out;
    }
    
    void set_argv(const object& values) {
        list<str> vals = list<str>{};
        try {
            vals = static_cast<list<str>>(py_to_str_list_from_any(values));
        }
        catch (const ::std::exception& ex) {
            vals = _to_str_list_fallback(values);
        }
        argv.clear();
        for (str v : vals)
            argv.append(v);
    }
    
    void set_path(const object& values) {
        list<str> vals = list<str>{};
        try {
            vals = static_cast<list<str>>(py_to_str_list_from_any(values));
        }
        catch (const ::std::exception& ex) {
            vals = _to_str_list_fallback(values);
        }
        path.clear();
        for (str v : vals)
            path.append(v);
    }
    
    void write_stderr_impl(const str& text) {
        py_runtime_write_stderr(text);
    }
    
    void write_stdout_impl(const str& text) {
        py_runtime_write_stdout(text);
    }
    
    void write_stderr(const str& text) {
        write_stderr_impl(text);
    }
    
    void write_stdout(const str& text) {
        write_stdout_impl(text);
    }
    
}  // namespace pytra::std::sys
