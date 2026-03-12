#include "runtime/cpp/generated/compiler/backend_registry_static.h"

#include <cstdlib>
#include <filesystem>
#include <stdexcept>

#include "runtime/cpp/generated/compiler/transpile_cli.h"
#include "generated/std/json.h"

#if defined(_WIN32)
#include <process.h>
#define PYTRA_GETPID _getpid
#else
#include <unistd.h>
#define PYTRA_GETPID getpid
#endif

namespace pytra::compiler::backend_registry_static {

namespace {

::std::string _shell_quote(const ::std::string& raw) {
    ::std::string out = "'";
    for (char ch : raw) {
        if (ch == '\'') {
            out += "'\\''";
        } else {
            out.push_back(ch);
        }
    }
    out.push_back('\'');
    return out;
}

pytra::std::pathlib::Path _temp_path(const ::std::string& suffix) {
    static int64 counter = 0;
    const auto base = ::std::filesystem::temp_directory_path()
        / ("pytra_selfhost_" + ::std::to_string(PYTRA_GETPID()) + "_" + ::std::to_string(++counter) + suffix);
    return pytra::std::pathlib::Path(base.string());
}

void _remove_if_exists(const pytra::std::pathlib::Path& path) {
    pytra::std::pathlib::Path path_copy = path;
    if (path_copy.exists()) {
        ::std::error_code ec;
        ::std::filesystem::remove(::std::filesystem::path(py_to_string(path_copy.__str__())), ec);
    }
}

str _read_file_or_empty(const pytra::std::pathlib::Path& path) {
    pytra::std::pathlib::Path path_copy = path;
    if (!path_copy.exists()) {
        return "";
    }
    return path_copy.read_text();
}

void _run_host_python_command(const ::std::string& command, const str& error_prefix) {
    pytra::std::pathlib::Path err_path = _temp_path(".stderr.txt");
    ::std::string full = "(" + command + ") >" + _shell_quote(py_to_string(err_path.__str__())) + " 2>&1";
    int rc = ::std::system(full.c_str());
    if (rc != 0) {
        str err = _read_file_or_empty(err_path);
        _remove_if_exists(err_path);
        throw ::std::runtime_error(
            py_to_string(error_prefix + ": " + (err == "" ? str("host python command failed") : err))
        );
    }
    _remove_if_exists(err_path);
}

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

bool _object_is_runtime_type(const object& value, uint32 expected_type_id) {
    return py_runtime_object_isinstance(value, expected_type_id);
}

str _dict_get_str(const dict<str, object>& src, const str& key, const str& default_value = "") {
    auto it = src.find(key);
    if (it == src.end() || !_object_is_runtime_type(it->second, PYTRA_TID_STR)) {
        return default_value;
    }
    return py_to_string(it->second);
}

ResolvedBackendSpec _coerce_backend_spec(const dict<str, object>& spec) {
    return ResolvedBackendSpec{
        BackendSpecCarrier{
            _dict_get_str(spec, "target_lang"),
            _dict_get_str(spec, "extension"),
        },
    };
}

LayerOptionsCarrier _coerce_layer_options(const str& layer, const dict<str, object>& raw) {
    return LayerOptionsCarrier{layer, dict<str, str>(raw)};
}

}  // namespace

dict<str, object> export_backend_spec(const ResolvedBackendSpec& spec) {
    return dict<str, object>(
        dict<str, str>{
            {"target_lang", spec.carrier.target_lang},
            {"extension", spec.carrier.extension},
        }
    );
}

dict<str, object> export_layer_options(const LayerOptionsCarrier& options) {
    return dict<str, object>(options.values);
}

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
    return pytra::std::pathlib::Path(stem + get_backend_spec_typed(target).carrier.extension);
}

ResolvedBackendSpec get_backend_spec_typed(const str& target) {
    return ResolvedBackendSpec{
        BackendSpecCarrier{target, _target_extension(target)},
    };
}

dict<str, object> get_backend_spec(const str& target) {
    return export_backend_spec(get_backend_spec_typed(target));
}

LayerOptionsCarrier resolve_layer_options_typed(
    const ResolvedBackendSpec& spec,
    const str& layer,
    const dict<str, str>& raw
) {
    (void)spec;
    return LayerOptionsCarrier{layer, raw};
}

dict<str, object> resolve_layer_options(
    const dict<str, object>& spec,
    const str& layer,
    const dict<str, str>& raw
) {
    return export_layer_options(resolve_layer_options_typed(_coerce_backend_spec(spec), layer, raw));
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

dict<str, object> lower_ir_typed(
    const ResolvedBackendSpec& spec,
    const pytra::compiler::transpile_cli::CompilerRootDocument& east,
    const LayerOptionsCarrier& lower_options
) {
    (void)spec;
    (void)lower_options;
    return pytra::compiler::transpile_cli::export_compiler_root_document(east);
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

dict<str, object> optimize_ir_typed(
    const ResolvedBackendSpec& spec,
    const dict<str, object>& ir,
    const LayerOptionsCarrier& optimizer_options
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
    return emit_source_typed(_coerce_backend_spec(spec), ir, output_path, _coerce_layer_options("emitter", emitter_options));
}

str emit_source_typed(
    const ResolvedBackendSpec& spec,
    const dict<str, object>& ir,
    const pytra::std::pathlib::Path& output_path,
    const LayerOptionsCarrier& emitter_options
) {
    (void)emitter_options;
    const str target = spec.carrier.target_lang;
    if (target != "cpp") {
        throw ::std::runtime_error(
            py_to_string("[not_implemented] selfhost backend_registry_static.emit_source only supports cpp: " + target)
        );
    }
    pytra::std::pathlib::Path ir_path = _temp_path(".east3.json");
    try {
        ir_path.write_text(pytra::std::json::_dump_json_dict(ir, true, ::std::nullopt, ",", ":", 0));
        const ::std::string cmd =
            "PYTHONPATH=src${PYTHONPATH:+:$PYTHONPATH} python3 src/ir2lang.py "
            + _shell_quote(py_to_string(ir_path.__str__()))
            + " --target cpp -o "
            + _shell_quote(py_to_string(pytra::std::pathlib::Path(output_path).__str__()));
        _run_host_python_command(cmd, "selfhost direct route failed to emit source");
        pytra::std::pathlib::Path output_copy = output_path;
        str out = output_copy.read_text();
        _remove_if_exists(ir_path);
        return out;
    } catch (...) {
        _remove_if_exists(ir_path);
        throw;
    }
}

void apply_runtime_hook(
    const dict<str, object>& spec,
    const pytra::std::pathlib::Path& output_path
) {
    (void)spec;
    apply_runtime_hook_typed(output_path);
}

void apply_runtime_hook_typed(
    const pytra::std::pathlib::Path& output_path
) {
    (void)output_path;
}

void apply_runtime_hook_typed(
    const ResolvedBackendSpec& spec,
    const pytra::std::pathlib::Path& output_path
) {
    (void)spec;
    apply_runtime_hook_typed(output_path);
}

}  // namespace pytra::compiler::backend_registry_static
