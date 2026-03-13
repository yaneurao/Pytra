// AUTO-GENERATED FILE. DO NOT EDIT.
// source: src/pytra/std/os_path.py
// generated-by: tools/gen_runtime_from_manifest.py

function join(a, b) {
    return __path.join(a, b);
}

function dirname(p) {
    return __path.dirname(p);
}

function basename(p) {
    return __path.basename(p);
}

function splitext(p) {
    return __path.splitext(p);
}

function abspath(p) {
    return __path.abspath(p);
}

function exists(p) {
    return __path.exists(p);
}

module.exports = {join, dirname, basename, splitext, abspath, exists};
