// std/math_native.dart — hand-written native implementation for pytra.std.math
// source: src/runtime/dart/std/math_native.dart

import 'dart:math' as _m;

final double pi = _m.pi;
final double e = _m.e;

double sqrt(num x) => _m.sqrt(x);
double sin(num x) => _m.sin(x);
double cos(num x) => _m.cos(x);
double tan(num x) => _m.tan(x);
double asin(num x) => _m.asin(x);
double acos(num x) => _m.acos(x);
double atan(num x) => _m.atan(x);
double atan2(num y, num x) => _m.atan2(y, x);
double exp(num x) => _m.exp(x);
double log(num x) => _m.log(x);
double floor(num x) => x.toDouble().floorToDouble();
double ceil(num x) => x.toDouble().ceilToDouble();
double fabs(num x) => x.toDouble().abs();
double pow(num x, num y) => _m.pow(x, y).toDouble();
double log10(num x) {
  double r = _m.log(x) / _m.ln10;
  // Correct floating point errors near exact integers (e.g. log10(1000.0) = 2.9999...)
  double rounded = r.roundToDouble();
  if ((r - rounded).abs() < 1e-10) return rounded;
  return r;
}
