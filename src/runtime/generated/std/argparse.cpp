#include "core/py_runtime.h"
#include "core/process_runtime.h"
#include "built_in/contains.h"
#include "built_in/string_ops.h"
#include "std/sys.h"

/* Minimal pure-Python argparse subset for selfhost usage. */

using ArgValue = object;


struct Namespace {
    dict<str, ArgValue> values;
    
    Namespace(const ::std::optional<dict<str, ArgValue>>& values = ::std::nullopt) {
        if (!values.has_value()) {
            this->values = dict<str, ArgValue>{};
            return;
        }
        this->values = values.value();
    }
};

struct _ArgSpec {
    rc<list<str>> names;
    str action;
    rc<list<str>> choices;
    ArgValue py_default;
    str help_text;
    bool is_optional;
    str dest;
    
    _ArgSpec(const rc<list<str>>& names, const str& action = "", const rc<list<str>>& choices = rc_list_from_value(list<str>{}), const ArgValue& py_default = ArgValue{}, const str& help_text = "") {
        this->names = names;
        this->action = action;
        this->choices = choices;
        this->py_default = py_default;
        this->help_text = help_text;
        this->is_optional = ((rc_list_ref(names)).size() > 0) && (py_startswith(py_list_at_ref(rc_list_ref(names), 0), "-"));
        if (this->is_optional) {
            auto base = py_replace(py_list_at_ref(rc_list_ref(names), -(1)).lstrip("-"), "-", "_");
            this->dest = py_to_string(base);
        } else {
            this->dest = py_list_at_ref(rc_list_ref(names), 0);
        }
    }
};

struct ArgumentParser {
    str description;
    rc<list<_ArgSpec>> _specs;
    
    ArgumentParser(const str& description = "") {
        this->description = description;
        this->_specs = rc_list_from_value(list<_ArgSpec>{});
    }
    void add_argument(const str& name0, const str& name1 = "", const str& name2 = "", const str& name3 = "", const str& help = "", const str& action = "", const rc<list<str>>& choices = rc_list_from_value(list<str>{}), const ArgValue& py_default = ArgValue{}) {
        rc<list<str>> names = rc_list_from_value(list<str>{});
        if (name0 != "")
            rc_list_ref(names).append(name0);
        if (name1 != "")
            rc_list_ref(names).append(name1);
        if (name2 != "")
            rc_list_ref(names).append(name2);
        if (name3 != "")
            rc_list_ref(names).append(name3);
        if ((rc_list_ref(names)).empty())
            throw ValueError("add_argument requires at least one name");
        _ArgSpec spec = _ArgSpec(names, action, choices, py_default, help);
        rc_list_ref(this->_specs).append(spec);
    }
    void _fail(const str& msg) const {
        if (msg != "")
            pytra::std::sys::write_stderr("error: " + msg + "\n");
        throw SystemExit(2);
    }
    dict<str, ArgValue> parse_args(const ::std::optional<rc<list<str>>>& argv = ::std::nullopt) const {
        rc<list<str>> args;
        if (!argv.has_value())
            args = py_to<rc<list<str>>>(py_str_slice(pytra::std::sys::argv, 1, int64((pytra::std::sys::argv).size())));
        else
            args = py_to<rc<list<str>>>(argv.value());
        rc<list<_ArgSpec>> specs_pos = rc_list_from_value(list<_ArgSpec>{});
        rc<list<_ArgSpec>> specs_opt = rc_list_from_value(list<_ArgSpec>{});
        for (_ArgSpec s : rc_list_ref(this->_specs)) {
            if (s.is_optional)
                rc_list_ref(specs_opt).append(s);
            else
                rc_list_ref(specs_pos).append(s);
        }
        dict<str, int64> by_name = {};
        int64 spec_i = 0;
        for (_ArgSpec s : rc_list_ref(specs_opt)) {
            for (str n : rc_list_ref(s.names)) {
                by_name[n] = spec_i;
            }
            spec_i++;
        }
        dict<str, ArgValue> values = {};
        for (_ArgSpec s : rc_list_ref(this->_specs)) {
            if (s.action == "store_true") {
                if ((s.py_default).tag == PYTRA_TID_BOOL)
                    values[s.dest] = s.py_default.unbox<bool, PYTRA_TID_BOOL>();
                else
                    values[s.dest] = false;
            } else if (s.py_default.tag != PYTRA_TID_NONE) {
                values[s.dest] = s.py_default;
            } else {
                values[s.dest] = ArgValue{};
            }
        }
        int64 pos_i = 0;
        int64 i = 0;
        while (i < (rc_list_ref(args)).size()) {
            str tok = py_list_at_ref(rc_list_ref(args), i);
            if (py_startswith(tok, "-")) {
                if (!py_contains(by_name, tok))
                    this->_fail("unknown option: " + tok);
                auto __idx_1 = ([&]() { auto&& __dict_2 = by_name; auto __dict_key_3 = tok; return __dict_2.at(__dict_key_3); }());
                _ArgSpec spec = py_list_at_ref(rc_list_ref(specs_opt), __idx_1);
                if (spec.action == "store_true") {
                    values[spec.dest] = true;
                    i++;
                    continue;
                }
                if (i + 1 >= (rc_list_ref(args)).size())
                    this->_fail("missing value for option: " + tok);
                str val = py_list_at_ref(rc_list_ref(args), i + 1);
                if (((rc_list_ref(spec.choices)).size() > 0) && (!py_contains(spec.choices, val)))
                    this->_fail("invalid choice for " + tok + ": " + val);
                values[spec.dest] = val;
                i += 2;
                continue;
            }
            if (pos_i >= (rc_list_ref(specs_pos)).size())
                this->_fail("unexpected extra argument: " + tok);
            _ArgSpec spec = py_list_at_ref(rc_list_ref(specs_pos), pos_i);
            values[spec.dest] = tok;
            pos_i++;
            i++;
        }
        if (pos_i < (rc_list_ref(specs_pos)).size())
            this->_fail("missing required argument: " + py_list_at_ref(rc_list_ref(specs_pos), pos_i).dest);
        return values;
    }
};
