#ifndef PYCS_CPP_MODULE_NATIVE_PYCPP_TRANSPILER_H
#define PYCS_CPP_MODULE_NATIVE_PYCPP_TRANSPILER_H

#include <algorithm>
#include <filesystem>
#include <fstream>
#include <regex>
#include <sstream>
#include <stdexcept>
#include <string>
#include <unordered_map>
#include <vector>

namespace pycs::cpp_module {

class NativePyCppTranspiler {
public:
    // input_path の Python ファイルを C++ に変換して output_path へ書き出す。
    bool transpile_file(const std::string& input_path, const std::string& output_path, std::string* err) {
        std::ifstream ifs(input_path);
        if (!ifs) {
            if (err) {
                *err = "failed to open input: " + input_path;
            }
            return false;
        }

        std::vector<std::string> lines;
        std::string line;
        while (std::getline(ifs, line)) {
            lines.push_back(line);
        }

        std::vector<std::string> body;
        std::vector<std::string> main_body;
        std::unordered_map<int, bool> dataclass_next;
        std::vector<std::string> import_includes;

        for (std::size_t i = 0; i < lines.size(); ++i) {
            std::string t = trim(lines[i]);
            if (t.empty() || starts_with(t, "#")) {
                continue;
            }
            if (t == "@dataclass") {
                dataclass_next[static_cast<int>(i) + 1] = true;
                continue;
            }
            collect_import_include(t, import_includes);
            if (t == "if __name__ == \"__main__\":") {
                const int base = indent_of(lines[i]);
                ++i;
                while (i < lines.size()) {
                    if (trim(lines[i]).empty()) {
                        ++i;
                        continue;
                    }
                    if (indent_of(lines[i]) <= base) {
                        --i;
                        break;
                    }
                    main_body.push_back(lines[i]);
                    ++i;
                }
                continue;
            }
            body.push_back(lines[i]);
        }

        class_names_.clear();
        collect_class_names(body);

        std::vector<std::string> out;
        emit_preamble(out, import_includes);
        out.push_back("");

        std::vector<std::string> converted_body;
        if (!convert_block(body, 0, false, "", false, converted_body, err)) {
            return false;
        }
        out.insert(out.end(), converted_body.begin(), converted_body.end());

        out.push_back("");
        out.push_back("int main()");
        out.push_back("{");
        std::vector<std::string> converted_main;
        if (!convert_block(main_body, 1, false, "", false, converted_main, err)) {
            return false;
        }
        for (const auto& l : converted_main) {
            out.push_back(indent(1) + l);
        }
        out.push_back(indent(1) + "return 0;");
        out.push_back("}");

        std::ofstream ofs(output_path);
        if (!ofs) {
            if (err) {
                *err = "failed to open output: " + output_path;
            }
            return false;
        }
        for (const auto& l : out) {
            ofs << l << '\n';
        }
        return true;
    }

private:
    struct Block {
        int py_indent;
        std::string close_token;
    };

    std::vector<std::string> class_names_;

    static std::string trim(const std::string& s) {
        std::size_t b = 0;
        while (b < s.size() && (s[b] == ' ' || s[b] == '\t')) {
            ++b;
        }
        std::size_t e = s.size();
        while (e > b && (s[e - 1] == ' ' || s[e - 1] == '\t' || s[e - 1] == '\r')) {
            --e;
        }
        return s.substr(b, e - b);
    }

    static bool starts_with(const std::string& s, const std::string& prefix) {
        return s.size() >= prefix.size() && s.compare(0, prefix.size(), prefix) == 0;
    }

    static int indent_of(const std::string& s) {
        int n = 0;
        while (n < static_cast<int>(s.size()) && s[n] == ' ') {
            ++n;
        }
        return n / 4;
    }

    static std::string indent(int n) {
        return std::string(static_cast<std::size_t>(n * 4), ' ');
    }

    static std::vector<std::string> split(const std::string& s, char delim) {
        std::vector<std::string> out;
        std::stringstream ss(s);
        std::string part;
        while (std::getline(ss, part, delim)) {
            out.push_back(trim(part));
        }
        return out;
    }

    void collect_class_names(const std::vector<std::string>& lines) {
        static const std::regex re(R"(^class\s+([A-Za-z_][A-Za-z0-9_]*)(?:\(([A-Za-z_][A-Za-z0-9_]*)\))?:$)");
        std::smatch m;
        for (const auto& raw : lines) {
            const std::string t = trim(raw);
            if (std::regex_match(t, m, re)) {
                class_names_.push_back(m[1].str());
            }
        }
    }

    bool is_class_name(const std::string& name) const {
        return std::find(class_names_.begin(), class_names_.end(), name) != class_names_.end();
    }

    std::string map_annotation(std::string a) const {
        a = trim(a);
        if (a == "int") return "int";
        if (a == "float") return "double";
        if (a == "str") return "string";
        if (a == "bool") return "bool";
        if (a == "None") return "void";
        if (is_class_name(a)) return "pycs::gc::RcHandle<" + a + ">";

        if (starts_with(a, "list[") || starts_with(a, "List[")) {
            return "vector<" + map_annotation(a.substr(a.find('[') + 1, a.size() - a.find('[') - 2)) + ">";
        }
        if (starts_with(a, "set[") || starts_with(a, "Set[")) {
            return "unordered_set<" + map_annotation(a.substr(a.find('[') + 1, a.size() - a.find('[') - 2)) + ">";
        }
        if (starts_with(a, "dict[") || starts_with(a, "Dict[")) {
            std::string inner = a.substr(a.find('[') + 1, a.size() - a.find('[') - 2);
            auto parts = split(inner, ',');
            if (parts.size() == 2) {
                return "unordered_map<" + map_annotation(parts[0]) + ", " + map_annotation(parts[1]) + ">";
            }
            return "unordered_map<string, string>";
        }
        return a;
    }

    std::string convert_expr(std::string e) const {
        e = trim(e);
        if (e.empty()) return e;

        e = std::regex_replace(e, std::regex(R"(\bTrue\b)"), "true");
        e = std::regex_replace(e, std::regex(R"(\bFalse\b)"), "false");
        e = std::regex_replace(e, std::regex(R"(\bNone\b)"), "nullptr");
        e = std::regex_replace(e, std::regex(R"(\bnot\b)"), "!");
        e = std::regex_replace(e, std::regex(R"(\band\b)"), "&&");
        e = std::regex_replace(e, std::regex(R"(\bor\b)"), "||");
        e = std::regex_replace(e, std::regex(R"(\bself\.)"), "this->");

        // constructor call of known class -> RcHandle adopt rc_new
        for (const auto& c : class_names_) {
            const std::string pat = c + "\\s*\\((.*)\\)";
            std::regex cre("^" + pat + "$");
            std::smatch m;
            if (std::regex_match(e, m, cre)) {
                return "pycs::gc::RcHandle<" + c + ">::adopt(pycs::gc::rc_new<" + c + ">(" + trim(m[1].str()) + "))";
            }
        }

        // obj.method(...) / obj.field はポインタアクセスへ寄せる。
        // クラス名で始まる参照は static アクセスとして :: に置き換える。
        for (const auto& c : class_names_) {
            e = std::regex_replace(e, std::regex("\\b" + c + "\\."), c + "::");
        }
        e = std::regex_replace(
            e,
            std::regex(R"(\b([A-Za-z_][A-Za-z0-9_]*)\.([A-Za-z_][A-Za-z0-9_]*)\b)"),
            "$1->$2");

        // f-string (simple): f"a{b}c"
        if (starts_with(e, "f\"") && e.size() >= 3 && e.back() == '"') {
            std::string inner = e.substr(2, e.size() - 3);
            std::string out;
            std::size_t pos = 0;
            while (pos < inner.size()) {
                auto lb = inner.find('{', pos);
                if (lb == std::string::npos) {
                    std::string lit = inner.substr(pos);
                    if (!lit.empty()) {
                        if (!out.empty()) out += " + ";
                        out += '"' + lit + '"';
                    }
                    break;
                }
                if (lb > pos) {
                    std::string lit = inner.substr(pos, lb - pos);
                    if (!out.empty()) out += " + ";
                    out += '"' + lit + '"';
                }
                auto rb = inner.find('}', lb + 1);
                if (rb == std::string::npos) {
                    break;
                }
                std::string key = trim(inner.substr(lb + 1, rb - lb - 1));
                if (!out.empty()) out += " + ";
                out += "py_to_string(" + convert_expr(key) + ")";
                pos = rb + 1;
            }
            if (out.empty()) {
                out = "\"\"";
            }
            return "(" + out + ")";
        }

        return e;
    }

    void emit_preamble(std::vector<std::string>& out, const std::vector<std::string>& import_includes) {
        out.push_back("#include \"cpp_module/gc.h\"");
        out.push_back("#include \"cpp_module/py_runtime_modules.h\"");
        out.push_back("#include <iostream>");
        out.push_back("#include <sstream>");
        out.push_back("#include <stdexcept>");
        out.push_back("#include <string>");
        out.push_back("#include <tuple>");
        out.push_back("#include <unordered_map>");
        out.push_back("#include <unordered_set>");
        out.push_back("#include <vector>");
        for (const auto& inc : import_includes) {
            out.push_back(inc);
        }
        out.push_back("");
        out.push_back("using namespace std;");
        out.push_back("using namespace pycs::gc;");
        out.push_back("");
        out.push_back("template <typename T>");
        out.push_back("string py_to_string(const T& value)");
        out.push_back("{");
        out.push_back("    std::ostringstream oss;");
        out.push_back("    oss << value;");
        out.push_back("    return oss.str();");
        out.push_back("}");
        out.push_back("");
        out.push_back("template <typename T>");
        out.push_back("bool py_in(const T& key, const unordered_set<T>& s)");
        out.push_back("{");
        out.push_back("    return s.find(key) != s.end();");
        out.push_back("}");
        out.push_back("");
        out.push_back("template <typename K, typename V>");
        out.push_back("bool py_in(const K& key, const unordered_map<K, V>& m)");
        out.push_back("{");
        out.push_back("    return m.find(key) != m.end();");
        out.push_back("}");
        out.push_back("");
        out.push_back("template <typename T>");
        out.push_back("bool py_in(const T& key, const vector<T>& v)");
        out.push_back("{");
        out.push_back("    for (const auto& item : v) {");
        out.push_back("        if (item == key) {");
        out.push_back("            return true;");
        out.push_back("        }");
        out.push_back("    }");
        out.push_back("    return false;");
        out.push_back("}");
        out.push_back("");
        out.push_back("inline void py_print()");
        out.push_back("{");
        out.push_back("    std::cout << std::endl;");
        out.push_back("}");
        out.push_back("");
        out.push_back("template <typename T>");
        out.push_back("void py_print_one(const T& value)");
        out.push_back("{");
        out.push_back("    std::cout << value;");
        out.push_back("}");
        out.push_back("");
        out.push_back("inline void py_print_one(bool value)");
        out.push_back("{");
        out.push_back("    std::cout << (value ? \"True\" : \"False\");");
        out.push_back("}");
        out.push_back("");
        out.push_back("template <typename T, typename... Rest>");
        out.push_back("void py_print(const T& first, const Rest&... rest)");
        out.push_back("{");
        out.push_back("    py_print_one(first);");
        out.push_back("    ((std::cout << \" \", py_print_one(rest)), ...);");
        out.push_back("    std::cout << std::endl;");
        out.push_back("}");
    }

    bool convert_block(
        const std::vector<std::string>& lines,
        int base_indent,
        bool in_class,
        const std::string& class_name,
        bool class_is_dataclass,
        std::vector<std::string>& out,
        std::string* err) {
        std::vector<Block> stack;
        std::unordered_map<std::string, bool> declared;
        std::vector<std::pair<std::string, std::string>> dataclass_fields;
        bool has_ctor = false;

        auto close_until = [&](int ind) {
            while (!stack.empty() && ind < stack.back().py_indent) {
                out.push_back(indent(stack.back().py_indent - 1) + stack.back().close_token);
                stack.pop_back();
            }
        };

        static const std::regex re_class(R"(^class\s+([A-Za-z_][A-Za-z0-9_]*)(?:\(([A-Za-z_][A-Za-z0-9_]*)\))?:$)");
        static const std::regex re_def(R"(^def\s+([A-Za-z_][A-Za-z0-9_]*)\((.*)\)\s*->\s*([^:]+):$)");
        static const std::regex re_ann_assign(R"(^([A-Za-z_][A-Za-z0-9_\.]*)\s*:\s*([^=]+?)(?:\s*=\s*(.+))?$)");
        static const std::regex re_assign(R"(^(.+?)\s*=\s*(.+)$)");
        static const std::regex re_for(R"(^for\s+(.+)\s+in\s+(.+):$)");
        static const std::regex re_if(R"(^if\s+(.+):$)");
        static const std::regex re_elif(R"(^elif\s+(.+):$)");
        static const std::regex re_except(R"(^except(?:\s+([A-Za-z_][A-Za-z0-9_]*)(?:\s+as\s+([A-Za-z_][A-Za-z0-9_]*))?)?:$)");
        static const std::regex re_return(R"(^return(?:\s+(.+))?$)");
        static const std::regex re_raise(R"(^raise(?:\s+(.+))?$)");

        for (std::size_t i = 0; i < lines.size(); ++i) {
            const std::string raw = lines[i];
            const std::string t = trim(raw);
            if (t.empty() || starts_with(t, "#")) {
                continue;
            }
            if (starts_with(t, "import ") || starts_with(t, "from ")) {
                continue;
            }

            int ind = indent_of(raw);
            if (ind < base_indent) {
                continue;
            }
            close_until(ind);

            std::smatch m;

            if (std::regex_match(t, m, re_class)) {
                const std::string c = m[1].str();
                std::string base = "pycs::gc::PyObj";
                if (m[2].matched) {
                    base = m[2].str();
                }
                out.push_back(indent(ind) + "class " + c + " : public " + base);
                out.push_back(indent(ind) + "{");
                out.push_back(indent(ind) + "public:");
                stack.push_back({ind + 1, "};"});
                continue;
            }

            if (std::regex_match(t, m, re_def)) {
                std::string fn = m[1].str();
                std::string args = trim(m[2].str());
                std::string ret = map_annotation(m[3].str());

                std::vector<std::string> parts;
                if (!args.empty()) {
                    parts = split(args, ',');
                }
                std::vector<std::string> cargs;
                for (std::size_t ai = 0; ai < parts.size(); ++ai) {
                    auto p = parts[ai];
                    if (p == "self") {
                        continue;
                    }
                    auto pos = p.find(':');
                    if (pos == std::string::npos) {
                        cargs.push_back("auto " + trim(p));
                    } else {
                        std::string name = trim(p.substr(0, pos));
                        std::string typ = map_annotation(p.substr(pos + 1));
                        cargs.push_back(typ + " " + name);
                    }
                }

                if (in_class && fn == "__init__") {
                    out.push_back(indent(ind) + class_name + "(" + join(cargs, ", ") + ")");
                    has_ctor = true;
                } else {
                    out.push_back(indent(ind) + ret + " " + fn + "(" + join(cargs, ", ") + ")");
                }
                out.push_back(indent(ind) + "{");
                stack.push_back({ind + 1, "}"});
                continue;
            }

            if (std::regex_match(t, m, re_if)) {
                out.push_back(indent(ind) + "if (" + convert_expr(m[1].str()) + ")");
                out.push_back(indent(ind) + "{");
                stack.push_back({ind + 1, "}"});
                continue;
            }

            if (std::regex_match(t, m, re_elif)) {
                out.push_back(indent(ind) + "else if (" + convert_expr(m[1].str()) + ")");
                out.push_back(indent(ind) + "{");
                stack.push_back({ind + 1, "}"});
                continue;
            }

            if (t == "else:") {
                out.push_back(indent(ind) + "else");
                out.push_back(indent(ind) + "{");
                stack.push_back({ind + 1, "}"});
                continue;
            }

            if (std::regex_match(t, m, re_for)) {
                out.push_back(indent(ind) + "for (const auto& " + trim(m[1].str()) + " : " + convert_expr(m[2].str()) + ")");
                out.push_back(indent(ind) + "{");
                stack.push_back({ind + 1, "}"});
                continue;
            }

            if (t == "try:") {
                out.push_back(indent(ind) + "try");
                out.push_back(indent(ind) + "{");
                stack.push_back({ind + 1, "}"});
                continue;
            }

            if (std::regex_match(t, m, re_except)) {
                std::string ex_type = "std::exception";
                std::string ex_name = "ex";
                if (m[1].matched && m[1].str() != "Exception") {
                    ex_type = m[1].str();
                }
                if (m[2].matched) {
                    ex_name = m[2].str();
                }
                out.push_back(indent(ind) + "catch (const " + ex_type + "& " + ex_name + ")");
                out.push_back(indent(ind) + "{");
                stack.push_back({ind + 1, "}"});
                continue;
            }

            if (t == "finally:") {
                out.push_back(indent(ind) + "{");
                stack.push_back({ind + 1, "}"});
                continue;
            }

            if (t == "pass") {
                continue;
            }

            if (t == "break") {
                out.push_back(indent(ind) + "break;");
                continue;
            }

            if (t == "continue") {
                out.push_back(indent(ind) + "continue;");
                continue;
            }

            if (std::regex_match(t, m, re_return)) {
                if (m[1].matched) {
                    out.push_back(indent(ind) + "return " + convert_expr(m[1].str()) + ";");
                } else {
                    out.push_back(indent(ind) + "return;");
                }
                continue;
            }

            if (std::regex_match(t, m, re_raise)) {
                if (!m[1].matched) {
                    out.push_back(indent(ind) + "throw;");
                } else {
                    std::string e = trim(m[1].str());
                    if (starts_with(e, "Exception(")) {
                        auto inside = e.substr(std::string("Exception(").size());
                        if (!inside.empty() && inside.back() == ')') inside.pop_back();
                        out.push_back(indent(ind) + "throw std::runtime_error(py_to_string(" + convert_expr(inside) + "));\n");
                    } else {
                        out.push_back(indent(ind) + "throw std::runtime_error(py_to_string(" + convert_expr(e) + "));\n");
                    }
                }
                continue;
            }

            if (std::regex_match(t, m, re_ann_assign)) {
                const std::string lhs = trim(m[1].str());
                const std::string typ = map_annotation(m[2].str());
                const bool has_val = m[3].matched;
                const std::string rhs = has_val ? convert_expr(m[3].str()) : "";

                if (starts_with(lhs, "self.")) {
                    out.push_back(indent(ind) + convert_expr(lhs) + " = " + rhs + ";");
                    continue;
                }

                if (in_class && ind == base_indent) {
                    out.push_back(indent(ind) + "inline static " + typ + " " + lhs + (has_val ? (" = " + rhs) : "") + ";");
                    continue;
                }

                out.push_back(indent(ind) + typ + " " + lhs + (has_val ? (" = " + rhs) : "") + ";");
                declared[lhs] = true;
                continue;
            }

            if (std::regex_match(t, m, re_assign)) {
                std::string lhs = trim(m[1].str());
                std::string rhs = convert_expr(m[2].str());

                if (lhs.find(',') != std::string::npos) {
                    auto parts = split(lhs, ',');
                    out.push_back(indent(ind) + "auto _tmp_tuple = " + rhs + ";");
                    for (std::size_t ti = 0; ti < parts.size(); ++ti) {
                        out.push_back(indent(ind) + trim(parts[ti]) + " = std::get<" + std::to_string(ti) + ">(_tmp_tuple);");
                    }
                    continue;
                }

                if (!declared[lhs] && !starts_with(lhs, "this->") && lhs.find("->") == std::string::npos && lhs.find("::") == std::string::npos) {
                    out.push_back(indent(ind) + "auto " + convert_expr(lhs) + " = " + rhs + ";");
                    declared[lhs] = true;
                } else {
                    out.push_back(indent(ind) + convert_expr(lhs) + " = " + rhs + ";");
                }
                continue;
            }

            // expression statement
            if (starts_with(t, "print(")) {
                std::string inside = t.substr(6);
                if (!inside.empty() && inside.back() == ')') inside.pop_back();
                out.push_back(indent(ind) + "py_print(" + convert_expr(inside) + ");");
            } else {
                out.push_back(indent(ind) + convert_expr(t) + ";");
            }
        }

        while (!stack.empty()) {
            out.push_back(indent(stack.back().py_indent - 1) + stack.back().close_token);
            stack.pop_back();
        }

        return true;
    }

    static std::string join(const std::vector<std::string>& v, const std::string& sep) {
        std::string out;
        for (std::size_t i = 0; i < v.size(); ++i) {
            if (i > 0) out += sep;
            out += v[i];
        }
        return out;
    }

    static bool contains(const std::vector<std::string>& v, const std::string& s) {
        return std::find(v.begin(), v.end(), s) != v.end();
    }

    static void collect_import_include(const std::string& t, std::vector<std::string>& includes) {
        auto add = [&](const std::string& inc) {
            if (!contains(includes, inc)) {
                includes.push_back(inc);
            }
        };
        if (starts_with(t, "import ")) {
            std::string rest = trim(t.substr(7));
            auto mods = split(rest, ',');
            for (const auto& m0 : mods) {
                std::string m = m0;
                auto as_pos = m.find(" as ");
                if (as_pos != std::string::npos) {
                    m = trim(m.substr(0, as_pos));
                }
                if (m == "ast") {
                    add("#include \"cpp_module/ast.h\"");
                } else if (m == "pathlib") {
                    add("#include \"cpp_module/pathlib.h\"");
                } else if (m == "dataclasses") {
                    add("#include \"cpp_module/dataclasses.h\"");
                } else if (m == "typing") {
                    add("#include <any>");
                } else if (m == "math") {
                    add("#include <cmath>");
                }
            }
            return;
        }
        if (starts_with(t, "from ")) {
            std::string rest = trim(t.substr(5));
            auto import_pos = rest.find(" import ");
            if (import_pos == std::string::npos) {
                return;
            }
            std::string mod = trim(rest.substr(0, import_pos));
            if (mod == "ast") {
                add("#include \"cpp_module/ast.h\"");
            } else if (mod == "pathlib") {
                add("#include \"cpp_module/pathlib.h\"");
            } else if (mod == "dataclasses") {
                add("#include \"cpp_module/dataclasses.h\"");
            } else if (mod == "typing") {
                add("#include <any>");
            } else if (mod == "math") {
                add("#include <cmath>");
            }
        }
    }
};

}  // namespace pycs::cpp_module

#endif  // PYCS_CPP_MODULE_NATIVE_PYCPP_TRANSPILER_H
