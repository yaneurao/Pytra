#include "core/py_runtime.h"
#include "core/process_runtime.h"
#include "core/scope_exit.h"
#include "built_in/string_ops.h"
#include "std/glob.h"
#include "std/os.h"
#include "std/os_path.h"

/* Pure Python Path helper compatible with a subset of pathlib.Path. */

struct Path : public RcObject {
    str _value;
    PYTRA_DECLARE_CLASS_TYPE(PYTRA_TID_OBJECT);
    
    Path(const object& value) {
        if ((value).tag == Path::PYTRA_TYPE_ID)
            this->_value = py_to_string((object(value.as<Path>())).as<Path>()->_value);
        else
            this->_value = value.unbox<str, PYTRA_TID_STR>();
    }
    str __str__() const {
        return this->_value;
    }
    str __repr__() const {
        return "Path(" + this->_value + ")";
    }
    str __fspath__() const {
        return this->_value;
    }
    rc<Path> __truediv__(const object& rhs) const {
        if ((rhs).tag == Path::PYTRA_TYPE_ID)
            return ::rc_new<Path>(pytra::std::os_path::join(this->_value, (object(rhs.as<Path>())).as<Path>()->_value));
        return ::rc_new<Path>(pytra::std::os_path::join(this->_value, rhs.unbox<str, PYTRA_TID_STR>()));
    }
    rc<Path> parent() const {
        auto parent_txt = pytra::std::os_path::dirname(this->_value);
        if (parent_txt == "")
            parent_txt = ".";
        return ::rc_new<Path>(parent_txt);
    }
    rc<list<rc<Path>>> parents() const {
        rc<list<rc<Path>>> out = rc_list_from_value(list<rc<Path>>{});
        str current = py_to_string(pytra::std::os_path::dirname(this->_value));
        while (true) {
            if (current == "")
                current = ".";
            rc_list_ref(out).append(::rc_new<Path>(current));
            str next_current = py_to_string(pytra::std::os_path::dirname(current));
            if (next_current == "")
                next_current = ".";
            if (next_current == current)
                break;
            current = next_current;
        }
        return out;
    }
    str name() const {
        return pytra::std::os_path::basename(this->_value);
    }
    str suffix() const {
        auto __tuple_1 = pytra::std::os_path::splitext(pytra::std::os_path::basename(this->_value));
        auto _ = py_at(__tuple_1, 0);
        auto ext = py_at(__tuple_1, 1);
        return ext;
    }
    str stem() const {
        auto __tuple_2 = pytra::std::os_path::splitext(pytra::std::os_path::basename(this->_value));
        auto root = py_at(__tuple_2, 0);
        auto _ = py_at(__tuple_2, 1);
        return root;
    }
    rc<Path> with_suffix(const str& suffix) const {
        str root;
        str _ext;
        auto __tuple_3 = pytra::std::os_path::splitext(this->_value);
        root = py_at(__tuple_3, 0);
        _ext = py_at(__tuple_3, 1);
        return ::rc_new<Path>(root + suffix);
    }
    rc<Path> relative_to(const object& other) const {
        str base;
        if ((other).tag == Path::PYTRA_TYPE_ID)
            base = py_to_string((object(other.as<Path>())).as<Path>()->_value);
        else
            base = other.unbox<str, PYTRA_TID_STR>();
        str self_abs = py_to_string(pytra::std::os_path::abspath(this->_value));
        str base_abs = py_to_string(pytra::std::os_path::abspath(base));
        if (!(py_endswith(base_abs, "/")))
            base_abs = base_abs + "/";
        if ((self_abs == base_abs) || (self_abs == py_str_slice(base_abs, 0, -(1))))
            return ::rc_new<Path>(".");
        if (py_startswith(self_abs, base_abs))
            return ::rc_new<Path>(py_str_slice(self_abs, base_abs.size(), int64(self_abs.size())));
        throw ValueError(this->_value + " is not relative to " + base);
    }
    rc<Path> resolve() const {
        return ::rc_new<Path>(pytra::std::os_path::abspath(this->_value));
    }
    bool exists() const {
        return pytra::std::os_path::exists(this->_value);
    }
    void mkdir(bool parents = false, bool exist_ok = false) const {
        if (parents) {
            pytra::std::os::makedirs(this->_value, exist_ok);
            return;
        }
        if ((exist_ok) && (pytra::std::os_path::exists(this->_value)))
            return;
        pytra::std::os::mkdir(this->_value);
    }
    str read_text(const str& encoding = "utf-8") const {
        pytra::runtime::cpp::base::PyFile f = open(this->_value, "r");
        {
            auto __finally_4 = py_make_scope_exit([&]() {{
                f.close();
            });
            return f.read();
        }
    }
    int64 write_text(const str& text, const str& encoding = "utf-8") const {
        pytra::runtime::cpp::base::PyFile f = open(this->_value, "w");
        {
            auto __finally_5 = py_make_scope_exit([&]() {{
                f.close();
            });
            return f.write(text);
        }
    }
    rc<Path> joinpath(const rc<list<object>>& parts) const {
        str result = this->_value;
        for (object part : rc_list_ref(parts)) {
            if ((part).tag == Path::PYTRA_TYPE_ID)
                result = py_to_string(pytra::std::os_path::join(result, (object(part.as<Path>())).as<Path>()->_value));
            else
                result = py_to_string(pytra::std::os_path::join(result, part.unbox<str, PYTRA_TID_STR>()));
        }
        return ::rc_new<Path>(result);
    }
    rc<list<rc<Path>>> glob(const str& pattern) const {
        rc<list<str>> paths = py_to<rc<list<str>>>(pytra::std::glob::glob(pytra::std::os_path::join(this->_value, pattern)));
        rc<list<rc<Path>>> out = rc_list_from_value(list<rc<Path>>{});
        for (str p : rc_list_ref(paths)) {
            rc_list_ref(out).append(::rc_new<Path>(p));
        }
        return out;
    }
    static rc<Path> cwd() {
        return ::rc_new<Path>(pytra::std::os::getcwd());
    }
};
