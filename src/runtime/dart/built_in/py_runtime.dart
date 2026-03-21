// py_runtime.dart — Pytra Dart runtime helpers
// source: src/runtime/dart/built_in/py_runtime.dart
// generated-by: pytra dart native emitter

import 'dart:math' as math;
import 'dart:io';

// --- math helpers ---
double pyMathSqrt(dynamic x) => math.sqrt((x as num).toDouble());
double pyMathSin(dynamic x) => math.sin((x as num).toDouble());
double pyMathCos(dynamic x) => math.cos((x as num).toDouble());
double pyMathTan(dynamic x) => math.tan((x as num).toDouble());
double pyMathAsin(dynamic x) => math.asin((x as num).toDouble());
double pyMathAcos(dynamic x) => math.acos((x as num).toDouble());
double pyMathAtan(dynamic x) => math.atan((x as num).toDouble());
double pyMathAtan2(dynamic y, dynamic x) =>
    math.atan2((y as num).toDouble(), (x as num).toDouble());
double pyMathExp(dynamic x) => math.exp((x as num).toDouble());
double pyMathLog(dynamic x) => math.log((x as num).toDouble());
double pytraLog(dynamic x) => math.log((x as num).toDouble());
double pyMathFloor(dynamic x) => ((x as num).toDouble()).floorToDouble();
double pyMathCeil(dynamic x) => ((x as num).toDouble()).ceilToDouble();
double pyMathFabs(dynamic x) => ((x as num).toDouble()).abs();
double pyMathPi() => math.pi;
double pyMathE() => math.e;
dynamic pyMathPow(dynamic x, dynamic y) =>
    math.pow((x as num).toDouble(), (y as num).toDouble());

// --- perf counter ---
double pytraPerfCounter() =>
    DateTime.now().microsecondsSinceEpoch / 1000000.0;

// --- zip ---
List<List<dynamic>> pytraZip(dynamic a, dynamic b) {
  List<dynamic> la = (a is List) ? a : [];
  List<dynamic> lb = (b is List) ? b : [];
  int n = la.length < lb.length ? la.length : lb.length;
  List<List<dynamic>> out = [];
  for (int i = 0; i < n; i++) {
    out.add([la[i], lb[i]]);
  }
  return out;
}

// --- noop ---
void pytraNoop() {}

// --- int/float conversion ---
int pytraInt(dynamic v) {
  if (v is int) return v;
  if (v is double) return v.toInt();
  if (v is String) return int.parse(v);
  if (v is bool) return v ? 1 : 0;
  return 0;
}

double pytraFloat(dynamic v) {
  if (v is double) return v;
  if (v is int) return v.toDouble();
  if (v is String) return double.parse(v);
  if (v is bool) return v ? 1.0 : 0.0;
  return 0.0;
}

// --- slice ---
List<dynamic> pytraSlice(dynamic container, int start, dynamic end_) {
  if (container is List) {
    int len = container.length;
    int s = start < 0 ? (len + start) : start;
    if (s < 0) s = 0;
    if (end_ == null) return container.sublist(s);
    int e = (end_ is int) ? (end_ < 0 ? len + end_ : end_) : len;
    if (e > len) e = len;
    if (s >= e) return [];
    return container.sublist(s, e);
  }
  return [];
}

// --- string slice (handles negative indices like Python) ---
String pytraStrSlice(String s, int start, int? end_) {
  int len = s.length;
  int s0 = start < 0 ? (len + start) : start;
  if (s0 < 0) s0 = 0;
  if (s0 > len) s0 = len;
  if (end_ == null) return s.substring(s0);
  int e = end_! < 0 ? len + end_! : end_!;
  if (e < 0) e = 0;
  if (e > len) e = len;
  if (s0 >= e) return '';
  return s.substring(s0, e);
}

// --- bytearray/bytes ---
List<int> pytraBytearray([dynamic arg]) {
  if (arg == null) return <int>[];
  if (arg is int) return List<int>.filled(arg, 0);
  if (arg is List) return List<int>.from(arg);
  return <int>[];
}

List<int> pytraBytes([dynamic arg]) {
  if (arg == null) return List<int>.unmodifiable(<int>[]);
  if (arg is List) return List<int>.unmodifiable(arg);
  return List<int>.unmodifiable(<int>[]);
}

// --- file I/O (Python open/write/close bridge) ---
class PytraFile {
  final RandomAccessFile _raf;
  PytraFile(this._raf);
  void write(dynamic data) {
    if (data is List<int>) {
      _raf.writeFromSync(data);
    } else if (data is String) {
      _raf.writeStringSync(data);
    }
  }
  void close() => _raf.closeSync();
}

PytraFile open(String path, [String mode = "r"]) {
  FileMode fm = FileMode.read;
  if (mode == "wb" || mode == "w") fm = FileMode.write;
  if (mode == "ab" || mode == "a") fm = FileMode.append;
  return PytraFile(File(path).openSync(mode: fm));
}

// --- IO helpers (for sys.stderr/stdout stubs) ---
class PytraStderr {
  void write(dynamic text) => stderr.write(text);
}

class PytraStdout {
  void write(dynamic text) => stdout.write(text);
}
