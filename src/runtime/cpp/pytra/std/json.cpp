#include "runtime/cpp/pytra/built_in/py_runtime.h"

#include "pytra/std/typing.h"

namespace pytra::std::json {

    
    
    str loads(const str& text) {
        return text;
    }
    
    str _escape_str(const str& s) {
        list<str> out = list<str>{"\""};
        for (str ch : s) {
            if (ch == "\"") {
                out.append(str("\\\""));
            } else {
                if (ch == "\\") {
                    out.append(str("\\\\"));
                } else {
                    if (ch == "\n") {
                        out.append(str("\\n"));
                    } else {
                        if (ch == "\r") {
                            out.append(str("\\r"));
                        } else {
                            if (ch == "\t")
                                out.append(str("\\t"));
                            else
                                out.append(str(ch));
                        }
                    }
                }
            }
        }
        out.append(str("\""));
        return py_to_string(py_join("", out));
    }
    
    str dumps(const object& obj) {
        if (py_is_none(obj))
            return "null";
        if (py_is_bool(obj))
            return (obj ? "true" : "false");
        if (py_is_int(obj))
            return py_to_string(obj);
        if (py_is_float(obj))
            return py_to_string(obj);
        if (py_is_str(obj))
            return _escape_str(py_to_string(obj));
        throw ::std::runtime_error("json.dumps unsupported type");
    }
    
}  // namespace pytra::std::json
