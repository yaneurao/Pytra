#include "runtime/cpp/generated/compiler/transpile_cli.h"

#include <cstdlib>
#include <filesystem>
#include <stdexcept>

#include "pytra/std/json.h"

#if defined(_WIN32)
#include <process.h>
#define PYTRA_GETPID _getpid
#else
#include <unistd.h>
#define PYTRA_GETPID getpid
#endif

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

dict<str, object> _load_json_root_dict(const pytra::std::pathlib::Path& json_path) {
    pytra::std::pathlib::Path json_copy = json_path;
    auto parsed = pytra::std::json::loads_obj(json_copy.read_text());
    if (!parsed.has_value()) {
        throw ::std::runtime_error("invalid EAST JSON root: expected dict");
    }
    pytra::std::json::JsonObj root = parsed.value();
    auto east = root.get_obj("east");
    if (east.has_value()) {
        return east.value().raw;
    }
    return root.raw;
}

}  // namespace

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
    pytra::std::pathlib::Path input_copy = input_path;
    const str input_text = input_copy.__str__();
    if (py_endswith(input_text, ".json")) {
        return _load_json_root_dict(input_path);
    }
    if (!py_endswith(input_text, ".py")) {
        throw ::std::runtime_error("unsupported selfhost input: expected .py or .json");
    }

    pytra::std::pathlib::Path east_path = _temp_path(".east3.json");
    const ::std::string script =
        "import json, sys; "
        "from toolchain.compiler.transpile_cli import load_east3_document; "
        "from pytra.std.pathlib import Path; "
        "doc = load_east3_document("
        "Path(sys.argv[1]), "
        "parser_backend=sys.argv[3], "
        "object_dispatch_mode=sys.argv[4], "
        "east3_opt_level=sys.argv[5], "
        "east3_opt_pass=sys.argv[6], "
        "dump_east3_before_opt=sys.argv[7], "
        "dump_east3_after_opt=sys.argv[8], "
        "dump_east3_opt_trace=sys.argv[9], "
        "target_lang=sys.argv[10]); "
        "open(sys.argv[2], 'w', encoding='utf-8').write(json.dumps(doc, ensure_ascii=False, indent=2) + '\\n')";
    const ::std::string cmd =
        "PYTHONPATH=src${PYTHONPATH:+:$PYTHONPATH} python3 -c "
        + _shell_quote(script)
        + " "
        + _shell_quote(py_to_string(input_copy.__str__()))
        + " "
        + _shell_quote(py_to_string(east_path.__str__()))
        + " "
        + _shell_quote(py_to_string(parser_backend))
        + " "
        + _shell_quote(py_to_string(object_dispatch_mode))
        + " "
        + _shell_quote(py_to_string(east3_opt_level))
        + " "
        + _shell_quote(py_to_string(east3_opt_pass))
        + " "
        + _shell_quote(py_to_string(dump_east3_before_opt))
        + " "
        + _shell_quote(py_to_string(dump_east3_after_opt))
        + " "
        + _shell_quote(py_to_string(dump_east3_opt_trace))
        + " "
        + _shell_quote(py_to_string(target_lang));
    try {
        _run_host_python_command(cmd, "selfhost direct route failed to build EAST3");
        return _load_json_root_dict(east_path);
    } catch (...) {
        _remove_if_exists(east_path);
        throw;
    }
}

}  // namespace pytra::compiler::transpile_cli
