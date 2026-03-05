// AUTO-GENERATED FILE. DO NOT EDIT.
// source: src/pytra/std/pathlib.py
// generated-by: src/backends/cpp/cli.py
#include "runtime/cpp/core/built_in/py_runtime.h"

#include "runtime/cpp/gen/std/pathlib.h"

#include "runtime/cpp/gen/std/glob.h"
#include "runtime/cpp/gen/std/os.h"

namespace pytra::std::pathlib {

    struct Path {
        str _value;
        
        Path(const str& value) {
            this->_value = value;
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
            auto parent_txt = py_os_path_dirname(this->_value);
            if (parent_txt == "")
                parent_txt = ".";
            return Path(parent_txt);
        }
        list<Path> parents() {
            list<Path> out = {};
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
            return py_os_path_basename(this->_value);
        }
        str suffix() {
            auto __tuple_1 = py_os_path_splitext(py_os_path_basename(this->_value));
            auto _ = py_at(__tuple_1, 0);
            auto ext = py_at(__tuple_1, 1);
            return ext;
        }
        str stem() {
            auto __tuple_2 = py_os_path_splitext(py_os_path_basename(this->_value));
            auto root = py_at(__tuple_2, 0);
            auto _ = py_at(__tuple_2, 1);
            return root;
        }
        Path resolve() {
            return Path(py_os_path_abspath(this->_value));
        }
        bool exists() {
            return py_os_path_exists(this->_value);
        }
        void mkdir(bool parents = false, bool exist_ok = false) {
            if (parents) {
                py_os_makedirs(this->_value, exist_ok);
                return;
            }
            if ((exist_ok) && (py_os_path_exists(this->_value)))
                return;
            py_os_mkdir(this->_value);
        }
        str read_text(const str& encoding = "utf-8") {
            pytra::runtime::cpp::base::PyFile f = open(this->_value, "r");
            {
                auto __finally_3 = py_make_scope_exit([&]() {
                    f.close();
                });
                return f.read();
            }
        }
        int64 write_text(const str& text, const str& encoding = "utf-8") {
            pytra::runtime::cpp::base::PyFile f = open(this->_value, "w");
            {
                auto __finally_4 = py_make_scope_exit([&]() {
                    f.close();
                });
                return f.write(text);
            }
        }
        list<Path> glob(const str& pattern) {
            list<str> paths = py_to_str_list_from_object(py_glob_glob(py_os_path_join(this->_value, pattern)));
            list<Path> out = {};
            for (object __itobj_5 : py_dyn_range(paths)) {
                str p = py_to_string(__itobj_5);
                out.append(Path(Path(p)));
            }
            return out;
        }
        Path cwd() {
            return Path(py_os_getcwd());
        }
    };
    
    static void __pytra_module_init() {
        static bool __initialized = false;
        if (__initialized) return;
        __initialized = true;
        /* Pure Python Path helper compatible with a subset of pathlib.Path. */
    }
    
    namespace {
        struct __pytra_module_initializer {
            __pytra_module_initializer() { __pytra_module_init(); }
        };
        static const __pytra_module_initializer __pytra_module_initializer_instance{};
    }  // namespace
    
}  // namespace pytra::std::pathlib
