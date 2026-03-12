// AUTO-GENERATED FILE. DO NOT EDIT.
// source: src/pytra/std/pathlib.py
// generated-by: src/backends/cpp/cli.py
#include "runtime/cpp/native/core/py_runtime.h"

#include "runtime/cpp/generated/std/pathlib.h"
#include "runtime/cpp/native/core/process_runtime.h"
#include "runtime/cpp/native/core/scope_exit.h"

#include "generated/std/glob.h"
#include "generated/std/os.h"
#include "generated/std/os_path.h"

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
            str parent_txt = pytra::std::os_path::dirname(this->_value);
            if (parent_txt == "")
                parent_txt = ".";
            return Path(parent_txt);
    }

    rc<list<Path>> Path::parents() {
            rc<list<Path>> out = rc_list_from_value(list<Path>{});
            str current = pytra::std::os_path::dirname(this->_value);
            while (true) {
                if (current == "")
                    current = ".";
                py_list_append_mut(rc_list_ref(out), Path(current));
                str next_current = pytra::std::os_path::dirname(current);
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
            auto __tuple_1 = pytra::std::os_path::splitext(pytra::std::os_path::basename(this->_value));
            str _ = ::std::get<0>(__tuple_1);
            str ext = ::std::get<1>(__tuple_1);
            return ext;
    }

    str Path::stem() {
            auto __tuple_2 = pytra::std::os_path::splitext(pytra::std::os_path::basename(this->_value));
            str root = ::std::get<0>(__tuple_2);
            str _ = ::std::get<1>(__tuple_2);
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

    rc<list<Path>> Path::glob(const str& pattern) {
            rc<list<str>> paths = pytra::std::glob::glob(pytra::std::os_path::join(this->_value, pattern));
            rc<list<Path>> out = rc_list_from_value(list<Path>{});
            for (str p : rc_list_ref(paths)) {
                py_list_append_mut(rc_list_ref(out), Path(p));
            }
            return out;
    }

    Path Path::cwd() {
            return Path(pytra::std::os::getcwd());
    }
    
}  // namespace pytra::std::pathlib
