// AUTO-GENERATED FILE. DO NOT EDIT.
// source: src/pytra/std/sys.py
// generated-by: tools/gen_runtime_from_manifest.py

const sys = {
    argv: Array.from(process.argv),
    path: [],
    stderr: process.stderr,
    stdout: process.stdout,
    exit(code = 0) {
        process.exit(Number(code) || 0);
    },
};

function exit(code) {
    sys.exit(code);
}

function set_argv(values) {
    sys.argv = Array.isArray(values) ? Array.from(values, (value) => String(value)) : [];
}

function set_path(values) {
    sys.path = Array.isArray(values) ? Array.from(values, (value) => String(value)) : [];
}

function write_stderr(text) {
    process.stderr.write(String(text));
}

function write_stdout(text) {
    process.stdout.write(String(text));
}

sys.set_argv = set_argv;
sys.set_path = set_path;
sys.write_stderr = write_stderr;
sys.write_stdout = write_stdout;

module.exports = { sys, argv: sys.argv, path: sys.path, stderr: sys.stderr, stdout: sys.stdout, exit, set_argv, set_path, write_stderr, write_stdout };
