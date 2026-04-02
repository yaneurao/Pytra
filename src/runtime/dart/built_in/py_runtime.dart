// py_runtime.dart — Pytra Dart runtime helpers (Python built-in functions only)
// source: src/runtime/dart/built_in/py_runtime.dart
//
// §6: py_runtime provides ONLY Python built-in function equivalents.
// pytra.std.* functions (math, time, etc.) are in std/*_native.dart files.

import 'dart:core';
import 'dart:core' as core;
import 'dart:collection';
import 'dart:io';

class PytraBaseException implements core.Exception {
  final String message;
  PytraBaseException([this.message = ""]);
  @override
  String toString() => message.isEmpty ? "BaseException" : message;
}

class PytraException extends PytraBaseException {
  PytraException([super.message = ""]);
  @override
  String toString() => message.isEmpty ? "Exception" : message;
}

class PytraRuntimeError extends PytraException {
  PytraRuntimeError([super.message = ""]);
}

class PytraValueError extends PytraException {
  PytraValueError([super.message = ""]);
}

class PytraTypeError extends PytraException {
  PytraTypeError([super.message = ""]);
}

class PytraIndexError extends PytraException {
  PytraIndexError([super.message = ""]);
}

class PytraKeyError extends PytraException {
  PytraKeyError([super.message = ""]);
}

typedef BaseException = PytraBaseException;
typedef Exception = PytraException;
typedef RuntimeError = PytraRuntimeError;
typedef ValueError = PytraValueError;
typedef TypeError = PytraTypeError;
typedef IndexError = PytraIndexError;
typedef KeyError = PytraKeyError;
typedef AssertionError = PytraException;
typedef AttributeError = PytraException;
typedef FileNotFoundError = PytraException;
typedef IOError = PytraException;
typedef ImportError = PytraException;
typedef NameError = PytraException;
typedef NotImplementedError = PytraException;
typedef OSError = PytraException;
typedef OverflowError = PytraException;
typedef PermissionError = PytraException;
typedef RecursionError = PytraException;
typedef StopIteration = PytraException;
typedef ZeroDivisionError = PytraException;

// --- print / repr ---
String pytraPrintRepr(dynamic v) {
  return pytraStr(v);
}

String _pytraRepr(dynamic v) {
  if (v == true) return 'True';
  if (v == false) return 'False';
  if (v == null) return 'None';
  if (v is String) {
    return "'" + v.replaceAll("\\", "\\\\").replaceAll("'", "\\'") + "'";
  }
  if (v is List) return "[" + v.map(_pytraRepr).join(", ") + "]";
  if (v is Map) {
    return "{" + v.entries.map((e) => _pytraRepr(e.key) + ": " + _pytraRepr(e.value)).join(", ") + "}";
  }
  if (v is Set) {
    if (v.isEmpty) return "set()";
    return "{" + v.map(_pytraRepr).join(", ") + "}";
  }
  return v.toString();
}

String pytraStr(dynamic v) {
  if (v is String) return v;
  return _pytraRepr(v);
}

String pytraTupleStr(List<dynamic> v) {
  if (v.length == 1) return "(" + _pytraRepr(v[0]) + ",)";
  return "(" + v.map(_pytraRepr).join(", ") + ")";
}

List<dynamic> pytraTupleView(dynamic v) {
  if (v is List<dynamic>) return v;
  if (v is List) return List<dynamic>.from(v);
  if (v is Iterable) return List<dynamic>.from(v);
  return <dynamic>[];
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

bool pytraDeepEquals(dynamic a, dynamic b) {
  if (identical(a, b)) return true;
  if (a is List && b is List) {
    if (a.length != b.length) return false;
    for (var i = 0; i < a.length; i++) {
      if (!pytraDeepEquals(a[i], b[i])) return false;
    }
    return true;
  }
  if (a is Set && b is Set) {
    if (a.length != b.length) return false;
    for (final item in a) {
      if (!b.contains(item)) return false;
    }
    return true;
  }
  if (a is Map && b is Map) {
    if (a.length != b.length) return false;
    for (final entry in a.entries) {
      if (!b.containsKey(entry.key)) return false;
      if (!pytraDeepEquals(entry.value, b[entry.key])) return false;
    }
    return true;
  }
  return a == b;
}

int pytraDeepHash(dynamic value) {
  if (value is List) {
    return Object.hashAll(value.map(pytraDeepHash));
  }
  if (value is Set) {
    final hashes = value.map(pytraDeepHash).toList()..sort();
    return Object.hashAll(hashes);
  }
  if (value is Map) {
    final entries = value.entries
        .map((e) => Object.hash(pytraDeepHash(e.key), pytraDeepHash(e.value)))
        .toList()
      ..sort();
    return Object.hashAll(entries);
  }
  return value.hashCode;
}

LinkedHashSet<dynamic> pytraNewSet() {
  return LinkedHashSet<dynamic>(equals: pytraDeepEquals, hashCode: pytraDeepHash);
}

LinkedHashSet<dynamic> pytraSetLiteral(List<dynamic> elements) {
  final out = pytraNewSet();
  out.addAll(elements);
  return out;
}

LinkedHashSet<dynamic> pytraSetFrom(dynamic iterable) {
  final out = pytraNewSet();
  if (iterable is Iterable) {
    out.addAll(iterable);
  }
  return out;
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

dynamic pytraIndex(dynamic container, dynamic indexValue) {
  final index = indexValue is int ? indexValue : pytraInt(indexValue);
  if (container is List) {
    final idx = index < 0 ? container.length + index : index;
    if (idx < 0 || idx >= container.length) {
      throw IndexError("list index out of range");
    }
    return container[idx];
  }
  if (container is String) {
    final idx = index < 0 ? container.length + index : index;
    if (idx < 0 || idx >= container.length) {
      throw IndexError("string index out of range");
    }
    return container[idx];
  }
  return null;
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
