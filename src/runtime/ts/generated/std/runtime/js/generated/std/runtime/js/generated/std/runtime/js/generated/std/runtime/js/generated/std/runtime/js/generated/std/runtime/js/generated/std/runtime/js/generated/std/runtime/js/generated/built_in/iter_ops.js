// AUTO-GENERATED FILE. DO NOT EDIT.
// source: src/pytra/built_in/iter_ops.py
// generated-by: tools/gen_runtime_from_manifest.py

function py_reversed_object(values) {
    let out = [];
    for (const value of values) {
        out.push(value);
    }
    return reversed(out);
}

function py_enumerate_object(values, start) {
    let out = [];
    let i = start;
    for (const value of values) {
        out.push([i, value]);
        i += 1;
    }
    return out;
}

module.exports = {py_reversed_object, py_enumerate_object};
