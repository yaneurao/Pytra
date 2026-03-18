// AUTO-GENERATED FILE. DO NOT EDIT.
// source: src/pytra/built_in/numeric_ops.py
// generated-by: tools/gen_runtime_from_manifest.py

function sum(values) {
    if ((values).length === 0) {
        return 0;
    }
    let acc = values[(((0) < 0) ? ((values).length + (0)) : (0))] - values[(((0) < 0) ? ((values).length + (0)) : (0))];
    let i = 0;
    let n = (values).length;
    while (i < n) {
        acc += values[(((i) < 0) ? ((values).length + (i)) : (i))];
        i += 1;
    }
    return acc;
}

function py_min(a, b) {
    if (a < b) {
        return a;
    }
    return b;
}

function py_max(a, b) {
    if (a > b) {
        return a;
    }
    return b;
}

module.exports = {sum, py_min, py_max};
