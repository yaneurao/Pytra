// AUTO-GENERATED FILE. DO NOT EDIT.
// source: src/pytra/std/argparse.py
// generated-by: src/backends/cpp/cli.py
#include "runtime/cpp/core/py_runtime.h"
#include "runtime/cpp/core/process_runtime.h"

#include "runtime/cpp/generated/std/argparse.h"

#include "pytra/built_in/string_ops.h"
#include "pytra/std/sys.h"

namespace pytra::std::argparse {

    /* Minimal pure-Python argparse subset for selfhost usage. */
    

    Namespace::Namespace(const object& values) {
            if (py_is_none(values)) {
                this->values = dict<str, object>{};
                return;
            }
            this->values = values;
    }
    

    _ArgSpec::_ArgSpec(const rc<list<str>>& names, const str& action, const rc<list<str>>& choices, const object& py_default, const str& help_text) {
            this->names = names;
            this->action = action;
            this->choices = choices;
            this->py_default = make_object(py_default);
            this->help_text = help_text;
            this->is_optional = (py_len(names) > 0) && (py_startswith(py_at(names, py_to<int64>(0)), "-"));
            if (this->is_optional) {
                auto base = py_replace(py_at(names, py_to<int64>(-(1))).lstrip("-"), "-", "_");
                this->dest = py_to_string(base);
            } else {
                this->dest = py_at(names, py_to<int64>(0));
            }
    }
    

    ArgumentParser::ArgumentParser(const str& description) {
            this->description = description;
            this->_specs = rc_list_from_value(list<_ArgSpec>{});
    }

    void ArgumentParser::add_argument(const str& name0, const str& name1, const str& name2, const str& name3, const str& help, const str& action, const rc<list<str>>& choices, const object& py_default) {
            rc<list<str>> names = rc_list_from_value(list<str>{});
            if (name0 != "")
                py_append(names, name0);
            if (name1 != "")
                py_append(names, name1);
            if (name2 != "")
                py_append(names, name2);
            if (name3 != "")
                py_append(names, name3);
            if ((rc_list_ref(names)).empty())
                throw ValueError("add_argument requires at least one name");
            _ArgSpec spec = _ArgSpec(names, action, choices, py_default, help);
            py_append(this->_specs, spec);
    }

    void ArgumentParser::_fail(const str& msg) {
            if (msg != "")
                pytra::std::sys::write_stderr("error: " + msg + "\n");
            throw SystemExit(2);
    }

    dict<str, object> ArgumentParser::parse_args(const object& argv) {
            rc<list<str>> args;
            if (py_is_none(argv))
                args = py_to<rc<list<str>>>(py_slice(py_runtime_argv(), 1, py_len(py_runtime_argv())));
            else
                args = py_to<rc<list<str>>>(make_object(list<object>(argv)));
            rc<list<_ArgSpec>> specs_pos = rc_list_from_value(list<_ArgSpec>{});
            rc<list<_ArgSpec>> specs_opt = rc_list_from_value(list<_ArgSpec>{});
            for (_ArgSpec s : rc_list_ref(this->_specs)) {
                if (s.is_optional)
                    py_append(specs_opt, s);
                else
                    py_append(specs_pos, s);
            }
            dict<str, int64> by_name = {};
            int64 spec_i = 0;
            for (_ArgSpec s : rc_list_ref(specs_opt)) {
                for (str n : rc_list_ref(s.names)) {
                    by_name[n] = spec_i;
                }
                spec_i++;
            }
            dict<str, object> values = dict<str, object>{};
            for (_ArgSpec s : rc_list_ref(this->_specs)) {
                if (s.action == "store_true") {
                    values[s.dest] = make_object((!py_is_none(s.py_default) ? py_to<bool>(s.py_default) : false));
                } else if (!py_is_none(s.py_default)) {
                    values[s.dest] = make_object(s.py_default);
                } else {
                    values[s.dest] = object{};
                }
            }
            int64 pos_i = 0;
            int64 i = 0;
            while (i < py_len(args)) {
                str tok = py_at(args, py_to<int64>(i));
                if (py_startswith(tok, "-")) {
                    if (!py_contains(by_name, tok))
                        this->_fail("unknown option: " + tok);
                    auto __idx_1 = py_dict_get(by_name, tok);
                    _ArgSpec spec = py_at(specs_opt, py_to<int64>(__idx_1));
                    if (spec.action == "store_true") {
                        values[spec.dest] = make_object(true);
                        i++;
                        continue;
                    }
                    if (i + 1 >= py_len(args))
                        this->_fail("missing value for option: " + tok);
                    str val = py_at(args, py_to<int64>(i + 1));
                    if ((py_len(spec.choices) > 0) && (!py_contains(spec.choices, val)))
                        this->_fail("invalid choice for " + tok + ": " + val);
                    values[spec.dest] = make_object(val);
                    i += 2;
                    continue;
                }
                if (pos_i >= py_len(specs_pos))
                    this->_fail("unexpected extra argument: " + tok);
                _ArgSpec spec = py_at(specs_pos, py_to<int64>(pos_i));
                values[spec.dest] = make_object(tok);
                pos_i++;
                i++;
            }
            if (pos_i < py_len(specs_pos))
                this->_fail("missing required argument: " + py_at(specs_pos, py_to<int64>(pos_i)).dest);
            return values;
    }
    
}  // namespace pytra::std::argparse
