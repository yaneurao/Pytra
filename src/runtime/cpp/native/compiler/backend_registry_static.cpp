#include "runtime/cpp/generated/compiler/backend_registry_static.h"

#include <stdexcept>

namespace pytra::compiler::backend_registry_static {

namespace {

str _target_extension(const str& target) {
    if (target == "cpp") return ".cpp";
    if (target == "rs") return ".rs";
    if (target == "cs") return ".cs";
    if (target == "js") return ".js";
    if (target == "ts") return ".ts";
    if (target == "go") return ".go";
    if (target == "java") return ".java";
    if (target == "kotlin") return ".kt";
    if (target == "swift") return ".swift";
    if (target == "ruby") return ".rb";
    if (target == "lua") return ".lua";
    if (target == "scala") return ".scala";
    if (target == "php") return ".php";
    if (target == "nim") return ".nim";
    return ".out";
}

str _strip_known_suffix(const str& path_txt) {
    const ::std::string raw = py_to_string(path_txt);
    if (raw.size() >= 3 && raw.substr(raw.size() - 3) == ".py") {
        return str(raw.substr(0, raw.size() - 3));
    }
    if (raw.size() >= 5 && raw.substr(raw.size() - 5) == ".json") {
        return str(raw.substr(0, raw.size() - 5));
    }
    return path_txt;
}

}  // namespace

list<str> list_backend_targets() {
    return list<str>{
        "cpp",
        "rs",
        "cs",
        "js",
        "ts",
        "go",
        "java",
        "kotlin",
        "swift",
        "ruby",
        "lua",
        "scala",
        "php",
        "nim",
    };
}

pytra::std::pathlib::Path default_output_path(
    const pytra::std::pathlib::Path& input_path,
    const str& target
) {
    pytra::std::pathlib::Path input_copy = input_path;
    str stem = _strip_known_suffix(input_copy.__str__());
    return pytra::std::pathlib::Path(stem + _target_extension(target));
}

dict<str, object> get_backend_spec(const str& target) {
    dict<str, object> spec = {};
    spec["target_lang"] = make_object(target);
    spec["extension"] = make_object(_target_extension(target));
    return spec;
}

dict<str, object> resolve_layer_options(
    const dict<str, object>& spec,
    const str& layer,
    const dict<str, str>& raw
) {
    (void)spec;
    (void)layer;
    (void)raw;
    return dict<str, object>{};
}

dict<str, object> lower_ir(
    const dict<str, object>& spec,
    const dict<str, object>& east,
    const dict<str, object>& lower_options
) {
    (void)spec;
    (void)lower_options;
    return east;
}

dict<str, object> optimize_ir(
    const dict<str, object>& spec,
    const dict<str, object>& ir,
    const dict<str, object>& optimizer_options
) {
    (void)spec;
    (void)optimizer_options;
    return ir;
}

str emit_source(
    const dict<str, object>& spec,
    const dict<str, object>& ir,
    const pytra::std::pathlib::Path& output_path,
    const dict<str, object>& emitter_options
) {
    (void)spec;
    (void)ir;
    (void)output_path;
    (void)emitter_options;
    throw ::std::runtime_error(
        "[not_implemented] selfhost backend_registry_static.emit_source is not implemented yet"
    );
}

void apply_runtime_hook(
    const dict<str, object>& spec,
    const pytra::std::pathlib::Path& output_path
) {
    (void)spec;
    (void)output_path;
}

}  // namespace pytra::compiler::backend_registry_static
