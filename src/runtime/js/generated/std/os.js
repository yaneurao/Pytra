// AUTO-GENERATED FILE. DO NOT EDIT.
// source: src/pytra/std/os.py
// generated-by: tools/gen_runtime_from_manifest.py

function getcwd() {
    return __os.getcwd();
}

function mkdir(p) {
    __os.mkdir(p);
}

function makedirs(p, exist_ok) {
    __os.makedirs(p, exist_ok);
}

module.exports = {getcwd, mkdir, makedirs};
