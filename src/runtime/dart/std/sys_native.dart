// std/sys_native.dart — Pytra Dart sys native seam
// source: src/runtime/dart/std/sys_native.dart

import 'dart:io' as _io;

final List<String> argv = <String>[];
final List<String> path = <String>[];
final dynamic stderr = _io.stderr;
final dynamic stdout = _io.stdout;

void exit([dynamic code]) {
  _io.exit(code is int ? code : 0);
}

void set_argv(List<dynamic> values) {
  argv.clear();
  argv.addAll(values.map((v) => v.toString()));
}

void set_path(List<dynamic> values) {
  path.clear();
  path.addAll(values.map((v) => v.toString()));
}

void write_stderr(dynamic text) {
  _io.stderr.write(text.toString());
}

void write_stdout(dynamic text) {
  _io.stdout.write(text.toString());
}
