// AUTO-GENERATED FILE. DO NOT EDIT.
// source: src/pytra/built_in/iter_ops.py
// generated-by: tools/gen_runtime_from_manifest.py

const {pyLen} = require("../../native/built_in/py_runtime.js");

function py_reversed_object(values) {
    let out = [];
    let i = pyLen(values) - 1;
    while (i >= 0) {
        out.push(values[i]);
        i -= 1;
    }
    return out;
}

function py_enumerate_object(values, start) {
    let out = [];
    let i = 0;
    let n = pyLen(values);
    while (i < n) {
        out.push([start + i, values[i]]);
        i += 1;
    }
    return out;
}

module.exports = {py_reversed_object, py_enumerate_object};
