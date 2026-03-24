// py_runtime.dart — Pytra Dart runtime helpers (Python built-in functions only)
// source: src/runtime/dart/built_in/py_runtime.dart
//
// §6: py_runtime provides ONLY Python built-in function equivalents.
// pytra.std.* functions (math, time, etc.) are in std/*_native.dart files.

import 'dart:io';

// --- print / repr ---
String pytraPrintRepr(dynamic v) {
  if (v == true) return 'True';
  if (v == false) return 'False';
  if (v == null) return 'None';
  return v.toString();
}

void pytraPrint(List<dynamic> args) {
  print(args.map(pytraPrintRepr).join(' '));
}

// --- Python or/and value-select semantics ---
dynamic pytraOr(dynamic a, dynamic b) => pytraTruthy(a) ? a : b;
dynamic pytraAnd(dynamic a, dynamic b) => pytraTruthy(a) ? b : a;

// --- truthiness ---
bool pytraTruthy(dynamic v) {
  if (v == null) return false;
  if (v is bool) return v;
  if (v is num) return v != 0;
  if (v is String) return v.isNotEmpty;
  if (v is List) return v.isNotEmpty;
  if (v is Map) return v.isNotEmpty;
  return true;
}

// --- contains (in operator) ---
bool pytraContains(dynamic container, dynamic value) {
  if (container is List) return container.contains(value);
  if (container is Map) return container.containsKey(value);
  if (container is Set) return container.contains(value);
  if (container is String) return container.contains(value.toString());
  return false;
}

// --- sequence repeat (* operator) ---
dynamic pytraRepeatSeq(dynamic a, dynamic b) {
  dynamic seq = a;
  dynamic count = b;
  if (a is num && b is! num) { seq = b; count = a; }
  int n = (count is num) ? count.toInt() : 0;
  if (n <= 0) {
    if (seq is String) return '';
    return [];
  }
  if (seq is String) return seq * n;
  if (seq is List) {
    var out = [];
    for (var i = 0; i < n; i++) { out.addAll(seq); }
    return out;
  }
  return (a is num ? a : 0) * (b is num ? b : 0);
}

// --- string predicates ---
bool pytraStrIsdigit(String s) {
  if (s.isEmpty) return false;
  for (var i = 0; i < s.length; i++) {
    var c = s.codeUnitAt(i);
    if (c < 48 || c > 57) return false;
  }
  return true;
}

bool pytraStrIsalpha(String s) {
  if (s.isEmpty) return false;
  for (var i = 0; i < s.length; i++) {
    var c = s.codeUnitAt(i);
    if (!((c >= 65 && c <= 90) || (c >= 97 && c <= 122))) return false;
  }
  return true;
}

bool pytraStrIsspace(String s) {
  if (s.isEmpty) return false;
  for (var i = 0; i < s.length; i++) {
    var c = s.codeUnitAt(i);
    if (!(c == 32 || c == 9 || c == 10 || c == 13 || c == 11 || c == 12)) return false;
  }
  return true;
}

bool pytraStrIsalnum(String s) {
  if (s.isEmpty) return false;
  for (var i = 0; i < s.length; i++) {
    var c = s.codeUnitAt(i);
    if (!((c >= 48 && c <= 57) || (c >= 65 && c <= 90) || (c >= 97 && c <= 122))) return false;
  }
  return true;
}

// --- isinstance helper ---
bool pytraIsinstance(dynamic obj, dynamic classType) {
  if (obj == null) return false;
  return false;
}

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
