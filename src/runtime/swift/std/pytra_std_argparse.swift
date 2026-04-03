import Foundation

typealias ArgValue = Any

class Namespace {
    var values: [AnyHashable: Any]

    init(_ values: [AnyHashable: Any] = [:]) {
        self.values = values
    }
}

final class _ArgSpec {
    let names: [String]
    let action: String
    let choices: [Any]
    let defaultValue: Any
    let helpText: String
    let isOptional: Bool
    let dest: String

    init(
        _ names: [String],
        _ action: String = "",
        _ choices: [Any] = [],
        _ defaultValue: Any = __pytra_none(),
        _ helpText: String = ""
    ) {
        self.names = names
        self.action = action
        self.choices = choices
        self.defaultValue = defaultValue
        self.helpText = helpText
        self.isOptional = !names.isEmpty && names[0].hasPrefix("-")
        if self.isOptional {
            self.dest = names.last!.trimmingCharacters(in: CharacterSet(charactersIn: "-")).replacingOccurrences(of: "-", with: "_")
        } else {
            self.dest = names[0]
        }
    }
}

final class ArgumentParser {
    let description: String
    var specs: [_ArgSpec]

    init(_ description: String = "") {
        self.description = description
        self.specs = []
    }

    func add_argument(
        _ name0: String,
        _ name1: String = "",
        _ name2: String = "",
        _ name3: String = "",
        _ help: String = "",
        _ action: String = "",
        _ choices: [Any] = [],
        _ default_: Any = __pytra_none()
    ) {
        var names: [String] = []
        for name in [name0, name1, name2, name3] where name != "" {
            names.append(name)
        }
        if names.isEmpty {
            fatalError("add_argument requires at least one name")
        }
        specs.append(_ArgSpec(names, action, choices, default_, help))
    }

    private func fail(_ msg: String) {
        if msg != "" {
            sys_native_write_stderr("error: \(msg)\n")
        }
        sys_native_exit(Int64(2))
        fatalError("unreachable")
    }

    func parse_args(_ argv: Any = __pytra_none()) -> [AnyHashable: Any] {
        let args: [String]
        if __pytra_is_none(argv) {
            args = __pytra_sys_argv.map { __pytra_str($0) }
        } else {
            args = __pytra_as_list(argv).map { __pytra_str($0) }
        }

        var positionalSpecs: [_ArgSpec] = []
        var optionalSpecs: [_ArgSpec] = []
        var byName: [String: _ArgSpec] = [:]
        for spec in specs {
            if spec.isOptional {
                optionalSpecs.append(spec)
                for name in spec.names {
                    byName[name] = spec
                }
            } else {
                positionalSpecs.append(spec)
            }
        }

        var values: [AnyHashable: Any] = [:]
        for spec in specs {
            if spec.action == "store_true" {
                values[AnyHashable(spec.dest)] = __pytra_is_bool(spec.defaultValue) ? __pytra_truthy(spec.defaultValue) : false
            } else if !__pytra_is_none(spec.defaultValue) {
                values[AnyHashable(spec.dest)] = spec.defaultValue
            } else {
                values[AnyHashable(spec.dest)] = __pytra_none()
            }
        }

        var position = 0
        var i = 0
        while i < args.count {
            let token = args[i]
            if token.hasPrefix("-") {
                if byName[token] == nil {
                    fail("unknown option: \(token)")
                }
                let spec = byName[token]!
                if spec.action == "store_true" {
                    values[AnyHashable(spec.dest)] = true
                    i += 1
                    continue
                }
                if i + 1 >= args.count {
                    fail("missing value for option: \(token)")
                }
                let value = args[i + 1]
                if !spec.choices.isEmpty && !spec.choices.contains(where: { __pytra_str($0) == value }) {
                    fail("invalid choice for \(token): \(value)")
                }
                values[AnyHashable(spec.dest)] = value
                i += 2
                continue
            }
            if position >= positionalSpecs.count {
                fail("unexpected extra argument: \(token)")
            }
            values[AnyHashable(positionalSpecs[position].dest)] = token
            position += 1
            i += 1
        }

        if position < positionalSpecs.count {
            fail("missing required argument: \(positionalSpecs[position].dest)")
        }
        return values
    }
}
