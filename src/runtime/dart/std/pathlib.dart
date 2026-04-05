// std/pathlib.dart — hand-written Path implementation for Dart
// source: src/runtime/dart/std/pathlib.dart
// Replaces EAST3-generated version which has Dart-incompatible patterns.

import 'dart:io';

class Path {
  String _value;
  Path(dynamic value) : _value = (value is Path) ? value._value : value.toString();

  @override
  String toString() => _value;

  Path operator /(dynamic rhs) {
    String other = (rhs is Path) ? rhs._value : rhs.toString();
    return Path('$_value/$other');
  }

  String get name {
    int idx = _value.lastIndexOf('/');
    return idx < 0 ? _value : _value.substring(idx + 1);
  }

  String get stem {
    String n = name;
    int idx = n.lastIndexOf('.');
    return idx <= 0 ? n : n.substring(0, idx);
  }

  String get suffix {
    String n = name;
    int idx = n.lastIndexOf('.');
    return idx <= 0 ? '' : n.substring(idx);
  }

  Path get parent {
    int idx = _value.lastIndexOf('/');
    return idx < 0 ? Path('.') : Path(_value.substring(0, idx));
  }

  bool exists() => File(_value).existsSync() || Directory(_value).existsSync();

  void mkdir([bool parents = false, bool existOk = false]) {
    try {
      Directory(_value).createSync(recursive: parents);
    } catch (e) {
      if (!existOk) rethrow;
    }
  }

  Path joinpath(
    String first, [
    dynamic second = null,
    dynamic third = null,
    dynamic fourth = null,
    dynamic fifth = null,
  ]) {
    Path result = Path('$_value/$first');
    final rest = <dynamic>[];
    for (final value in [second, third, fourth, fifth]) {
      if (value == null) {
        continue;
      }
      if (value is Iterable && value is! String) {
        rest.addAll(value);
      } else {
        rest.add(value);
      }
    }
    for (var part in rest) {
      String s = (part is Path) ? part._value : part.toString();
      result = Path('${result._value}/$s');
    }
    return result;
  }

  void write_text(String text, [String encoding = "utf-8"]) {
    File(_value).writeAsStringSync(text);
  }

  String read_text([String encoding = "utf-8"]) => File(_value).readAsStringSync();

  Path resolve() => Path(File(_value).absolute.path);

  Path relative_to(dynamic other) {
    String base = (other is Path) ? other._value : other.toString();
    String baseAbs = File(base).absolute.path;
    String selfAbs = File(_value).absolute.path;
    if (!baseAbs.endsWith('/')) baseAbs = '$baseAbs/';
    if (selfAbs.startsWith(baseAbs)) {
      return Path(selfAbs.substring(baseAbs.length));
    }
    throw Exception('$_value is not relative to $base');
  }
}
