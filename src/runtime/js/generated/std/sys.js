// AUTO-GENERATED FILE. DO NOT EDIT.
// source: src/pytra/std/sys.py
// generated-by: tools/gen_runtime_from_manifest.py

const sys_native = require("../../native/std/sys_native.js");

function exit(code) {
    return sys_native.exit(code);
}

function set_argv(values) {
    return sys_native.set_argv(values);
}

function set_path(values) {
    return sys_native.set_path(values);
}

function write_stderr(text) {
    return sys_native.write_stderr(text);
}

function write_stdout(text) {
    return sys_native.write_stdout(text);
}

const sys = sys_native.sys;
const argv = sys_native.argv;
const path = sys_native.path;
const stderr = sys_native.stderr;
const stdout = sys_native.stdout;

module.exports = { sys, argv, path, stderr, stdout, exit, set_argv, set_path, write_stderr, write_stdout };
