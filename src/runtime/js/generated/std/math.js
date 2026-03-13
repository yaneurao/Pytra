// AUTO-GENERATED FILE. DO NOT EDIT.
// source: src/pytra/std/math.py
// generated-by: tools/gen_runtime_from_manifest.py

const math_native = require("../../native/std/math_native.js");

function sqrt(x) {
    return math_native.sqrt(x);
}

function sin(x) {
    return math_native.sin(x);
}

function cos(x) {
    return math_native.cos(x);
}

function tan(x) {
    return math_native.tan(x);
}

function exp(x) {
    return math_native.exp(x);
}

function log(x) {
    return math_native.log(x);
}

function log10(x) {
    return math_native.log10(x);
}

function fabs(x) {
    return math_native.fabs(x);
}

function floor(x) {
    return math_native.floor(x);
}

function ceil(x) {
    return math_native.ceil(x);
}

function pow(x, y) {
    return math_native.pow(x, y);
}

const pi = math_native.pi;
const e = math_native.e;

module.exports = { pi, e, sqrt, sin, cos, tan, exp, log, log10, fabs, floor, ceil, pow };
