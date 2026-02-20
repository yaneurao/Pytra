#include "runtime/cpp/pytra/built_in/py_runtime.h"


namespace pytra::std::re {

    
    bool _is_space(const str& ch) {
        return (ch == " ") || (ch == "\t") || (ch == "\n") || (ch == "\r") || (ch == "") || (ch == "");
    }
    
    str sub(const str& pattern, const str& repl, const str& text) {
        if (pattern == "\\s+") {
            list<str> out = list<str>{};
            int64 i = 0;
            int64 n = py_len(text);
            while (i < n) {
                str ch = text[i];
                if (_is_space(ch)) {
                    while ((i < n) && (_is_space(text[i]))) {
                        i++;
                    }
                    out.append(str(repl));
                    continue;
                }
                out.append(str(ch));
                i++;
            }
            return py_to_string(str("").join(out));
        }
        return py_to_string(py_replace(text, pattern, repl));
    }
    
}  // namespace pytra::std::re
