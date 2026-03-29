#include "argparse.h"

#include "built_in/contains.h"
#include "built_in/string_ops_fwd.h"
#include "sys.h"
#include "core/exceptions.h"

Namespace::Namespace()
    : values(rc_dict_from_value(dict<str, object>{})) {}

Namespace::Namespace(const Object<dict<str, object>>& values_in)
    : values(values_in) {}

_ArgSpec::_ArgSpec()
    : names(rc_list_from_value(list<str>{})),
      action(str("")),
      choices(rc_list_from_value(list<str>{})),
      default_value(object()),
      help_text(str("")),
      is_optional(false),
      dest(str("")) {}

_ArgSpec::_ArgSpec(
    const Object<list<str>>& names_in,
    const str& action_in,
    const Object<list<str>>& choices_in,
    const object& default_value_in,
    const str& help_text_in
)
    : names(names_in),
      action(action_in),
      choices(choices_in),
      default_value(default_value_in),
      help_text(help_text_in),
      is_optional(false),
      dest(str("")) {
    is_optional = py_len(names) > int64(0) && py_startswith(py_list_at_ref(names, int64(0)), str("-"));
    if (is_optional) {
        str base = py_replace(py_lstrip_chars(py_list_at_ref(names, py_len(names) - int64(1)), str("-")), str("-"), str("_"));
        dest = base;
    } else if (py_len(names) > int64(0)) {
        dest = py_list_at_ref(names, int64(0));
    }
}

ArgumentParser::ArgumentParser(const str& description_in)
    : description(description_in),
      _specs(rc_list_from_value(list<_ArgSpec>{})) {}

void ArgumentParser::add_argument(
    const str& name0,
    const str& name1,
    const str& name2,
    const str& name3,
    const str& help,
    const str& action,
    const Object<list<str>>& choices,
    const object& default_value
) {
    Object<list<str>> names = rc_list_from_value(list<str>{});
    if (name0 != str("")) py_list_append_mut(names, name0);
    if (name1 != str("")) py_list_append_mut(names, name1);
    if (name2 != str("")) py_list_append_mut(names, name2);
    if (name3 != str("")) py_list_append_mut(names, name3);
    if (py_len(names) == int64(0)) {
        throw ::std::runtime_error("add_argument requires at least one name");
    }
    py_list_append_mut(_specs, _ArgSpec(names, action, choices, default_value, help));
}

void ArgumentParser::_fail(const str& msg) const {
    if (msg != str("")) {
        write_stderr(str("error: ") + msg + str("\n"));
    }
    throw SystemExit(2);
}

Object<dict<str, object>> ArgumentParser::parse_args(const ::std::optional<Object<list<str>>>& argv_in) const {
    Object<list<str>> args = rc_list_from_value(list<str>{});
    if (argv_in == ::std::nullopt) {
        args = rc_list_from_value(py_list_slice_copy(::argv, int64(1), py_len(::argv)));
    } else {
        args = *argv_in;
    }

    Object<list<_ArgSpec>> specs_pos = rc_list_from_value(list<_ArgSpec>{});
    Object<list<_ArgSpec>> specs_opt = rc_list_from_value(list<_ArgSpec>{});
    for (const auto& spec : _specs) {
        if (spec.is_optional) {
            py_list_append_mut(specs_opt, spec);
        } else {
            py_list_append_mut(specs_pos, spec);
        }
    }

    Object<dict<str, int64>> by_name = rc_dict_from_value(dict<str, int64>{});
    int64 spec_i = int64(0);
    for (const auto& spec : specs_opt) {
        for (const auto& name : spec.names) {
            (*by_name)[name] = spec_i;
        }
        spec_i += int64(1);
    }

    Object<dict<str, object>> values = rc_dict_from_value(dict<str, object>{});
    for (const auto& spec : _specs) {
        if (spec.action == str("store_true")) {
            if (py_runtime_value_exact_is<bool>(spec.default_value)) {
                (*values)[spec.dest] = spec.default_value;
            } else {
                (*values)[spec.dest] = object(false);
            }
        } else if (!py_is_none(spec.default_value)) {
            (*values)[spec.dest] = spec.default_value;
        } else {
            (*values)[spec.dest] = object();
        }
    }

    int64 pos_i = int64(0);
    int64 i = int64(0);
    while (i < py_len(args)) {
        str tok = py_list_at_ref(args, i);
        if (py_startswith(tok, str("-"))) {
            if (!py_contains(by_name, tok)) {
                _fail(str("unknown option: ") + tok);
            }
            const _ArgSpec& spec = py_list_at_ref(specs_opt, py_at(by_name, tok));
            if (spec.action == str("store_true")) {
                (*values)[spec.dest] = object(true);
                i += int64(1);
                continue;
            }
            if (i + int64(1) >= py_len(args)) {
                _fail(str("missing value for option: ") + tok);
            }
            str val = py_list_at_ref(args, i + int64(1));
            if (py_len(spec.choices) > int64(0) && !py_contains(spec.choices, val)) {
                _fail(str("invalid choice for ") + tok + str(": ") + val);
            }
            (*values)[spec.dest] = object(val);
            i += int64(2);
            continue;
        }

        if (pos_i >= py_len(specs_pos)) {
            _fail(str("unexpected extra argument: ") + tok);
        }
        const _ArgSpec& spec = py_list_at_ref(specs_pos, pos_i);
        (*values)[spec.dest] = object(tok);
        pos_i += int64(1);
        i += int64(1);
    }

    if (pos_i < py_len(specs_pos)) {
        _fail(str("missing required argument: ") + py_list_at_ref(specs_pos, pos_i).dest);
    }

    return values;
}
