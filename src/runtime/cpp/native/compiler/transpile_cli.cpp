#include "runtime/cpp/generated/compiler/transpile_cli.h"

#include <stdexcept>

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
) {
    (void)input_path;
    (void)parser_backend;
    (void)object_dispatch_mode;
    (void)east3_opt_level;
    (void)east3_opt_pass;
    (void)dump_east3_before_opt;
    (void)dump_east3_after_opt;
    (void)dump_east3_opt_trace;
    (void)target_lang;
    throw ::std::runtime_error(
        "[not_implemented] selfhost transpile_cli.load_east3_document is not implemented yet"
    );
}

}  // namespace pytra::compiler::transpile_cli
