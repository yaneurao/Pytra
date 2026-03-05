// Python の math モジュール互換（最小実装）。

const pi = Math.PI;
const e = Math.E;

function sin(v) { return Math.sin(v); }
function cos(v) { return Math.cos(v); }
function tan(v) { return Math.tan(v); }
function sqrt(v) { return Math.sqrt(v); }
function exp(v) { return Math.exp(v); }
function log(v) { return Math.log(v); }
function log10(v) { return Math.log10(v); }
function fabs(v) { return Math.abs(v); }
function floor(v) { return Math.floor(v); }
function ceil(v) { return Math.ceil(v); }
function pow(a, b) { return Math.pow(a, b); }

module.exports = { pi, e, sin, cos, tan, sqrt, exp, log, log10, fabs, floor, ceil, pow };
