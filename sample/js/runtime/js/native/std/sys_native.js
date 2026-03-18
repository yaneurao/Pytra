// Generated std/sys.js delegates host bindings through this native seam.

function _replaceArray(target, values) {
    const next = Array.isArray(values) ? Array.from(values, (value) => String(value)) : [];
    target.splice(0, target.length, ...next);
}

const sys = {
    argv: Array.from(process.argv, (value) => String(value)),
    path: [],
    stderr: process.stderr,
    stdout: process.stdout,
    exit(code = 0) {
        process.exit(Number(code) || 0);
    },
};

const argv = sys.argv;
const path = sys.path;
const stderr = sys.stderr;
const stdout = sys.stdout;

function exit(code) {
    return sys.exit(code);
}

function set_argv(values) {
    _replaceArray(sys.argv, values);
}

function set_path(values) {
    _replaceArray(sys.path, values);
}

function write_stderr(text) {
    sys.stderr.write(String(text));
}

function write_stdout(text) {
    sys.stdout.write(String(text));
}

sys.set_argv = set_argv;
sys.set_path = set_path;
sys.write_stderr = write_stderr;
sys.write_stdout = write_stdout;

module.exports = { sys, argv, path, stderr, stdout, exit, set_argv, set_path, write_stderr, write_stdout };
