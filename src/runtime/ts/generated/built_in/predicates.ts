// AUTO-GENERATED FILE. DO NOT EDIT.
// source: src/pytra/built_in/predicates.py
// generated-by: tools/gen_runtime_from_manifest.py

const {pyBool, pyLen} = require("../../native/built_in/py_runtime.js");

function py_any(values) {
    let i = 0;
    let n = pyLen(values);
    while (i < n) {
        if (pyBool(values[i])) {
            return true;
        }
        i += 1;
    }
    return false;
}

function py_all(values) {
    let i = 0;
    let n = pyLen(values);
    while (i < n) {
        if (!(pyBool(values[i]))) {
            return false;
        }
        i += 1;
    }
    return true;
}

module.exports = {py_any, py_all};
