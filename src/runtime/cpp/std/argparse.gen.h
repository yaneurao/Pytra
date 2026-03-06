// AUTO-GENERATED FILE. DO NOT EDIT.
// source: src/pytra/std/argparse.py
// generated-by: src/backends/cpp/cli.py

#ifndef PYTRA_STD_ARGPARSE_GEN_H
#define PYTRA_STD_ARGPARSE_GEN_H

#include "runtime/cpp/core/py_types.ext.h"

namespace pytra::std::argparse {

    struct Namespace {
        Namespace(const ::std::optional<dict<str, object>>& values = ::std::nullopt);
    };

    struct _ArgSpec : public PyObj {
        ::std::optional<str> action;
        ::std::optional<list<str>> choices;
        object default;
        ::std::optional<str> help_text;
        bool is_optional;
        list<str> names;
        PYTRA_DECLARE_CLASS_TYPE(PYTRA_TID_OBJECT);
        
        _ArgSpec(const list<str>& names, const ::std::optional<str>& action, const ::std::optional<list<str>>& choices, const object& default, const ::std::optional<str>& help_text);
    };

    struct ArgumentParser : public PyObj {
        list<rc<_ArgSpec>> _specs;
        bool description;
        PYTRA_DECLARE_CLASS_TYPE(PYTRA_TID_OBJECT);
        
        ArgumentParser(const ::std::optional<str>& description = ::std::nullopt);
        void add_argument(const str& name0, const str& name1 = "", const str& name2 = "", const str& name3 = "", const ::std::optional<str>& help = ::std::nullopt, const ::std::optional<str>& action = ::std::nullopt, const ::std::optional<list<str>>& choices = ::std::nullopt, const object& default = object{});
        void _fail(const str& msg);
        dict<str, object> parse_args(const ::std::optional<list<str>>& argv = ::std::nullopt);
    };


}  // namespace pytra::std::argparse

#endif  // PYTRA_STD_ARGPARSE_GEN_H
