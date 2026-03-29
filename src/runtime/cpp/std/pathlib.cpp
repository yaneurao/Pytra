#include "pathlib.h"

#include <stdexcept>

#include "glob.h"
#include "std/os.h"
#include "std/os_path.h"

Path::Path(const str& value) : _value(value) {}

Path::Path(const char* value) : _value(value == nullptr ? "" : value) {}

Path::Path(const object& value) : _value(str(py_to_string(value))) {}

str Path::__str__() const {
    return _value;
}

str Path::__repr__() const {
    return str("Path(") + _value + str(")");
}

str Path::__fspath__() const {
    return _value;
}

Path Path::__truediv__(const object& rhs) const {
    return Path(join(_value, str(py_to_string(rhs))));
}

Path Path::parent() const {
    str parent_txt = dirname(_value);
    if (parent_txt == "") {
        parent_txt = str(".");
    }
    return Path(parent_txt);
}

list<Path> Path::parents() const {
    list<Path> out{};
    str current = dirname(_value);
    while (true) {
        if (current == "") {
            current = str(".");
        }
        out.append(Path(current));
        str next_current = dirname(current);
        if (next_current == "") {
            next_current = str(".");
        }
        if (next_current == current) {
            break;
        }
        current = next_current;
    }
    return out;
}

str Path::name() const {
    return basename(_value);
}

str Path::suffix() const {
    return ::std::get<1>(splitext(basename(_value)));
}

str Path::stem() const {
    return ::std::get<0>(splitext(basename(_value)));
}

Path Path::with_suffix(const str& suffix_value) const {
    return Path(::std::get<0>(splitext(_value)) + suffix_value);
}

Path Path::relative_to(const object& other) const {
    str base = str(py_to_string(other));
    str self_abs = abspath(_value);
    str base_abs = abspath(base);
    if (!base_abs.empty() && base_abs.std().back() != '/') {
        base_abs += str("/");
    }
    if (self_abs == base_abs || (!base_abs.empty() && self_abs == base_abs.substr(0, base_abs.size() - 1))) {
        return Path(str("."));
    }
    const ::std::string self_std = self_abs.std();
    const ::std::string base_std = base_abs.std();
    if (self_std.rfind(base_std, 0) == 0) {
        return Path(str(self_std.substr(base_std.size())));
    }
    throw ::std::runtime_error(self_abs.std() + " is not relative to " + base.std());
}

Path Path::resolve() const {
    return Path(abspath(_value));
}

bool Path::exists() const {
    return ::exists(_value);
}

void Path::mkdir(bool parents_flag, bool exist_ok) const {
    if (parents_flag) {
        makedirs(_value, exist_ok);
        return;
    }
    if (exist_ok && ::exists(_value)) {
        return;
    }
    ::mkdir(_value, exist_ok);
}

str Path::read_text(const str& encoding) const {
    (void)encoding;
    auto file = open(_value, str("r"));
    return file.read();
}

int64 Path::write_text(const str& text, const str& encoding) const {
    (void)encoding;
    auto file = open(_value, str("w"));
    return file.write(text.std());
}

Path Path::joinpath(const str& part) const {
    return Path(join(_value, part));
}

Path Path::joinpath(const Path& part) const {
    return Path(join(_value, part._value));
}

list<Path> Path::glob(const str& pattern) const {
    list<Path> out{};
    for (const auto& item : ::glob(join(_value, pattern))) {
        out.append(Path(item));
    }
    return out;
}

Path Path::cwd() {
    return Path(getcwd());
}
