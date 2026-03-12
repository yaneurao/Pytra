#pragma once

#include "runtime/cpp/native/core/py_runtime.h"

#include "generated/std/pathlib.h"

namespace pytra::compiler::transpile_cli {

struct CompilerRootMeta {
    str source_path;
    int64 east_stage;
    int64 schema_version;
    str dispatch_mode;
    str parser_backend;
};

struct CompilerRootDocument {
    CompilerRootMeta meta;
    str module_kind;
    dict<str, object> raw_module_doc;
};

dict<str, object> export_compiler_root_document(const CompilerRootDocument& doc);

CompilerRootDocument coerce_compiler_root_document(
    const dict<str, object>& raw_doc,
    const str& source_path = "",
    const str& parser_backend = ""
);

CompilerRootDocument load_east3_document_typed(
    const pytra::std::pathlib::Path& input_path,
    const str& parser_backend,
    const str& object_dispatch_mode,
    const str& east3_opt_level,
    const str& east3_opt_pass,
    const str& dump_east3_before_opt,
    const str& dump_east3_after_opt,
    const str& dump_east3_opt_trace,
    const str& target_lang
);

dict<str, object> load_east3_document(
    const pytra::std::pathlib::Path& input_path,
    const str& parser_backend,
    const str& object_dispatch_mode,
    const str& east3_opt_level,
    const str& east3_opt_pass,
    const str& dump_east3_before_opt,
    const str& dump_east3_after_opt,
    const str& dump_east3_opt_trace,
    const str& target_lang
);

}  // namespace pytra::compiler::transpile_cli
