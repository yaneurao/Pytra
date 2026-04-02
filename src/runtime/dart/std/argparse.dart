import '../built_in/py_runtime.dart';
import '../std/sys.dart' as sys;

class Namespace {
  dynamic values;
  Namespace([dynamic values = null]) : values = values ?? {};
}

class _ArgSpec {
  late List<String> names;
  late String action;
  late List<String> choices;
  late dynamic default_;
  late String helpText;
  late bool isOptional;
  late String dest;

  _ArgSpec(
    dynamic names, [
    String action = "",
    dynamic choices = const [],
    dynamic default_ = null,
    String helpText = "",
  ]) {
    this.names = List<String>.from(names);
    this.action = action;
    this.choices = List<String>.from(choices);
    this.default_ = default_;
    this.helpText = helpText;
    isOptional = this.names.isNotEmpty && this.names.first.startsWith("-");
    if (isOptional) {
      dest = this.names.last.replaceFirst(RegExp(r"^-+"), "").replaceAll("-", "_");
    } else {
      dest = this.names.first;
    }
  }
}

class ArgumentParser {
  late String description;
  late List<_ArgSpec> _specs;

  ArgumentParser([String description = ""]) {
    this.description = description;
    _specs = <_ArgSpec>[];
  }

  void add_argument(
    String name0, [
    dynamic name1 = "",
    dynamic name2 = "",
    dynamic name3 = "",
    String help = "",
    String action = "",
    dynamic choices = const [],
    dynamic default_ = null,
  ]) {
    if (action == "" && help == "" && name1 is String && name1 == "store_true") {
      action = "store_true";
      name1 = "";
    }
    if (action == "" && help == "" && choices is List && choices.isEmpty && default_ == null && name2 is List) {
      choices = name2;
      name2 = "";
      if (name3 is String && name3 != "") {
        default_ = name3;
        name3 = "";
      }
    }

    final names = <String>[];
    if (name0 != "") names.add(name0);
    if (name1 is String && name1 != "") names.add(name1);
    if (name2 is String && name2 != "") names.add(name2);
    if (name3 is String && name3 != "") names.add(name3);
    if (names.isEmpty) {
      throw ValueError("add_argument requires at least one name");
    }
    _specs.add(_ArgSpec(names, action, choices, default_, help));
  }

  Never _fail(String msg) {
    if (msg != "") {
      sys.write_stderr("error: $msg\n");
    }
    throw SystemExit(2);
  }

  dynamic parse_args([dynamic argv = null]) {
    final args = argv == null ? List<dynamic>.from(pytraSlice(sys.argv, 1, null)) : List<dynamic>.from(argv);
    final specsPos = <_ArgSpec>[];
    final specsOpt = <_ArgSpec>[];
    for (final s in _specs) {
      if (s.isOptional) {
        specsOpt.add(s);
      } else {
        specsPos.add(s);
      }
    }

    final byName = <String, int>{};
    for (var i = 0; i < specsOpt.length; i++) {
      for (final name in specsOpt[i].names) {
        byName[name] = i;
      }
    }

    final values = <String, dynamic>{};
    for (final s in _specs) {
      if (s.action == "store_true") {
        values[s.dest] = s.default_ is bool ? s.default_ : false;
      } else {
        values[s.dest] = s.default_;
      }
    }

    var posI = 0;
    var i = 0;
    while (i < args.length) {
      final tok = pytraStr(args[i]);
      if (tok.startsWith("-")) {
        if (!byName.containsKey(tok)) {
          _fail("unknown option: $tok");
        }
        final spec = specsOpt[byName[tok] as int];
        if (spec.action == "store_true") {
          values[spec.dest] = true;
          i += 1;
          continue;
        }
        if (i + 1 >= args.length) {
          _fail("missing value for option: $tok");
        }
        final val = pytraStr(args[i + 1]);
        if (spec.choices.isNotEmpty && !pytraContains(spec.choices, val)) {
          _fail("invalid choice for $tok: $val");
        }
        values[spec.dest] = val;
        i += 2;
        continue;
      }

      if (posI >= specsPos.length) {
        _fail("unexpected extra argument: $tok");
      }
      final spec = specsPos[posI];
      values[spec.dest] = tok;
      posI += 1;
      i += 1;
    }

    if (posI < specsPos.length) {
      _fail("missing required argument: ${specsPos[posI].dest}");
    }
    return values;
  }
}
