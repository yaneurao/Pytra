// AUTO-GENERATED FILE. DO NOT EDIT.
// source: src/pytra/std/argparse.py
// generated-by: src/backends/cpp/cli.py

#ifndef PYTRA_GENERATED_STD_ARGPARSE_H
#define PYTRA_GENERATED_STD_ARGPARSE_H

#include "runtime/cpp/core/py_types.h"

namespace pytra::std::argparse {

    struct Namespace {
        dict<str, object> values;
        
        Namespace(const object& values = object{});
    };

    struct _ArgSpec {
        rc<list<str>> names;
        str action;
        rc<list<str>> choices;
        object py_default;
        str help_text;
        bool is_optional;
        str dest;
        
        _ArgSpec(const rc<list<str>>& names, const str& action = "", const rc<list<str>>& choices = rc_list_from_value(list<str>{}), const object& py_default = object{}, const str& help_text = "");
    };

    struct ArgumentParser {
        str description;
        rc<list<_ArgSpec>> _specs;
        
        ArgumentParser(const str& description = "");
        void add_argument(const str& name0, const str& name1 = "", const str& name2 = "", const str& name3 = "", const str& help = "", const str& action = "", const rc<list<str>>& choices = rc_list_from_value(list<str>{}), const object& py_default = object{});
        void _fail(const str& msg);
        dict<str, object> parse_args(const object& argv = object{});
    };


}  // namespace pytra::std::argparse

#endif  // PYTRA_GENERATED_STD_ARGPARSE_H
