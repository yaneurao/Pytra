#include "runtime/cpp/pytra/built_in/py_runtime.h"

#include "pytra/std/sys.h"

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
    
    void set_argv(const list<str>& values) {
        argv.clear();
        for (str v : values)
            argv.append(v);
    }

    void set_argv(const ::std::any& values) {
        set_argv(py_to_str_list_from_any(values));
    }
    
    void set_path(const list<str>& values) {
        path.clear();
        for (str v : values)
            path.append(v);
    }

    void set_path(const ::std::any& values) {
        set_path(py_to_str_list_from_any(values));
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
