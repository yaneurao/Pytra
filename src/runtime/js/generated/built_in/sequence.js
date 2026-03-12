// AUTO-GENERATED FILE. DO NOT EDIT.
// source: src/pytra/built_in/sequence.py
// generated-by: tools/gen_runtime_from_manifest.py

function py_range(start, stop, step) {
    let out = [];
    if (step === 0) {
        return out;
    }
    if (step > 0) {
        let i = start;
        while (i < stop) {
            out.push(i);
            i += step;
        }
    } else {
        let i = start;
        while (i > stop) {
            out.push(i);
            i += step;
        }
    }
    return out;
}

function py_repeat(v, n) {
    if (n <= 0) {
        return "";
    }
    let out = "";
    let i = 0;
    while (i < n) {
        out += v;
        i += 1;
    }
    return out;
}

module.exports = {py_range, py_repeat};
