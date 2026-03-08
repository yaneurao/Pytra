#pragma once

#include "runtime/cpp/core/py_runtime.h"

#include "pytra/std/pathlib.h"

namespace pytra::compiler::transpile_cli {

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
