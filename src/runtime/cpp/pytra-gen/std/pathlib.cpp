// AUTO-GENERATED FILE. DO NOT EDIT.
// source: src/pytra/std/pathlib.py
// generated-by: src/py2cpp.py

#include "runtime/cpp/pytra/built_in/py_runtime.h"

#include "pytra/std/pathlib.h"

#include "pytra/std/glob.h"
#include "pytra/std/os.h"

namespace pytra::std::pathlib {

    /* Pure Python Path helper compatible with a subset of pathlib.Path. */
    
    
    
    
    struct Path {
        str _value;
        
        Path(const str& value) {
            this->_value = make_object(value);
        }
        str __str__() {
            return this->_value;
        }
        str __repr__() {
            return "Path(" + this->_value + ")";
        }
        str __fspath__() {
            return this->_value;
        }
        Path __truediv__(const str& rhs) {
            return Path(py_os_path_join(this->_value, rhs));
        }
        Path parent() {
            ::std::any parent_txt = make_object(py_os_path_dirname(this->_value));
            if (parent_txt == "")
                parent_txt = make_object(".");
            return Path(parent_txt);
        }
        list<Path> parents() {
            list<Path> out = list<Path>{};
            str current = py_to_string(py_os_path_dirname(this->_value));
            while (true) {
                if (current == "")
                    current = ".";
                out.append(Path(Path(current)));
                str next_current = py_to_string(py_os_path_dirname(current));
                if (next_current == "")
                    next_current = ".";
                if (next_current == current)
                    break;
                current = next_current;
            }
            return out;
        }
        str name() {
            return py_to_string(py_os_path_basename(this->_value));
        }
        str suffix() {
            auto __tuple_1 = py_os_path_splitext(py_os_path_basename(this->_value));
            auto _ = ::std::get<0>(__tuple_1);
            auto ext = ::std::get<1>(__tuple_1);
            return py_to_string(ext);
        }
        str stem() {
            auto __tuple_2 = py_os_path_splitext(py_os_path_basename(this->_value));
            auto root = ::std::get<0>(__tuple_2);
            auto _ = ::std::get<1>(__tuple_2);
            return py_to_string(root);
        }
        Path resolve() {
            return Path(py_os_path_abspath(this->_value));
        }
        bool exists() {
            return py_to_bool(py_os_path_exists(this->_value));
        }
        void mkdir(bool parents, bool exist_ok) {
            if (parents) {
                py_os_makedirs(this->_value, exist_ok);
                return;
            }
            if ((exist_ok) && (py_os_path_exists(this->_value)))
                return;
            py_os_mkdir(this->_value);
        }
        str read_text(const str& encoding) {
            pytra::runtime::cpp::base::PyFile f = open(this->_value, "r");
            {
                auto __finally_3 = py_make_scope_exit([&]() {
                    f.close();
                });
                return py_to_string(f.read());
            }
        }
        int64 write_text(const str& text, const str& encoding) {
            pytra::runtime::cpp::base::PyFile f = open(this->_value, "w");
            {
                auto __finally_4 = py_make_scope_exit([&]() {
                    f.close();
                });
                return f.write(text);
            }
        }
        list<Path> glob(const str& pattern) {
            list<str> paths = static_cast<list<str>>(py_glob_glob(py_os_path_join(this->_value, pattern)));
            list<Path> out = list<Path>{};
            for (str p : paths)
                out.append(Path(Path(p)));
            return out;
        }
        Path cwd() {
            return Path(py_os_getcwd());
        }
    };
    
}  // namespace pytra::std::pathlib
