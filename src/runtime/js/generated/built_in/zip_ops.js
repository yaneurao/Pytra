// AUTO-GENERATED FILE. DO NOT EDIT.
// source: src/pytra/built_in/zip_ops.py
// generated-by: tools/gen_runtime_from_manifest.py

function zip(lhs, rhs) {
    let out = [];
    let i = 0;
    let n = (lhs).length;
    if ((rhs).length < n) {
        n = (rhs).length;
    }
    while (i < n) {
        out.push([lhs[(((i) < 0) ? ((lhs).length + (i)) : (i))], rhs[(((i) < 0) ? ((rhs).length + (i)) : (i))]]);
        i += 1;
    }
    return out;
}

module.exports = {zip};
