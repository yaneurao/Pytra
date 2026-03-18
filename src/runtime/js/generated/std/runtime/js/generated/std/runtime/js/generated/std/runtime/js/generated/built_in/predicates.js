// AUTO-GENERATED FILE. DO NOT EDIT.
// source: src/pytra/built_in/predicates.py
// generated-by: tools/gen_runtime_from_manifest.py

const {pyBool} = require("../../native/built_in/py_runtime.js");

function py_any(values) {
    for (const value of values) {
        if (pyBool(value)) {
            return true;
        }
    }
    return false;
}

function py_all(values) {
    for (const value of values) {
        if (!(pyBool(value))) {
            return false;
        }
    }
    return true;
}

module.exports = {py_any, py_all};
