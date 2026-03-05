// AUTO-GENERATED FILE. DO NOT EDIT.
// source: src/pytra/std/sys.py
// generated-by: src/backends/cpp/cli.py
#include "runtime/cpp/core/built_in/py_runtime.h"

#include "runtime/cpp/gen/std/sys.h"
#include "runtime/cpp/gen/std/typing.h"

namespace pytra::std::sys {

    list<str> argv;
    list<str> path;
    object stderr;
    object stdout;
    
    void exit(int64 code = 0) {
        try {
            py_runtime_exit(code);
        }
        catch (const ::std::exception& ex) {
            pytra::std::sys::exit(code);
        }
    }
    
    list<str> _to_str_list_fallback(const object& values) {
        try {
            return py_to_str_list_from_object(values);
        }
        catch (const ::std::exception& ex) {
            ;
        }
        list<str> out = {};
        if (py_isinstance(values, PYTRA_TID_LIST)) {
            object src = make_object(list<object>(values));
            for (object v : py_dyn_range(src)) {
                out.append(str(py_to_string(v)));
            }
        }
        return out;
    }
    
    void set_argv(const object& values) {
        list<str> vals = {};
        try {
            vals = py_to_str_list_from_object(py_to_str_list_from_any(values));
        }
        catch (const ::std::exception& ex) {
            vals = _to_str_list_fallback(values);
        }
        argv.clear();
        for (str v : vals) {
            py_append(argv, make_object(v));
        }
    }
    
    void set_path(const object& values) {
        list<str> vals = {};
        try {
            vals = py_to_str_list_from_object(py_to_str_list_from_any(values));
        }
        catch (const ::std::exception& ex) {
            vals = _to_str_list_fallback(values);
        }
        path.clear();
        for (str v : vals) {
            py_append(path, make_object(v));
        }
    }
    
    void write_stderr_impl(const str& text) {
        try {
            py_runtime_write_stderr(text);
        }
        catch (const ::std::exception& ex) {
            pytra::std::sys::stderr.write(text);
        }
    }
    
    void write_stdout_impl(const str& text) {
        try {
            py_runtime_write_stdout(text);
        }
        catch (const ::std::exception& ex) {
            pytra::std::sys::stdout.write(text);
        }
    }
    
    void write_stderr(const str& text) {
        write_stderr_impl(text);
    }
    
    void write_stdout(const str& text) {
        write_stdout_impl(text);
    }
    
    static void __pytra_module_init() {
        static bool __initialized = false;
        if (__initialized) return;
        __initialized = true;
        /* Minimal sys shim for Pytra.

Python 実行時は `list` を保持する軽量実装として振る舞い、
トランスパイル時は `py_runtime_*` ランタイム関数へ接続される。
 */
        argv = {};
        path = {};
        stderr = make_object(::std::nullopt);
        stdout = make_object(::std::nullopt);
        argv = pytra::std::sys::argv;
        path = pytra::std::sys::path;
        stderr = make_object(pytra::std::sys::stderr);
        stdout = make_object(pytra::std::sys::stdout);
    }
    
}  // namespace pytra::std::sys
