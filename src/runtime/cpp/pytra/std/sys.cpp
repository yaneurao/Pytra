#include "runtime/cpp/py_runtime.h"

#include "pytra/std/sys.h"

namespace pytra::std::sys {

    
    
    
    
    
    
    void exit(int64 code) {
        py_sys_exit(code);
    }
    
    void set_argv(const list<str>& values) {
        py_sys_set_argv(values);
    }
    
    void set_path(const list<str>& values) {
        py_sys_set_path(values);
    }
    
    void write_stderr(const str& text) {
        py_sys_write_stderr(text);
    }
    
    void write_stdout(const str& text) {
        py_sys_write_stdout(text);
    }
    
}  // namespace pytra::std::sys
