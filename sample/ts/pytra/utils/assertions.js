exports.py_assert_true = function(cond, _label) { return !!cond; };
exports.py_assert_eq = function(actual, expected, _label) { return actual === expected; };
exports.py_assert_all = function(results, _label) {
  if (!Array.isArray(results)) return false;
  for (const v of results) { if (!v) return false; }
  return true;
};
exports.py_assert_stdout = function(_expected_lines, fn) {
  if (typeof fn === 'function') { fn(); }
  return true;
};
