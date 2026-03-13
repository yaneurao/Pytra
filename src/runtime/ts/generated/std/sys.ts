// AUTO-GENERATED FILE. DO NOT EDIT.
// source: src/pytra/std/sys.py
// generated-by: tools/gen_runtime_from_manifest.py

import { extern } from "./pytra/std.js";

function exit(code) {
    __s.exit(code);
}

function set_argv(values) {
    argv.clear();
    for (const v of values) {
        argv.append(v);
    }
}

function set_path(values) {
    path.clear();
    for (const v of values) {
        path.append(v);
    }
}

function write_stderr(text) {
    __s.stderr.write(text);
}

function write_stdout(text) {
    __s.stdout.write(text);
}

"pytra.std.sys: extern-marked sys API with Python runtime fallback.";
let argv = extern(__s.argv);
let path = extern(__s.path);
let stderr = extern(__s.stderr);
let stdout = extern(__s.stdout);

module.exports = {exit, set_argv, set_path, write_stderr, write_stdout};
