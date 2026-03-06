// AUTO-GENERATED FILE. DO NOT EDIT.
// source: src/pytra/std/pathlib.py
// generated-by: src/backends/cpp/cli.py
#include "runtime/cpp/core/py_runtime.ext.h"

#include "runtime/cpp/std/pathlib.gen.h"

#include "std/glob.gen.h"
#include "std/os.gen.h"
#include "std/os_path.gen.h"

namespace pytra::std::pathlib {

    /* Pure Python Path helper compatible with a subset of pathlib.Path. */
    

    Path::Path(const str& value) {
            this->_value = value;
    }

    str Path::__str__() {
            return this->_value;
    }

    str Path::__repr__() {
            return "Path(" + this->_value + ")";
    }

    str Path::__fspath__() {
            return this->_value;
    }

    Path Path::__truediv__(const str& rhs) {
            return Path(pytra::std::os_path::join(this->_value, rhs));
    }

    Path Path::parent() {
            auto parent_txt = pytra::std::os_path::dirname(this->_value);
            if (parent_txt == "")
                parent_txt = ".";
            return Path(parent_txt);
    }

    list<Path> Path::parents() {
            list<Path> out = {};
            str current = py_to_string(pytra::std::os_path::dirname(this->_value));
            while (true) {
                if (current == "")
                    current = ".";
                out.append(Path(Path(current)));
                str next_current = py_to_string(pytra::std::os_path::dirname(current));
                if (next_current == "")
                    next_current = ".";
                if (next_current == current)
                    break;
                current = next_current;
            }
            return out;
    }

    str Path::name() {
            return pytra::std::os_path::basename(this->_value);
    }

    str Path::suffix() {
            auto __tuple_1 = pytra::std::os_path::splitext(py_to_string(pytra::std::os_path::basename(this->_value)));
            auto _ = py_at(__tuple_1, 0);
            auto ext = py_at(__tuple_1, 1);
            return ext;
    }

    str Path::stem() {
            auto __tuple_2 = pytra::std::os_path::splitext(py_to_string(pytra::std::os_path::basename(this->_value)));
            auto root = py_at(__tuple_2, 0);
            auto _ = py_at(__tuple_2, 1);
            return root;
    }

    Path Path::resolve() {
            return Path(pytra::std::os_path::abspath(this->_value));
    }

    bool Path::exists() {
            return pytra::std::os_path::exists(this->_value);
    }

    void Path::mkdir(bool parents, bool exist_ok) {
            if (parents) {
                pytra::std::os::makedirs(this->_value, exist_ok);
                return;
            }
            if ((exist_ok) && (pytra::std::os_path::exists(this->_value)))
                return;
            pytra::std::os::mkdir(this->_value);
    }

    str Path::read_text(const str& encoding) {
            pytra::runtime::cpp::base::PyFile f = open(this->_value, "r");
            {
                auto __finally_3 = py_make_scope_exit([&]() {
                    f.close();
                });
                return f.read();
            }
    }

    int64 Path::write_text(const str& text, const str& encoding) {
            pytra::runtime::cpp::base::PyFile f = open(this->_value, "w");
            {
                auto __finally_4 = py_make_scope_exit([&]() {
                    f.close();
                });
                return f.write(text);
            }
    }

    list<Path> Path::glob(const str& pattern) {
            list<str> paths = py_to_str_list_from_object(pytra::std::glob::glob(py_to_string(pytra::std::os_path::join(this->_value, pattern))));
            list<Path> out = {};
            for (object __itobj_5 : py_dyn_range(paths)) {
                str p = py_to_string(__itobj_5);
                out.append(Path(Path(p)));
            }
            return out;
    }

    Path Path::cwd() {
            return Path(pytra::std::os::getcwd());
    }
    
}  // namespace pytra::std::pathlib
