// AUTO-GENERATED FILE. DO NOT EDIT.
// source: src/pytra/std/argparse.py
// generated-by: src/backends/cpp/cli.py

#ifndef PYTRA_GENERATED_STD_ARGPARSE_H
#define PYTRA_GENERATED_STD_ARGPARSE_H

#include "runtime/cpp/native/core/py_runtime.h"

namespace pytra::std::argparse {

struct Namespace;
struct _ArgSpec;
struct ArgumentParser;

struct ArgValue {
    uint32 tag;
    str str_val;
    bool bool_val;

    ArgValue() : tag(PYTRA_TID_NONE) {}
    ArgValue(const str& v) : tag(PYTRA_TID_STR), str_val(v) {}
    ArgValue(const bool& v) : tag(PYTRA_TID_BOOL), bool_val(v) {}
    ArgValue(::std::monostate) : tag(PYTRA_TID_NONE) {}
};


    struct Namespace {
        dict<str, ArgValue> values;
        
        Namespace(const ::std::optional<dict<str, ArgValue>>& values = ::std::nullopt);
    };

    struct _ArgSpec {
        rc<list<str>> names;
        str action;
        rc<list<str>> choices;
        ArgValue py_default;
        str help_text;
        bool is_optional;
        str dest;
        
        _ArgSpec(const rc<list<str>>& names, const str& action = "", const rc<list<str>>& choices = rc_list_from_value(list<str>{}), const ArgValue& py_default = ArgValue(), const str& help_text = "");
    };

    struct ArgumentParser {
        str description;
        rc<list<_ArgSpec>> _specs;
        
        ArgumentParser(const str& description = "");
        void add_argument(const str& name0, const str& name1 = "", const str& name2 = "", const str& name3 = "", const str& help = "", const str& action = "", const rc<list<str>>& choices = rc_list_from_value(list<str>{}), const ArgValue& py_default = ArgValue());
        void _fail(const str& msg) const;
        dict<str, ArgValue> parse_args(const ::std::optional<rc<list<str>>>& argv = ::std::nullopt) const;
    };


}  // namespace pytra::std::argparse

#endif  // PYTRA_GENERATED_STD_ARGPARSE_H
