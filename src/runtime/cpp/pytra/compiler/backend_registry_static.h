#pragma once

#include "runtime/cpp/pytra/built_in/py_runtime.h"

namespace pytra::compiler::backend_registry_static {

list<str> list_backend_targets();
Path default_output_path(const Path& input_path, const str& target);
dict<str, object> get_backend_spec(const str& target);
dict<str, object> resolve_layer_options(const dict<str, object>& spec, const str& layer, const dict<str, str>& raw);
dict<str, object> lower_ir(const dict<str, object>& spec, const dict<str, object>& east, const dict<str, object>& lower_options);
dict<str, object> optimize_ir(const dict<str, object>& spec, const dict<str, object>& ir, const dict<str, object>& optimizer_options);
str emit_source(const dict<str, object>& spec, const dict<str, object>& ir, const Path& output_path, const dict<str, object>& emitter_options);
void apply_runtime_hook(const dict<str, object>& spec, const Path& output_path);

}  // namespace pytra::compiler::backend_registry_static

