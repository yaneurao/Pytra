#include "runtime/cpp/py_runtime.h"


namespace pytra::std::sys {

    
    list<str> argv = static_cast<list<str>>(py_sys_argv());
    
    list<str> path = static_cast<list<str>>(py_sys_path());
    
    int64 stderr = 1;
    
    int64 stdout = 1;
    
    void exit(int64 code) {
        py_sys_exit(code);
    }
    
    void set_argv(const object& values) {
        list<str> vals = static_cast<list<str>>(py_to_str_list_from_any(values));
        argv.clear();
        for (str v : vals)
            argv.append(v);
        py_sys_set_argv(argv);
    }
    
    void set_path(const object& values) {
        list<str> vals = static_cast<list<str>>(py_to_str_list_from_any(values));
        path.clear();
        for (str v : vals)
            path.append(v);
        py_sys_set_path(path);
    }
    
    void write_stderr(const str& text) {
        py_sys_write_stderr(text);
    }
    
    void write_stdout(const str& text) {
        py_sys_write_stdout(text);
    }
    
}  // namespace pytra::std::sys
