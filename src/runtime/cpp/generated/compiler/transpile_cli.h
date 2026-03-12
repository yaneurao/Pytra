// AUTO-GENERATED FILE. DO NOT EDIT.
// source: src/toolchain/compiler/transpile_cli.py
// generated-by: src/backends/cpp/cli.py

#ifndef PYTRA_GENERATED_COMPILER_TRANSPILE_CLI_H
#define PYTRA_GENERATED_COMPILER_TRANSPILE_CLI_H

#include "runtime/cpp/native/core/py_types.h"
#include "runtime/cpp/native/compiler/transpile_cli.h"

namespace pytra::compiler::transpile_cli {

object normalize_east1_to_east2_document(const object& east_doc);
object load_east1_document(const object& input_path, const object& parser_backend);
object load_east3_document(const object& input_path, const object& parser_backend, const object& object_dispatch_mode, const object& east3_opt_level, const object& east3_opt_pass, const object& dump_east3_before_opt, const object& dump_east3_after_opt, const object& dump_east3_opt_trace, const object& target_lang);
CompilerRootDocument load_east3_document_typed(const object& input_path, const object& parser_backend, const object& object_dispatch_mode, const object& east3_opt_level, const object& east3_opt_pass, const object& dump_east3_before_opt, const object& dump_east3_after_opt, const object& dump_east3_opt_trace, const object& target_lang);

}  // namespace pytra::compiler::transpile_cli

#endif  // PYTRA_GENERATED_COMPILER_TRANSPILE_CLI_H
