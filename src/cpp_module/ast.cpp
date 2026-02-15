// このファイルは Python 風ソースを簡易ASTへ変換する実装です。
// トランスパイラ用途に必要な主要構文を対象に、インデントベースで解析します。

#include "cpp_module/ast.h"

#include <fstream>
#include <regex>
#include <sstream>
#include <stdexcept>

namespace pycs::cpp_module::ast {
namespace {

struct LineInfo {
    std::string raw;
    std::string text;
    int indent = 0;
    int line_no = 0;
};

std::string trim(const std::string& s) {
    std::size_t b = 0;
    while (b < s.size() && (s[b] == ' ' || s[b] == '\t' || s[b] == '\r')) {
        ++b;
    }
    std::size_t e = s.size();
    while (e > b && (s[e - 1] == ' ' || s[e - 1] == '\t' || s[e - 1] == '\r')) {
        --e;
    }
    return s.substr(b, e - b);
}

bool starts_with(const std::string& s, const std::string& p) {
    return s.size() >= p.size() && s.compare(0, p.size(), p) == 0;
}

int indent_of(const std::string& raw) {
    int n = 0;
    while (n < static_cast<int>(raw.size()) && raw[n] == ' ') {
        ++n;
    }
    return n / 4;
}

std::vector<std::string> split_top_level(const std::string& s, char delim) {
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
        } else if (ch == ')' || ch == ']' || ch == '}') {
            --depth;
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

ExprPtr raw_expr(const std::string& t) {
    return std::make_shared<RawExpr>(trim(t));
}

class Parser {
public:
    Parser(std::string filename, std::vector<LineInfo> lines)
        : filename_(std::move(filename)), lines_(std::move(lines)) {}

    ModulePtr parse_module() {
        auto m = std::make_shared<Module>();
        m->body = parse_block(0, true);
        return m;
    }

private:
    std::string filename_;
    std::vector<LineInfo> lines_;
    std::size_t pos_ = 0;

    [[noreturn]] void fail(const std::string& msg) const {
        int ln = pos_ < lines_.size() ? lines_[pos_].line_no : (lines_.empty() ? 1 : lines_.back().line_no);
        throw std::runtime_error("ast parse error (" + filename_ + ":" + std::to_string(ln) + "): " + msg);
    }

    bool eof() const { return pos_ >= lines_.size(); }

    bool skip_noise() {
        while (!eof()) {
            const auto& li = lines_[pos_];
            if (li.text.empty() || starts_with(li.text, "#")) {
                ++pos_;
                continue;
            }
            return true;
        }
        return false;
    }

    std::vector<StmtPtr> parse_block(int base_indent, bool top_level = false) {
        std::vector<StmtPtr> out;
        std::vector<std::string> pending_decorators;

        while (skip_noise()) {
            const auto& li = lines_[pos_];
            if (li.indent < base_indent) {
                break;
            }
            if (!top_level && li.indent > base_indent) {
                fail("unexpected indent");
            }
            if (li.indent > base_indent) {
                break;
            }

            if (starts_with(li.text, "@")) {
                pending_decorators.push_back(trim(li.text.substr(1)));
                ++pos_;
                continue;
            }

            auto stmt_node = parse_stmt(base_indent, pending_decorators);
            pending_decorators.clear();
            if (stmt_node) {
                out.push_back(stmt_node);
            }
        }
        return out;
    }

    StmtPtr parse_stmt(int base_indent, const std::vector<std::string>& decorators) {
        const auto& li = lines_[pos_];
        const std::string t = li.text;

        if (starts_with(t, "import ")) {
            return parse_import();
        }
        if (starts_with(t, "from ")) {
            return parse_import_from();
        }
        if (starts_with(t, "class ")) {
            return parse_class(base_indent, decorators);
        }
        if (starts_with(t, "def ")) {
            return parse_function(base_indent, decorators);
        }
        if (starts_with(t, "if ")) {
            return parse_if(base_indent);
        }
        if (starts_with(t, "for ")) {
            return parse_for(base_indent);
        }
        if (t == "try:") {
            return parse_try(base_indent);
        }
        if (starts_with(t, "return")) {
            return parse_return();
        }
        if (starts_with(t, "raise")) {
            return parse_raise();
        }
        if (t == "pass") {
            ++pos_;
            return std::make_shared<Pass>();
        }
        if (t == "break") {
            ++pos_;
            return std::make_shared<Break>();
        }
        if (t == "continue") {
            ++pos_;
            return std::make_shared<Continue>();
        }

        auto assign = parse_ann_assign_or_assign_or_expr();
        if (!assign) {
            fail("unsupported statement: " + t);
        }
        return assign;
    }

    StmtPtr parse_import() {
        auto node = std::make_shared<Import>();
        const std::string rest = trim(lines_[pos_].text.substr(7));
        for (const auto& part : split_top_level(rest, ',')) {
            auto a = std::make_shared<ImportAlias>();
            const auto as_pos = part.find(" as ");
            if (as_pos == std::string::npos) {
                a->name = trim(part);
            } else {
                a->name = trim(part.substr(0, as_pos));
                a->asname = trim(part.substr(as_pos + 4));
            }
            node->names.push_back(std::move(a));
        }
        ++pos_;
        return node;
    }

    StmtPtr parse_import_from() {
        static const std::regex re(R"(^from\s+([^\s]+)\s+import\s+(.+)$)");
        std::smatch m;
        if (!std::regex_match(lines_[pos_].text, m, re)) {
            fail("invalid from-import syntax");
        }
        auto node = std::make_shared<ImportFrom>();
        node->module = trim(m[1].str());
        for (const auto& part : split_top_level(trim(m[2].str()), ',')) {
            auto a = std::make_shared<ImportAlias>();
            const auto as_pos = part.find(" as ");
            if (as_pos == std::string::npos) {
                a->name = trim(part);
            } else {
                a->name = trim(part.substr(0, as_pos));
                a->asname = trim(part.substr(as_pos + 4));
            }
            node->names.push_back(std::move(a));
        }
        ++pos_;
        return node;
    }

    StmtPtr parse_class(int base_indent, const std::vector<std::string>& decorators) {
        static const std::regex re(R"(^class\s+([A-Za-z_][A-Za-z0-9_]*)(?:\(([A-Za-z_][A-Za-z0-9_\.]*)\))?:$)");
        std::smatch m;
        const std::string t = lines_[pos_].text;
        if (!std::regex_match(t, m, re)) {
            fail("invalid class syntax");
        }
        auto node = std::make_shared<ClassDef>();
        node->name = m[1].str();
        if (m[2].matched) {
            node->base = m[2].str();
        }
        node->decorators = decorators;

        ++pos_;
        node->body = parse_block(base_indent + 1);
        return node;
    }

    std::shared_ptr<arg> parse_arg(const std::string& text) {
        auto a = std::make_shared<arg>();
        std::string t = trim(text);
        auto eq = t.find('=');
        if (eq != std::string::npos) {
            t = trim(t.substr(0, eq));
        }
        auto col = t.find(':');
        if (col == std::string::npos) {
            a->arg = trim(t);
            a->annotation = nullptr;
        } else {
            a->arg = trim(t.substr(0, col));
            a->annotation = raw_expr(trim(t.substr(col + 1)));
        }
        return a;
    }

    StmtPtr parse_function(int base_indent, const std::vector<std::string>& decorators) {
        static const std::regex re(R"(^def\s+([A-Za-z_][A-Za-z0-9_]*)\((.*)\)\s*->\s*([^:]+):$)");
        std::smatch m;
        const std::string t = lines_[pos_].text;
        if (!std::regex_match(t, m, re)) {
            fail("invalid function syntax");
        }

        auto node = std::make_shared<FunctionDef>();
        node->name = trim(m[1].str());
        node->returns = raw_expr(trim(m[3].str()));
        node->args = std::make_shared<arguments>();
        node->decorators = decorators;

        const std::string args = trim(m[2].str());
        if (!args.empty()) {
            for (const auto& p : split_top_level(args, ',')) {
                node->args->args.push_back(parse_arg(p));
            }
        }

        ++pos_;
        node->body = parse_block(base_indent + 1);
        return node;
    }

    StmtPtr parse_if(int base_indent) {
        auto parse_cond = [](const std::string& t, const std::string& kw) -> std::string {
            std::string rest = trim(t.substr(kw.size()));
            if (!rest.empty() && rest.back() == ':') {
                rest.pop_back();
            }
            return trim(rest);
        };

        auto node = std::make_shared<If>();
        node->test = raw_expr(parse_cond(lines_[pos_].text, "if"));
        ++pos_;
        node->body = parse_block(base_indent + 1);

        std::vector<StmtPtr>* tail = &node->orelse;
        while (skip_noise()) {
            const auto& li = lines_[pos_];
            if (li.indent != base_indent) {
                break;
            }
            if (starts_with(li.text, "elif ")) {
                auto elif_node = std::make_shared<If>();
                elif_node->test = raw_expr(parse_cond(li.text, "elif"));
                ++pos_;
                elif_node->body = parse_block(base_indent + 1);
                tail->push_back(elif_node);
                tail = &elif_node->orelse;
                continue;
            }
            if (li.text == "else:") {
                ++pos_;
                *tail = parse_block(base_indent + 1);
            }
            break;
        }
        return node;
    }

    StmtPtr parse_for(int base_indent) {
        static const std::regex re(R"(^for\s+(.+)\s+in\s+(.+):$)");
        std::smatch m;
        if (!std::regex_match(lines_[pos_].text, m, re)) {
            fail("invalid for syntax");
        }
        auto node = std::make_shared<For>();
        node->target = raw_expr(m[1].str());
        node->iter = raw_expr(m[2].str());

        ++pos_;
        node->body = parse_block(base_indent + 1);
        if (skip_noise()) {
            const auto& li = lines_[pos_];
            if (li.indent == base_indent && li.text == "else:") {
                ++pos_;
                node->orelse = parse_block(base_indent + 1);
            }
        }
        return node;
    }

    StmtPtr parse_try(int base_indent) {
        auto node = std::make_shared<Try>();
        ++pos_;
        node->body = parse_block(base_indent + 1);

        static const std::regex re_except(R"(^except(?:\s+([A-Za-z_][A-Za-z0-9_\.]*)(?:\s+as\s+([A-Za-z_][A-Za-z0-9_]*))?)?:$)");

        while (skip_noise()) {
            const auto& li = lines_[pos_];
            if (li.indent != base_indent) {
                break;
            }
            std::smatch m;
            if (std::regex_match(li.text, m, re_except)) {
                auto h = std::make_shared<ExceptHandler>();
                if (m[1].matched) {
                    h->type = raw_expr(m[1].str());
                } else {
                    h->type = nullptr;
                }
                if (m[2].matched) h->name = m[2].str();
                ++pos_;
                h->body = parse_block(base_indent + 1);
                node->handlers.push_back(std::move(h));
                continue;
            }
            if (li.text == "finally:") {
                ++pos_;
                node->finalbody = parse_block(base_indent + 1);
            }
            break;
        }
        return node;
    }

    StmtPtr parse_return() {
        auto node = std::make_shared<Return>();
        const std::string t = lines_[pos_].text;
        if (t.size() > 6) {
            node->value = raw_expr(trim(t.substr(6)));
        } else {
            node->value = nullptr;
        }
        ++pos_;
        return node;
    }

    StmtPtr parse_raise() {
        auto node = std::make_shared<Raise>();
        const std::string t = lines_[pos_].text;
        if (t.size() > 5) {
            node->exc = raw_expr(trim(t.substr(5)));
        } else {
            node->exc = nullptr;
        }
        ++pos_;
        return node;
    }

    StmtPtr parse_ann_assign_or_assign_or_expr() {
        const std::string t = lines_[pos_].text;

        static const std::regex re_ann(R"(^([A-Za-z_][A-Za-z0-9_\.]*)\s*:\s*([^=]+?)(?:\s*=\s*(.+))?$)");
        std::smatch ma;
        if (std::regex_match(t, ma, re_ann)) {
            auto n = std::make_shared<AnnAssign>();
            n->target = raw_expr(ma[1].str());
            n->annotation = raw_expr(ma[2].str());
            if (ma[3].matched) {
                n->value = raw_expr(ma[3].str());
            }
            ++pos_;
            return n;
        }

        static const std::regex re_assign(R"(^(.+?)\s*=\s*(.+)$)");
        std::smatch ms;
        if (std::regex_match(t, ms, re_assign)) {
            auto n = std::make_shared<Assign>();
            for (const auto& target : split_top_level(ms[1].str(), ',')) {
                n->targets.push_back(raw_expr(target));
            }
            n->value = raw_expr(ms[2].str());
            ++pos_;
            return n;
        }

        auto n = std::make_shared<ExprStmt>();
        n->value = raw_expr(t);
        ++pos_;
        return n;
    }
};

std::vector<LineInfo> build_lines(const std::string& source) {
    std::vector<LineInfo> out;
    std::istringstream iss(source);
    std::string line;
    int ln = 1;
    while (std::getline(iss, line)) {
        LineInfo li;
        li.raw = line;
        li.text = trim(line);
        li.indent = indent_of(line);
        li.line_no = ln++;
        out.push_back(std::move(li));
    }
    return out;
}

}  // namespace

ModulePtr parse(const std::string& source, const std::string& filename) {
    Parser p(filename, build_lines(source));
    return p.parse_module();
}

ModulePtr parse_file(const std::string& path) {
    std::ifstream ifs(path);
    if (!ifs) {
        throw std::runtime_error("ast parse_file failed to open: " + path);
    }
    std::ostringstream oss;
    oss << ifs.rdbuf();
    return parse(oss.str(), path);
}

}  // namespace pycs::cpp_module::ast
