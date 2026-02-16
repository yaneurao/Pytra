// Python の math モジュール互換（最小実装）。

const pi = Math.PI;
const e = Math.E;

function sin(v) { return Math.sin(v); }
function cos(v) { return Math.cos(v); }
function sqrt(v) { return Math.sqrt(v); }
function exp(v) { return Math.exp(v); }
function floor(v) { return Math.floor(v); }

module.exports = { pi, e, sin, cos, sqrt, exp, floor };
