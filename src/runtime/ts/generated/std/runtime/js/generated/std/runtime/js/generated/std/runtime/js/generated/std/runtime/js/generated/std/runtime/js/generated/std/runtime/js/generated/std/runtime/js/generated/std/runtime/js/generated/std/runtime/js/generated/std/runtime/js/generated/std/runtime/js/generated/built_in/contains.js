// AUTO-GENERATED FILE. DO NOT EDIT.
// source: src/pytra/built_in/contains.py
// generated-by: tools/gen_runtime_from_manifest.py

const {pyStr} = require("../../native/built_in/py_runtime.js");

function py_contains_dict_object(values, key) {
    let needle = pyStr(key);
    for (const cur of values) {
        if (cur === needle) {
            return true;
        }
    }
    return false;
}

function py_contains_list_object(values, key) {
    for (const cur of values) {
        if (cur === key) {
            return true;
        }
    }
    return false;
}

function py_contains_set_object(values, key) {
    for (const cur of values) {
        if (cur === key) {
            return true;
        }
    }
    return false;
}

function py_contains_str_object(values, key) {
    let needle = pyStr(key);
    let haystack = pyStr(values);
    let n = (haystack).length;
    let m = (needle).length;
    if (m === 0) {
        return true;
    }
    let i = 0;
    let last = n - m;
    while (i <= last) {
        let j = 0;
        let ok = true;
        while (j < m) {
            if (haystack[(((i + j) < 0) ? ((haystack).length + (i + j)) : (i + j))] !== needle[(((j) < 0) ? ((needle).length + (j)) : (j))]) {
                ok = false;
                break;
            }
            j += 1;
        }
        if (ok) {
            return true;
        }
        i += 1;
    }
    return false;
}

module.exports = {py_contains_dict_object, py_contains_list_object, py_contains_set_object, py_contains_str_object};
