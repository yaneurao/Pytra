#pragma once

#include "runtime/cpp/native/core/py_runtime.h"

#include "generated/std/pathlib.h"

namespace pytra::compiler::transpile_cli {
struct CompilerRootDocument;
}

namespace pytra::compiler::backend_registry_static {

struct BackendSpecCarrier {
    str target_lang;
    str extension;
};

struct ResolvedBackendSpec {
    BackendSpecCarrier carrier;
};

dict<str, object> export_backend_spec(const ResolvedBackendSpec& spec);

struct LayerOptionsCarrier {
    str layer;
    dict<str, str> values;
};

dict<str, object> export_layer_options(const LayerOptionsCarrier& options);

list<str> list_backend_targets();
pytra::std::pathlib::Path default_output_path(
    const pytra::std::pathlib::Path& input_path,
    const str& target
);
ResolvedBackendSpec get_backend_spec_typed(const str& target);
dict<str, object> get_backend_spec(const str& target);
LayerOptionsCarrier resolve_layer_options_typed(
    const ResolvedBackendSpec& spec,
    const str& layer,
    const dict<str, str>& raw
);
dict<str, object> resolve_layer_options(
    const dict<str, object>& spec,
    const str& layer,
    const dict<str, str>& raw
);
dict<str, object> lower_ir(
    const dict<str, object>& spec,
    const dict<str, object>& east,
    const dict<str, object>& lower_options
);
dict<str, object> lower_ir_typed(
    const ResolvedBackendSpec& spec,
    const pytra::compiler::transpile_cli::CompilerRootDocument& east,
    const LayerOptionsCarrier& lower_options
);
dict<str, object> optimize_ir(
    const dict<str, object>& spec,
    const dict<str, object>& ir,
    const dict<str, object>& optimizer_options
);
dict<str, object> optimize_ir_typed(
    const ResolvedBackendSpec& spec,
    const dict<str, object>& ir,
    const LayerOptionsCarrier& optimizer_options
);
str emit_source(
    const dict<str, object>& spec,
    const dict<str, object>& ir,
    const pytra::std::pathlib::Path& output_path,
    const dict<str, object>& emitter_options
);
str emit_source_typed(
    const ResolvedBackendSpec& spec,
    const dict<str, object>& ir,
    const pytra::std::pathlib::Path& output_path,
    const LayerOptionsCarrier& emitter_options
);
void apply_runtime_hook(
    const dict<str, object>& spec,
    const pytra::std::pathlib::Path& output_path
);
void apply_runtime_hook_typed(
    const pytra::std::pathlib::Path& output_path
);
void apply_runtime_hook_typed(
    const ResolvedBackendSpec& spec,
    const pytra::std::pathlib::Path& output_path
);

}  // namespace pytra::compiler::backend_registry_static
