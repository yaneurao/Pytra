#ifndef PYCS_CPP_MODULE_PYCPP_TRANSPILER_RUNTIME_H
#define PYCS_CPP_MODULE_PYCPP_TRANSPILER_RUNTIME_H

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

class PyCppTranspilerRuntime {
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
        std::vector<std::string> import_includes;
        bool pending_dataclass = false;

        for (std::size_t i = 0; i < lines.size(); ++i) {
            std::string t = trim(lines[i]);
            if (t.empty() || starts_with(t, "#")) {
                continue;
            }
            if (t == "@dataclass") {
                pending_dataclass = true;
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
            if (pending_dataclass && starts_with(t, "class ")) {
                body.push_back("@dataclass");
                pending_dataclass = false;
            } else if (!starts_with(t, "class ")) {
                pending_dataclass = false;
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
    enum class BlockKind {
        Generic,
        Class,
        Function,
    };

    struct Block {
        int py_indent;
        std::string close_token;
        BlockKind kind = BlockKind::Generic;
        std::string class_name;
        bool class_is_dataclass = false;
    };

    struct ClassAnalysis {
        std::vector<std::string> field_lines;
        std::vector<std::string> dataclass_ctor_lines;
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

    static std::vector<std::string> split_top_level(const std::string& s, char delim) {
        std::vector<std::string> out;
        std::string cur;
        int depth = 0;
        bool in_str = false;
        char quote = 0;
        for (char ch : s) {
            if (in_str) {
                cur.push_back(ch);
                if (ch == quote) {
                    in_str = false;
                }
                continue;
            }
            if (ch == '"' || ch == '\'') {
                in_str = true;
                quote = ch;
                cur.push_back(ch);
                continue;
            }
            if (ch == '(' || ch == '[' || ch == '{') {
                ++depth;
                cur.push_back(ch);
                continue;
            }
            if (ch == ')' || ch == ']' || ch == '}') {
                --depth;
                cur.push_back(ch);
                continue;
            }
            if (ch == delim && depth == 0) {
                out.push_back(trim(cur));
                cur.clear();
                continue;
            }
            cur.push_back(ch);
        }
        if (!trim(cur).empty()) {
            out.push_back(trim(cur));
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
        e = std::regex_replace(
            e,
            std::regex(R"(\b([A-Za-z_][A-Za-z0-9_]*)\s+in\s+([A-Za-z_][A-Za-z0-9_]*)\b)"),
            "py_in($1, $2)");
        e = std::regex_replace(e, std::regex(R"(\bself\.)"), "this->");

        {
            std::smatch im;
            static const std::regex re_ifexpr(R"(^(.+)\s+if\s+(.+)\s+else\s+(.+)$)");
            if (std::regex_match(e, im, re_ifexpr)) {
                return "(" + convert_expr(trim(im[2].str())) + " ? " +
                    convert_expr(trim(im[1].str())) + " : " +
                    convert_expr(trim(im[3].str())) + ")";
            }
        }

        // constructor call of known class -> RcHandle adopt rc_new
        for (const auto& c : class_names_) {
            const std::string pat = c + "\\s*\\((.*)\\)";
            std::regex cre("^" + pat + "$");
            std::smatch m;
            if (std::regex_match(e, m, cre)) {
                return "pycs::gc::RcHandle<" + c + ">::adopt(pycs::gc::rc_new<" + c + ">(" + trim(m[1].str()) + "))";
            }
        }

        auto lp = e.find('(');
        if (lp != std::string::npos && e.back() == ')') {
            std::string callee = trim(e.substr(0, lp));
            std::string args = e.substr(lp + 1, e.size() - lp - 2);
            if (!callee.empty() &&
                std::regex_match(callee, std::regex(R"(^[A-Za-z_][A-Za-z0-9_:\->\.]*$)"))) {
                auto parts = split_top_level(args, ',');
                std::vector<std::string> mapped;
                for (const auto& p : parts) {
                    if (!trim(p).empty()) {
                        mapped.push_back(convert_expr(p));
                    }
                }
                e = callee + "(" + join(mapped, ", ") + ")";
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

        {
            std::smatch cm;
            static const std::regex re_comp(R"(^\[\s*([A-Za-z_][A-Za-z0-9_]*)\s+for\s+([A-Za-z_][A-Za-z0-9_]*)\s+in\s+(.+)\]$)");
            if (std::regex_match(e, cm, re_comp)) {
                const std::string expr_var = cm[1].str();
                const std::string iter_var = cm[2].str();
                const std::string iter = trim(cm[3].str());
                if (expr_var == iter_var) {
                    return convert_expr(iter);
                }
            }
        }

        if (starts_with(e, "[") && e.size() >= 2 && e.back() == ']') {
            std::string inner = trim(e.substr(1, e.size() - 2));
            if (inner.empty()) {
                return "vector<int>{}";
            }
            auto items = split_top_level(inner, ',');
            std::vector<std::string> mapped;
            std::string elem_type;
            for (const auto& item : items) {
                mapped.push_back(convert_expr(item));
                const std::string t = infer_literal_type(item);
                if (!t.empty()) {
                    if (elem_type.empty()) elem_type = t;
                    else if (elem_type != t) elem_type = "int";
                }
            }
            if (elem_type.empty()) elem_type = "int";
            return "vector<" + elem_type + ">{ " + join(mapped, ", ") + " }";
        }

        if (starts_with(e, "{") && e.size() >= 2 && e.back() == '}' && e.find(':') != std::string::npos) {
            std::string inner = trim(e.substr(1, e.size() - 2));
            if (!inner.empty()) {
                auto items = split_top_level(inner, ',');
                std::vector<std::string> mapped;
                for (const auto& item : items) {
                    auto kv = split_top_level(item, ':');
                    if (kv.size() == 2) {
                        mapped.push_back("{ " + convert_expr(kv[0]) + ", " + convert_expr(kv[1]) + " }");
                    }
                }
                if (!mapped.empty()) {
                    return "{ " + join(mapped, ", ") + " }";
                }
            }
        }

        if (starts_with(e, "{") && e.size() >= 2 && e.back() == '}' && e.find(':') == std::string::npos) {
            std::string inner = trim(e.substr(1, e.size() - 2));
            if (inner.empty()) {
                return "unordered_set<int>{}";
            }
            auto items = split_top_level(inner, ',');
            std::vector<std::string> mapped;
            std::string elem_type;
            for (const auto& item : items) {
                mapped.push_back(convert_expr(item));
                const std::string t = infer_literal_type(item);
                if (!t.empty()) {
                    if (elem_type.empty()) elem_type = t;
                    else if (elem_type != t) elem_type = "int";
                }
            }
            if (elem_type.empty()) elem_type = "int";
            return "unordered_set<" + elem_type + ">{ " + join(mapped, ", ") + " }";
        }

        if (starts_with(e, "(") && e.size() >= 2 && e.back() == ')') {
            std::string inner = trim(e.substr(1, e.size() - 2));
            auto parts = split_top_level(inner, ',');
            if (parts.size() > 1) {
                std::vector<std::string> mapped;
                for (const auto& p : parts) {
                    mapped.push_back(convert_expr(p));
                }
                return "std::make_tuple(" + join(mapped, ", ") + ")";
            }
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

    static std::string infer_literal_type(const std::string& expr) {
        const std::string v = trim(expr);
        if (v.empty()) return "";
        if (v == "True" || v == "False" || v == "true" || v == "false") return "bool";
        if ((v.front() == '"' && v.back() == '"') || (v.front() == '\'' && v.back() == '\'')) return "string";
        if (std::regex_match(v, std::regex(R"(^-?[0-9]+$)"))) return "int";
        if (std::regex_match(v, std::regex(R"(^-?[0-9]+\.[0-9]+$)"))) return "double";
        return "";
    }

    std::unordered_map<std::string, std::string> parse_typed_params(const std::string& args) const {
        std::unordered_map<std::string, std::string> out;
        auto parts = split_top_level(args, ',');
        for (const auto& part : parts) {
            if (part.empty() || part == "self") continue;
            auto colon = part.find(':');
            if (colon == std::string::npos) continue;
            std::string name = trim(part.substr(0, colon));
            std::string rhs = trim(part.substr(colon + 1));
            auto eq = rhs.find('=');
            if (eq != std::string::npos) {
                rhs = trim(rhs.substr(0, eq));
            }
            if (!name.empty() && !rhs.empty()) {
                out[name] = map_annotation(rhs);
            }
        }
        return out;
    }

    ClassAnalysis analyze_class(
        const std::vector<std::string>& lines,
        std::size_t class_line,
        int class_indent,
        bool is_dataclass) const {
        ClassAnalysis res;
        std::unordered_map<std::string, std::string> instance_fields;
        std::unordered_map<std::string, std::string> dataclass_defaults;
        std::vector<std::string> dataclass_order;
        bool has_init = false;

        static const std::regex re_def(R"(^def\s+([A-Za-z_][A-Za-z0-9_]*)\((.*)\)\s*->\s*([^:]+):$)");
        static const std::regex re_ann_assign(R"(^([A-Za-z_][A-Za-z0-9_\.]*)\s*:\s*([^=]+?)(?:\s*=\s*(.+))?$)");
        static const std::regex re_assign(R"(^(.+?)\s*=\s*(.+)$)");

        std::size_t end = class_line + 1;
        while (end < lines.size()) {
            const std::string t = trim(lines[end]);
            if (!t.empty() && indent_of(lines[end]) <= class_indent - 1) {
                break;
            }
            ++end;
        }

        for (std::size_t i = class_line + 1; i < end; ++i) {
            const std::string t = trim(lines[i]);
            if (t.empty() || starts_with(t, "#")) continue;
            const int ind = indent_of(lines[i]);
            std::smatch m;

            if (ind == class_indent && std::regex_match(t, m, re_ann_assign)) {
                const std::string lhs = trim(m[1].str());
                const std::string typ = map_annotation(m[2].str());
                const bool has_val = m[3].matched;
                const std::string rhs = has_val ? convert_expr(m[3].str()) : "";
                if (lhs.find('.') != std::string::npos) {
                    continue;
                }
                if (is_dataclass) {
                    dataclass_order.push_back(lhs);
                    instance_fields[lhs] = typ;
                    if (has_val) {
                        dataclass_defaults[lhs] = rhs;
                    }
                } else {
                    res.field_lines.push_back(
                        indent(class_indent) + "inline static " + typ + " " + lhs + (has_val ? (" = " + rhs) : "") + ";");
                }
                continue;
            }

            if (!is_dataclass && ind == class_indent && std::regex_match(t, m, re_assign)) {
                const std::string lhs = trim(m[1].str());
                if (lhs.find('.') != std::string::npos) continue;
                const std::string rhs = convert_expr(m[2].str());
                res.field_lines.push_back(indent(class_indent) + "inline static auto " + lhs + " = " + rhs + ";");
                continue;
            }

            if (ind == class_indent && std::regex_match(t, m, re_def) && m[1].str() == "__init__") {
                has_init = true;
                const auto param_types = parse_typed_params(trim(m[2].str()));
                std::size_t j = i + 1;
                while (j < end) {
                    const std::string bt = trim(lines[j]);
                    if (!bt.empty() && indent_of(lines[j]) <= class_indent) {
                        break;
                    }
                    std::smatch bm;
                    if (std::regex_match(bt, bm, re_ann_assign)) {
                        std::string lhs = trim(bm[1].str());
                        if (starts_with(lhs, "self.")) {
                            std::string name = lhs.substr(5);
                            instance_fields[name] = map_annotation(bm[2].str());
                        }
                    } else if (std::regex_match(bt, bm, re_assign)) {
                        std::string lhs = trim(bm[1].str());
                        std::string rhs = trim(bm[2].str());
                        if (starts_with(lhs, "self.")) {
                            std::string name = lhs.substr(5);
                            if (!instance_fields.count(name)) {
                                std::string typ;
                                auto lit = infer_literal_type(rhs);
                                if (!lit.empty()) {
                                    typ = lit;
                                } else if (param_types.count(rhs)) {
                                    typ = param_types.at(rhs);
                                } else {
                                    typ = "int";
                                }
                                instance_fields[name] = typ;
                            }
                        }
                    }
                    ++j;
                }
            }
        }

        for (const auto& kv : instance_fields) {
            if (is_dataclass) {
                auto it = std::find(dataclass_order.begin(), dataclass_order.end(), kv.first);
                if (it == dataclass_order.end()) {
                    dataclass_order.push_back(kv.first);
                }
            }
            if (!is_dataclass || std::find(dataclass_order.begin(), dataclass_order.end(), kv.first) == dataclass_order.end()) {
                res.field_lines.push_back(indent(class_indent) + kv.second + " " + kv.first + ";");
            }
        }

        if (is_dataclass) {
            for (const auto& name : dataclass_order) {
                const std::string typ = instance_fields.count(name) ? instance_fields.at(name) : "int";
                auto d = dataclass_defaults.find(name);
                if (d == dataclass_defaults.end()) {
                    res.field_lines.push_back(indent(class_indent) + typ + " " + name + ";");
                } else {
                    res.field_lines.push_back(indent(class_indent) + typ + " " + name + " = " + d->second + ";");
                }
            }
            if (!has_init && !dataclass_order.empty()) {
                std::vector<std::string> params;
                res.dataclass_ctor_lines.push_back(indent(class_indent) + trim(lines[class_line]).substr(6));
                // replace trailing ':' and base part from class header
                if (!res.dataclass_ctor_lines.empty()) {
                    // no-op placeholder, constructor signature is appended below
                }
                res.dataclass_ctor_lines.clear();
                std::string class_header = trim(lines[class_line]);
                std::smatch mc;
                std::string class_name;
                static const std::regex re_class(R"(^class\s+([A-Za-z_][A-Za-z0-9_]*).*$)");
                if (std::regex_match(class_header, mc, re_class)) {
                    class_name = mc[1].str();
                }
                for (const auto& name : dataclass_order) {
                    const std::string typ = instance_fields.count(name) ? instance_fields.at(name) : "int";
                    auto d = dataclass_defaults.find(name);
                    if (d == dataclass_defaults.end()) {
                        params.push_back(typ + " " + name);
                    } else {
                        params.push_back(typ + " " + name + " = " + d->second);
                    }
                }
                res.dataclass_ctor_lines.push_back(indent(class_indent) + class_name + "(" + join(params, ", ") + ")");
                res.dataclass_ctor_lines.push_back(indent(class_indent) + "{");
                for (const auto& name : dataclass_order) {
                    res.dataclass_ctor_lines.push_back(indent(class_indent + 1) + "this->" + name + " = " + name + ";");
                }
                res.dataclass_ctor_lines.push_back(indent(class_indent) + "}");
            }
        }

        return res;
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
        bool pending_dataclass = false;

        if (in_class) {
            stack.push_back({base_indent, "", BlockKind::Class, class_name, class_is_dataclass});
        }

        auto close_until = [&](int ind) {
            while (!stack.empty() && ind < stack.back().py_indent) {
                if (!stack.back().close_token.empty()) {
                    out.push_back(indent(stack.back().py_indent - 1) + stack.back().close_token);
                }
                stack.pop_back();
            }
        };

        auto current_class = [&](int ind) -> const Block* {
            for (auto it = stack.rbegin(); it != stack.rend(); ++it) {
                if (it->kind == BlockKind::Class && ind >= it->py_indent) {
                    return &(*it);
                }
            }
            return nullptr;
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
            if (t == "@dataclass") {
                pending_dataclass = true;
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
                const bool is_dataclass = pending_dataclass;
                pending_dataclass = false;
                if (m[2].matched) {
                    base = m[2].str();
                }
                out.push_back(indent(ind) + "class " + c + " : public " + base);
                out.push_back(indent(ind) + "{");
                out.push_back(indent(ind) + "public:");
                const auto cls = analyze_class(lines, i, ind + 1, is_dataclass);
                for (const auto& line : cls.field_lines) {
                    out.push_back(line);
                }
                for (const auto& line : cls.dataclass_ctor_lines) {
                    out.push_back(line);
                }
                stack.push_back({ind + 1, "};", BlockKind::Class, c, is_dataclass});
                continue;
            }

            if (std::regex_match(t, m, re_def)) {
                std::string fn = m[1].str();
                std::string args = trim(m[2].str());
                std::string ret = map_annotation(m[3].str());
                const Block* cls = current_class(ind);
                const bool method_def = cls != nullptr && ind == cls->py_indent;

                std::vector<std::string> parts;
                if (!args.empty()) {
                    parts = split_top_level(args, ',');
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
                        std::string typ_raw = trim(p.substr(pos + 1));
                        auto eq = typ_raw.find('=');
                        std::string def;
                        if (eq != std::string::npos) {
                            def = trim(typ_raw.substr(eq + 1));
                            typ_raw = trim(typ_raw.substr(0, eq));
                        }
                        std::string typ = map_annotation(typ_raw);
                        if (!def.empty()) {
                            cargs.push_back(typ + " " + name + " = " + convert_expr(def));
                        } else {
                            cargs.push_back(typ + " " + name);
                        }
                    }
                }

                if (method_def && fn == "__init__") {
                    out.push_back(indent(ind) + cls->class_name + "(" + join(cargs, ", ") + ")");
                } else {
                    out.push_back(indent(ind) + ret + " " + fn + "(" + join(cargs, ", ") + ")");
                }
                out.push_back(indent(ind) + "{");
                stack.push_back({ind + 1, "}", BlockKind::Function, "", false});
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
                const Block* cls = current_class(ind);

                if (cls != nullptr && ind == cls->py_indent) {
                    // class-level fields are emitted from analyze_class()
                    continue;
                }

                if (starts_with(lhs, "self.")) {
                    out.push_back(indent(ind) + convert_expr(lhs) + " = " + rhs + ";");
                    continue;
                }

                out.push_back(indent(ind) + typ + " " + lhs + (has_val ? (" = " + rhs) : "") + ";");
                declared[lhs] = true;
                continue;
            }

            if (std::regex_match(t, m, re_assign)) {
                std::string lhs = trim(m[1].str());
                std::string rhs_src = trim(m[2].str());
                std::string rhs = convert_expr(rhs_src);
                const Block* cls = current_class(ind);

                if (cls != nullptr && ind == cls->py_indent && lhs.find("self.") != 0) {
                    // class-level fields are emitted from analyze_class()
                    continue;
                }

                if (lhs.find(',') != std::string::npos) {
                    auto parts = split_top_level(lhs, ',');
                    auto rhs_parts = split_top_level(rhs_src, ',');
                    if (rhs_parts.size() > 1) {
                        std::vector<std::string> mapped_rhs;
                        for (const auto& p : rhs_parts) {
                            mapped_rhs.push_back(convert_expr(p));
                        }
                        rhs = "std::make_tuple(" + join(mapped_rhs, ", ") + ")";
                    }
                    out.push_back(indent(ind) + "auto _tmp_tuple = " + rhs + ";");
                    for (std::size_t ti = 0; ti < parts.size(); ++ti) {
                        const std::string name = trim(parts[ti]);
                        if (!declared[name]) {
                            out.push_back(indent(ind) + "auto " + name + " = std::get<" + std::to_string(ti) + ">(_tmp_tuple);");
                            declared[name] = true;
                        } else {
                            out.push_back(indent(ind) + name + " = std::get<" + std::to_string(ti) + ">(_tmp_tuple);");
                        }
                    }
                    continue;
                }

                const std::string lhs_cpp = convert_expr(lhs);
                if (!declared[lhs] && !starts_with(lhs_cpp, "this->") && lhs_cpp.find("->") == std::string::npos && lhs_cpp.find("::") == std::string::npos) {
                    out.push_back(indent(ind) + "auto " + lhs_cpp + " = " + rhs + ";");
                    declared[lhs] = true;
                } else {
                    out.push_back(indent(ind) + lhs_cpp + " = " + rhs + ";");
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

#endif  // PYCS_CPP_MODULE_PYCPP_TRANSPILER_RUNTIME_H
