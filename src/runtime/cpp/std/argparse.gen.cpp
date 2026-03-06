// AUTO-GENERATED FILE. DO NOT EDIT.
// source: src/pytra/std/argparse.py
// generated-by: src/backends/cpp/cli.py
#include "runtime/cpp/core/built_in/py_runtime.ext.h"

#include "runtime/cpp/std/argparse.gen.h"

#include "runtime/cpp/std/sys.gen.h"

namespace pytra::std::argparse {

    /* Minimal pure-Python argparse subset for selfhost usage. */
    

    Namespace::Namespace(const ::std::optional<dict<str, object>>& values) {
            if (py_is_none(values))
                return;
            for (object __itobj_1 : py_dyn_range(values)) {
                auto k = py_at(__itobj_1, 0);
                auto v = py_at(__itobj_1, 1);
                setattr(*this, k, v);
            }
    }
    

    _ArgSpec::_ArgSpec(const list<str>& names, const ::std::optional<str>& action, const ::std::optional<list<str>>& choices, const object& default, const ::std::optional<str>& help_text) {
            this->names = names;
            this->action = action;
            this->choices = choices;
            this->default = make_object(py_default);
            this->help_text = help_text;
            this->is_optional = (py_len(names) > 0) && (py_startswith(names[0], "-"));
            if (this->is_optional) {
                auto base = py_replace(py_at(names, -(1)).lstrip("-"), "-", "_");
                this->dest = base;
            } else {
                this->dest = names[0];
            }
    }
    

    ArgumentParser::ArgumentParser(const ::std::optional<str>& description) {
            this->description = (description ? description : "");
            this->_specs = {};
    }

    void ArgumentParser::add_argument(const str& name0, const str& name1, const str& name2, const str& name3, const ::std::optional<str>& help, const ::std::optional<str>& action, const ::std::optional<list<str>>& choices, const object& default) {
            list<str> names = {};
            if (name0 != "")
                names.append(name0);
            if (name1 != "")
                names.append(name1);
            if (name2 != "")
                names.append(name2);
            if (name3 != "")
                names.append(name3);
            if (names.empty())
                throw ValueError("add_argument requires at least one name");
            rc<_ArgSpec> spec = ::rc_new<_ArgSpec>(names, action, choices, py_default, help);
            this->_specs.append(spec);
    }

    void ArgumentParser::_fail(const str& msg) {
            if (msg != "")
                pytra::std::sys::write_stderr("error: " + msg + "\n");
            throw SystemExit(2);
    }

    dict<str, object> ArgumentParser::parse_args(const ::std::optional<list<str>>& argv) {
            object args = make_object(list<object>((py_is_none(argv) ? py_slice(py_runtime_argv(), 1, py_len(py_runtime_argv())) : argv)));
            
            list<rc<_ArgSpec>> specs_pos = [&]() -> list<rc<_ArgSpec>> {     list<rc<_ArgSpec>> __out;     for (auto s : this->_specs) {         if (!(s->is_optional)) __out.append(s);     }     return __out; }();
            list<rc<_ArgSpec>> specs_opt = [&]() -> list<rc<_ArgSpec>> {     list<rc<_ArgSpec>> __out;     for (auto s : this->_specs) {         if (s->is_optional) __out.append(s);     }     return __out; }();
            dict<str, rc<_ArgSpec>> by_name = {};
            for (const rc<_ArgSpec>& s : specs_opt) {
                for (object n : py_dyn_range(s->names)) {
                    by_name[n] = s;
                }
            }
            dict<str, object> values = dict<str, object>{};
            for (const rc<_ArgSpec>& s : this->_specs) {
                if (s->action == "store_true") {
                    values[s->dest] = make_object((!py_is_none(s->default) ? py_to<bool>(s->default) : false));
                } else if (!py_is_none(s->default)) {
                    values[s->dest] = make_object(s->default);
                } else {
                    values[s->dest] = object{};
                }
            }
            int64 pos_i = 0;
            int64 i = 0;
            while (i < py_len(args)) {
                auto tok = py_at(args, py_to<int64>(i));
                if (tok.startswith("-")) {
                    auto spec = py_dict_get_maybe(by_name, tok);
                    if (py_is_none(spec))
                        this->_fail("unknown option: " + py_to_string(tok));
                    if (obj_to_rc_or_raise<_ArgSpec>(make_object(spec), "_ArgSpec.action")->action == "store_true") {
                        values[spec.dest] = make_object(true);
                        i++;
                        continue;
                    }
                    if (i + 1 >= py_len(args))
                        this->_fail("missing value for option: " + py_to_string(tok));
                    auto __idx_4 = i + 1;
                    auto val = py_at(args, py_to<int64>(__idx_4));
                    if ((!py_is_none(obj_to_rc_or_raise<_ArgSpec>(make_object(spec), "_ArgSpec.choices")->choices)) && (!py_contains(obj_to_rc_or_raise<_ArgSpec>(make_object(spec), "_ArgSpec.choices")->choices, val)))
                        this->_fail("invalid choice for " + py_to_string(tok) + ": " + py_to_string(val));
                    values[spec.dest] = make_object(val);
                    i += 2;
                    continue;
                }
                if (pos_i >= py_len(specs_pos))
                    this->_fail("unexpected extra argument: " + py_to_string(tok));
                rc<_ArgSpec> spec = specs_pos[pos_i];
                values[spec->dest] = make_object(tok);
                pos_i++;
                i++;
            }
            if (pos_i < py_len(specs_pos))
                this->_fail("missing required argument: " + py_to_string(specs_pos[pos_i]->dest));
            return values;
    }
    
}  // namespace pytra::std::argparse
