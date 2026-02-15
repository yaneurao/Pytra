#include "cpp_module/ast.h"
#include "cpp_module/dataclasses.h"
#include "cpp_module/gc.h"
#include "cpp_module/pathlib.h"
#include "cpp_module/py_runtime_modules.h"
#include <algorithm>
#include <any>
#include <iostream>
#include <sstream>
#include <stdexcept>
#include <string>
#include <tuple>
#include <type_traits>
#include <unordered_map>
#include <unordered_set>
#include <vector>

using namespace std;
using namespace pycs::gc;

class TranspileError : public std::exception
{
public:
};

class Scope : public pycs::gc::PyObj
{
public:
    unordered_set<string> declared;
    Scope(unordered_set<string> declared)
    {
        this->declared = declared;
    }
};

class CppTranspiler : public pycs::gc::PyObj
{
public:
    inline static string INDENT = "    ";
    unordered_set<string> class_names;
    unordered_set<string> exception_class_names;
    string current_class_name;
    unordered_set<string> current_static_fields;
    CppTranspiler()
    {
        this->class_names = unordered_set<string>{};
        this->exception_class_names = unordered_set<string>{};
        this->current_class_name = "";
        this->current_static_fields = unordered_set<string>{};
    }
    void transpile_file(auto input_path, auto output_path)
    {
        auto source = input_path->read_text("utf-8");
        auto tree = pycs::cpp_module::ast::parse(source, py_to_string(input_path));
        auto cpp = this->transpile_module(tree);
        output_path->write_text(cpp, "utf-8");
    }
    string transpile_module(pycs::cpp_module::ast::ModulePtr module)
    {
        vector<string> function_defs = {};
        vector<string> class_defs = {};
        vector<pycs::cpp_module::ast::StmtPtr> top_level_body = {};
        unordered_set<string> include_lines = {"#include <algorithm>", "#include <any>", "#include <iostream>", "#include <string>", "#include <vector>", "#include <unordered_map>", "#include <unordered_set>", "#include <tuple>", "#include <sstream>", "#include <stdexcept>", "#include <type_traits>", "#include \"cpp_module/gc.h\"", "#include \"cpp_module/py_runtime_modules.h\""};
        this->class_names = unordered_set<string>{};
        this->exception_class_names = unordered_set<string>{};
        for (const auto& stmt : module->body)
        {
            if (auto __cast_stmt = py_cast<pycs::cpp_module::ast::ClassDef>(stmt))
            {
                auto stmt = __cast_stmt;
                this->class_names.insert(stmt->name);
                if (((py_len(stmt->bases) > 0) && py_isinstance<pycs::cpp_module::ast::Name>(stmt->bases[0]) && (stmt->bases[0]->id == "Exception")))
                {
                    this->exception_class_names.insert(stmt->name);
                }
            }
        }
        for (const auto& stmt : module->body)
        {
            if (auto __cast_stmt = py_cast<pycs::cpp_module::ast::FunctionDef>(stmt))
            {
                auto stmt = __cast_stmt;
                function_defs.push_back(this->transpile_function(stmt, false));
            }
            else
            {
                if (auto __cast_stmt = py_cast<pycs::cpp_module::ast::ClassDef>(stmt))
                {
                    auto stmt = __cast_stmt;
                    class_defs.push_back(this->transpile_class(stmt));
                }
                else
                {
                    if (py_isinstance_any<decltype(stmt), pycs::cpp_module::ast::Import, pycs::cpp_module::ast::ImportFrom>(stmt))
                    {
                        include_lines = py_set_union(include_lines, this->_includes_from_import(stmt));
                    }
                    else
                    {
                        top_level_body.push_back(stmt);
                    }
                }
            }
        }
        vector<pycs::cpp_module::ast::StmtPtr> main_stmts = {};
        for (const auto& stmt : top_level_body)
        {
            if (this->_is_main_guard(stmt))
            {
                py_extend(main_stmts, stmt->body);
            }
            else
            {
                main_stmts.push_back(stmt);
            }
        }
        auto main_func = this->transpile_main(main_stmts);
        auto parts = py_sorted(include_lines);
        parts.push_back("");
        parts.push_back("using namespace std;");
        parts.push_back("using namespace pycs::gc;");
        parts.push_back("");
        for (const auto& cls : class_defs)
        {
            py_extend(parts, py_splitlines(cls));
            parts.push_back("");
        }
        for (const auto& fn : function_defs)
        {
            py_extend(parts, py_splitlines(fn));
            parts.push_back("");
        }
        py_extend(parts, py_splitlines(main_func));
        parts.push_back("");
        return py_join("\n", parts);
    }
    unordered_set<string> _includes_from_import(pycs::cpp_module::ast::StmtPtr stmt)
    {
        unordered_set<string> includes = unordered_set<string>{};
        vector<string> modules = {};
        if (auto __cast_stmt = py_cast<pycs::cpp_module::ast::Import>(stmt))
        {
            auto stmt = __cast_stmt;
            for (const auto& alias : stmt->names)
            {
                modules.push_back(alias->name);
            }
        }
        else
        {
            if (auto __cast_stmt = py_cast<pycs::cpp_module::ast::ImportFrom>(stmt))
            {
                auto stmt = __cast_stmt;
                if (stmt->module)
                {
                    modules.push_back(stmt->module);
                }
            }
        }
        for (const auto& mod : modules)
        {
            if ((mod == "math"))
            {
                includes.insert("#include <cmath>");
            }
            else
            {
                if ((mod == "ast"))
                {
                    includes.insert("#include \"cpp_module/ast.h\"");
                }
                else
                {
                    if ((mod == "pathlib"))
                    {
                        includes.insert("#include \"cpp_module/pathlib.h\"");
                    }
                    else
                    {
                        if ((mod == "typing"))
                        {
                            includes.insert("#include <any>");
                        }
                        else
                        {
                            if ((mod == "dataclasses"))
                            {
                                includes.insert("#include \"cpp_module/dataclasses.h\"");
                            }
                        }
                    }
                }
            }
        }
        return includes;
    }
    string transpile_class(std::shared_ptr<pycs::cpp_module::ast::ClassDef> cls)
    {
        if ((py_len(cls->bases) > 1))
        {
            throw std::runtime_error(py_to_string(("Class '" + py_to_string(cls->name) + "' multiple inheritance is not supported")));
        }
        string base = " : public pycs::gc::PyObj";
        if ((py_len(cls->bases) > 0))
        {
            if ((!py_isinstance<pycs::cpp_module::ast::Name>(cls->bases[0])))
            {
                throw std::runtime_error(py_to_string(("Class '" + py_to_string(cls->name) + "' base class must be a simple name")));
            }
            if ((cls->bases[0]->id == "Exception"))
            {
                base = " : public std::exception";
            }
            else
            {
                base = (" : public " + py_to_string(cls->bases[0]->id));
            }
        }
        auto is_dataclass = this->_is_dataclass_class(cls);
        vector<string> static_fields = {};
        vector<tuple<string, string, bool, string>> dataclass_fields = {};
        unordered_set<string> static_field_names = unordered_set<string>{};
        vector<std::shared_ptr<pycs::cpp_module::ast::FunctionDef>> methods = {};
        for (const auto& stmt : cls->body)
        {
            if (auto __cast_stmt = py_cast<pycs::cpp_module::ast::FunctionDef>(stmt))
            {
                auto stmt = __cast_stmt;
                methods.push_back(stmt);
            }
            else
            {
                if (auto __cast_stmt = py_cast<pycs::cpp_module::ast::AnnAssign>(stmt))
                {
                    auto stmt = __cast_stmt;
                    if (is_dataclass)
                    {
                        dataclass_fields.push_back(this->_transpile_dataclass_field(stmt));
                    }
                    else
                    {
                        auto _tmp_tuple = this->_transpile_class_static_field(stmt);
                        auto field_line = std::get<0>(_tmp_tuple);
                        auto field_name = std::get<1>(_tmp_tuple);
                        static_fields.push_back(field_line);
                        static_field_names.insert(field_name);
                    }
                }
                else
                {
                    if (auto __cast_stmt = py_cast<pycs::cpp_module::ast::Assign>(stmt))
                    {
                        auto stmt = __cast_stmt;
                        auto _tmp_tuple = this->_transpile_class_static_assign(stmt);
                        auto field_line = std::get<0>(_tmp_tuple);
                        auto field_name = std::get<1>(_tmp_tuple);
                        static_fields.push_back(field_line);
                        static_field_names.insert(field_name);
                    }
                    else
                    {
                        if ((py_isinstance<pycs::cpp_module::ast::Expr>(stmt) && py_isinstance<pycs::cpp_module::ast::Constant>(stmt->value) && py_isinstance<string>(stmt->value->value)))
                        {
                            continue;
                        }
                        else
                        {
                            if (auto __cast_stmt = py_cast<pycs::cpp_module::ast::Pass>(stmt))
                            {
                                auto stmt = __cast_stmt;
                                continue;
                            }
                            else
                            {
                                throw std::runtime_error(py_to_string(("Unsupported class member in '" + py_to_string(cls->name) + "'")));
                            }
                        }
                    }
                }
            }
        }
        auto instance_fields = this->_collect_instance_fields(cls, static_field_names);
        auto has_init = false;
        for (const auto& method : methods)
        {
            if ((method->name == "__init__"))
            {
                has_init = true;
                break;
            }
        }
        vector<string> lines = {("class " + py_to_string(cls->name) + py_to_string(base)), "{", "public:"};
        for (const auto& static_field : static_fields)
        {
            py_extend(lines, this->_indent_block({static_field}));
        }
        for (const auto& _for_item : dataclass_fields)
        {
            auto field_type = std::get<0>(_for_item);
            auto field_name = std::get<1>(_for_item);
            auto has_default = std::get<2>(_for_item);
            auto default_value = std::get<3>(_for_item);
            if ((!has_default))
            {
                py_extend(lines, this->_indent_block({(py_to_string(field_type) + " " + py_to_string(field_name) + ";")}));
            }
            else
            {
                py_extend(lines, this->_indent_block({(py_to_string(field_type) + " " + py_to_string(field_name) + " = " + py_to_string(default_value) + ";")}));
            }
        }
        for (const auto& _for_item : instance_fields)
        {
            auto _ = std::get<0>(_for_item);
            auto field_type = std::get<1>(_for_item);
            auto field_name = std::get<2>(_for_item);
            py_extend(lines, this->_indent_block({(py_to_string(field_type) + " " + py_to_string(field_name) + ";")}));
        }
        if ((is_dataclass && (py_len(dataclass_fields) > 0) && (!has_init)))
        {
            vector<string> ctor_params = {};
            vector<string> ctor_body = {};
            for (const auto& _for_item : dataclass_fields)
            {
                auto field_type = std::get<0>(_for_item);
                auto field_name = std::get<1>(_for_item);
                auto has_default = std::get<2>(_for_item);
                auto default_value = std::get<3>(_for_item);
                if ((!has_default))
                {
                    ctor_params.push_back((py_to_string(field_type) + " " + py_to_string(field_name)));
                }
                else
                {
                    ctor_params.push_back((py_to_string(field_type) + " " + py_to_string(field_name) + " = " + py_to_string(default_value)));
                }
                ctor_body.push_back(("this->" + py_to_string(field_name) + " = " + py_to_string(field_name) + ";"));
            }
            py_extend(lines, this->_indent_block({(py_to_string(cls->name) + "(" + py_to_string(py_join(", ", ctor_params)) + ")")}));
            py_extend(lines, this->_indent_block({"{"}));
            py_extend(lines, this->_indent_block(this->_indent_block(ctor_body)));
            py_extend(lines, this->_indent_block({"}"}));
        }
        auto prev_class_name = this->current_class_name;
        auto prev_static_fields = this->current_static_fields;
        this->current_class_name = cls->name;
        this->current_static_fields = static_field_names;
        for (const auto& method : methods)
        {
            py_extend(lines, this->_indent_block(py_splitlines(this->transpile_function(method, true))));
        }
        this->current_class_name = prev_class_name;
        this->current_static_fields = prev_static_fields;
        lines.push_back("};");
        return py_join("\n", lines);
    }
    tuple<string, string> _transpile_class_static_field(pycs::cpp_module::ast::StmtPtr stmt)
    {
        if ((!py_isinstance<pycs::cpp_module::ast::Name>(stmt->target)))
        {
            throw std::runtime_error(py_to_string("Class field declaration must be a simple name"));
        }
        auto field_type = this->_map_annotation(stmt->annotation);
        auto field_name = stmt->target->id;
        if ((stmt->value == nullptr))
        {
            return std::make_tuple(("inline static " + py_to_string(field_type) + " " + py_to_string(field_name) + ";"), field_name);
        }
        return std::make_tuple(("inline static " + py_to_string(field_type) + " " + py_to_string(field_name) + " = " + py_to_string(this->transpile_expr(stmt->value)) + ";"), field_name);
    }
    tuple<string, string, bool, string> _transpile_dataclass_field(pycs::cpp_module::ast::StmtPtr stmt)
    {
        if ((!py_isinstance<pycs::cpp_module::ast::Name>(stmt->target)))
        {
            throw std::runtime_error(py_to_string("Dataclass field declaration must be a simple name"));
        }
        auto field_type = this->_map_annotation(stmt->annotation);
        auto field_name = stmt->target->id;
        if ((stmt->value == nullptr))
        {
            return std::make_tuple(field_type, field_name, false, "");
        }
        return std::make_tuple(field_type, field_name, true, this->transpile_expr(stmt->value));
    }
    tuple<string, string> _transpile_class_static_assign(pycs::cpp_module::ast::StmtPtr stmt)
    {
        if (((py_len(stmt->targets) != 1) || (!py_isinstance<pycs::cpp_module::ast::Name>(stmt->targets[0]))))
        {
            throw std::runtime_error(py_to_string("Class static assignment must be a simple name assignment"));
        }
        auto field_name = stmt->targets[0]->id;
        auto field_type = this->_infer_expr_cpp_type(stmt->value);
        if ((field_type == ""))
        {
            field_type = "auto";
        }
        return std::make_tuple(("inline static " + py_to_string(field_type) + " " + py_to_string(field_name) + " = " + py_to_string(this->transpile_expr(stmt->value)) + ";"), field_name);
    }
    vector<tuple<string, string, string>> _collect_instance_fields(pycs::cpp_module::ast::StmtPtr cls, unordered_set<string> static_field_names)
    {
        vector<tuple<string, string, string>> fields = {};
        unordered_set<string> seen = unordered_set<string>{};
        for (const auto& stmt : cls->body)
        {
            if (auto __cast_stmt = py_cast<pycs::cpp_module::ast::FunctionDef>(stmt))
            {
                auto stmt = __cast_stmt;
                auto init_fn = stmt;
                if ((init_fn->name != "__init__"))
                {
                    continue;
                }
                unordered_map<string, string> arg_types = {};
                auto idx = 0;
                for (const auto& arg : init_fn->args->args)
                {
                    if (((idx == 0) && (arg->arg == "self")))
                    {
                        idx = (idx + 1);
                        continue;
                    }
                    if ((arg->annotation != nullptr))
                    {
                        // unsupported assignment
                    }
                    idx = (idx + 1);
                }
                for (const auto& init_stmt : init_fn->body)
                {
                    string field_name = "";
                    string field_type = "";
                    if (auto __cast_init_stmt = py_cast<pycs::cpp_module::ast::AnnAssign>(init_stmt))
                    {
                        auto init_stmt = __cast_init_stmt;
                        auto target_expr = init_stmt->target;
                        if (auto __cast_target_expr = py_cast<pycs::cpp_module::ast::Attribute>(target_expr))
                        {
                            auto target_expr = __cast_target_expr;
                            auto attr_target = target_expr;
                            if ((py_isinstance<pycs::cpp_module::ast::Name>(attr_target->value) && (attr_target->value->id == "self")))
                            {
                                field_name = attr_target->attr;
                                field_type = this->_map_annotation(init_stmt->annotation);
                            }
                        }
                    }
                    else
                    {
                        if (auto __cast_init_stmt = py_cast<pycs::cpp_module::ast::Assign>(init_stmt))
                        {
                            auto init_stmt = __cast_init_stmt;
                            if ((py_len(init_stmt->targets) == 1))
                            {
                                auto target_expr = init_stmt->targets[0];
                                if ((!py_isinstance<pycs::cpp_module::ast::Attribute>(target_expr)))
                                {
                                    continue;
                                }
                                auto attr_target = target_expr;
                                if ((py_isinstance<pycs::cpp_module::ast::Name>(attr_target->value) && (attr_target->value->id == "self")))
                                {
                                    field_name = attr_target->attr;
                                    field_type = this->_infer_type(init_stmt->value, arg_types);
                                }
                            }
                        }
                    }
                    if (((field_name == "") || (field_type == "")))
                    {
                        continue;
                    }
                    if (py_in(field_name, static_field_names))
                    {
                        continue;
                    }
                    if (py_in(field_name, seen))
                    {
                        continue;
                    }
                    seen.insert(field_name);
                    fields.push_back(std::make_tuple(cls->name, field_type, field_name));
                }
                return fields;
            }
        }
        return fields;
    }
    string _infer_type(pycs::cpp_module::ast::ExprPtr expr, unordered_map<string, string> arg_types)
    {
        if (auto __cast_expr = py_cast<pycs::cpp_module::ast::Name>(expr))
        {
            auto expr = __cast_expr;
            if (py_in(expr->id, arg_types))
            {
                return arg_types[expr->id];
            }
            return "";
        }
        if (auto __cast_expr = py_cast<pycs::cpp_module::ast::Constant>(expr))
        {
            auto expr = __cast_expr;
            return this->_infer_expr_cpp_type(expr);
        }
        if ((py_isinstance<pycs::cpp_module::ast::Call>(expr) && py_isinstance<pycs::cpp_module::ast::Name>(expr->func)))
        {
            if (py_in(expr->func->id, this->class_names))
            {
                return ("pycs::gc::RcHandle<" + py_to_string(expr->func->id) + ">");
            }
        }
        return "";
    }
    string _infer_expr_cpp_type(pycs::cpp_module::ast::ExprPtr expr)
    {
        if (auto __cast_expr = py_cast<pycs::cpp_module::ast::Constant>(expr))
        {
            auto expr = __cast_expr;
            if (py_isinstance<bool>(expr->value))
            {
                return "bool";
            }
            if (py_isinstance<int>(expr->value))
            {
                return "int";
            }
            if (py_isinstance<float>(expr->value))
            {
                return "double";
            }
            if (py_isinstance<string>(expr->value))
            {
                return "string";
            }
            return "";
        }
        return "";
    }
    string transpile_function(std::shared_ptr<pycs::cpp_module::ast::FunctionDef> fn, bool in_class)
    {
        auto is_constructor = (in_class && (fn->name == "__init__"));
        auto return_type = this->_map_annotation(fn->returns);
        vector<string> params = {};
        unordered_set<string> declared = unordered_set<string>{};
        auto idx = 0;
        for (const auto& arg : fn->args->args)
        {
            if ((in_class && (idx == 0) && (arg->arg == "self")))
            {
                declared.insert("self");
                idx = (idx + 1);
                continue;
            }
            params.push_back((py_to_string(this->_map_annotation(arg->annotation)) + " " + py_to_string(arg->arg)));
            declared.insert(arg->arg);
            idx = (idx + 1);
        }
        auto body_lines = this->transpile_statements(fn->body, pycs::gc::RcHandle<Scope>::adopt(pycs::gc::rc_new<Scope>(declared)));
        if (is_constructor)
        {
            if ((this->current_class_name == ""))
            {
                throw std::runtime_error(py_to_string("Constructor conversion requires class context"));
            }
            if ((return_type != "void"))
            {
                throw std::runtime_error(py_to_string("__init__ return type must be None"));
            }
            vector<string> lines = {(py_to_string(this->current_class_name) + "(" + py_to_string(py_join(", ", params)) + ")"), "{"};
            py_extend(lines, this->_indent_block(body_lines));
            lines.push_back("}");
            return py_join("\n", lines);
        }
        vector<string> lines = {(py_to_string(return_type) + " " + py_to_string(fn->name) + "(" + py_to_string(py_join(", ", params)) + ")"), "{"};
        py_extend(lines, this->_indent_block(body_lines));
        lines.push_back("}");
        return py_join("\n", lines);
    }
    string transpile_main(vector<pycs::cpp_module::ast::StmtPtr> body)
    {
        vector<string> lines = {"int main()", "{"};
        auto body_lines = this->transpile_statements(body, pycs::gc::RcHandle<Scope>::adopt(pycs::gc::rc_new<Scope>(unordered_set<string>{})));
        py_extend(lines, this->_indent_block(body_lines));
        py_extend(lines, this->_indent_block({"return 0;"}));
        lines.push_back("}");
        return py_join("\n", lines);
    }
    vector<string> transpile_statements(vector<pycs::cpp_module::ast::StmtPtr> stmts, pycs::gc::RcHandle<Scope> scope)
    {
        vector<string> lines = {};
        for (const auto& stmt : stmts)
        {
            if (py_isinstance_any<decltype(stmt), pycs::cpp_module::ast::Import, pycs::cpp_module::ast::ImportFrom>(stmt))
            {
                continue;
            }
            if ((py_isinstance<pycs::cpp_module::ast::Expr>(stmt) && py_isinstance<pycs::cpp_module::ast::Constant>(stmt->value) && py_isinstance<string>(stmt->value->value)))
            {
                continue;
            }
            if (auto __cast_stmt = py_cast<pycs::cpp_module::ast::Return>(stmt))
            {
                auto stmt = __cast_stmt;
                if ((stmt->value == nullptr))
                {
                    lines.push_back("return;");
                }
                else
                {
                    lines.push_back(("return " + py_to_string(this->transpile_expr(stmt->value)) + ";"));
                }
            }
            else
            {
                if (auto __cast_stmt = py_cast<pycs::cpp_module::ast::Expr>(stmt))
                {
                    auto stmt = __cast_stmt;
                    auto expr = this->transpile_expr(stmt->value);
                    lines.push_back((py_to_string(expr) + ";"));
                }
                else
                {
                    if (auto __cast_stmt = py_cast<pycs::cpp_module::ast::AnnAssign>(stmt))
                    {
                        auto stmt = __cast_stmt;
                        py_extend(lines, this->_transpile_ann_assign(stmt, scope));
                    }
                    else
                    {
                        if (auto __cast_stmt = py_cast<pycs::cpp_module::ast::Assign>(stmt))
                        {
                            auto stmt = __cast_stmt;
                            py_extend(lines, this->_transpile_assign(stmt, scope));
                        }
                        else
                        {
                            if (auto __cast_stmt = py_cast<pycs::cpp_module::ast::If>(stmt))
                            {
                                auto stmt = __cast_stmt;
                                py_extend(lines, this->_transpile_if(stmt, scope));
                            }
                            else
                            {
                                if (auto __cast_stmt = py_cast<pycs::cpp_module::ast::For>(stmt))
                                {
                                    auto stmt = __cast_stmt;
                                    py_extend(lines, this->_transpile_for(stmt, scope));
                                }
                                else
                                {
                                    if (auto __cast_stmt = py_cast<pycs::cpp_module::ast::Try>(stmt))
                                    {
                                        auto stmt = __cast_stmt;
                                        py_extend(lines, this->_transpile_try(stmt, scope));
                                    }
                                    else
                                    {
                                        if (auto __cast_stmt = py_cast<pycs::cpp_module::ast::Raise>(stmt))
                                        {
                                            auto stmt = __cast_stmt;
                                            py_extend(lines, this->_transpile_raise(stmt));
                                        }
                                        else
                                        {
                                            if (auto __cast_stmt = py_cast<pycs::cpp_module::ast::Break>(stmt))
                                            {
                                                auto stmt = __cast_stmt;
                                                lines.push_back("break;");
                                            }
                                            else
                                            {
                                                if (auto __cast_stmt = py_cast<pycs::cpp_module::ast::Continue>(stmt))
                                                {
                                                    auto stmt = __cast_stmt;
                                                    lines.push_back("continue;");
                                                }
                                                else
                                                {
                                                    if (auto __cast_stmt = py_cast<pycs::cpp_module::ast::Pass>(stmt))
                                                    {
                                                        auto stmt = __cast_stmt;
                                                        continue;
                                                    }
                                                    else
                                                    {
                                                        throw std::runtime_error(py_to_string("Unsupported statement"));
                                                    }
                                                }
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }
        return lines;
    }
    vector<string> _transpile_ann_assign(pycs::cpp_module::ast::StmtPtr stmt, pycs::gc::RcHandle<Scope> scope)
    {
        auto target_expr = stmt->target;
        if (auto __cast_target_expr = py_cast<pycs::cpp_module::ast::Attribute>(target_expr))
        {
            auto target_expr = __cast_target_expr;
            auto attr_target = target_expr;
            if ((py_isinstance<pycs::cpp_module::ast::Name>(attr_target->value) && (attr_target->value->id == "self")))
            {
                if ((stmt->value == nullptr))
                {
                    throw std::runtime_error(py_to_string("Annotated assignment to self attributes requires an initializer"));
                }
                return {(py_to_string(this->transpile_expr(attr_target)) + " = " + py_to_string(this->transpile_expr(stmt->value)) + ";")};
            }
            throw std::runtime_error(py_to_string("Annotated assignment to attributes is not supported"));
        }
        if ((!py_isinstance<pycs::cpp_module::ast::Name>(stmt->target)))
        {
            throw std::runtime_error(py_to_string("Only simple annotated assignments are supported"));
        }
        auto name = stmt->target->id;
        auto cpp_type = this->_map_annotation(stmt->annotation);
        if ((stmt->value == nullptr))
        {
            scope->declared.insert(name);
            return {(py_to_string(cpp_type) + " " + py_to_string(name) + ";")};
        }
        scope->declared.insert(name);
        return {(py_to_string(cpp_type) + " " + py_to_string(name) + " = " + py_to_string(this->transpile_expr(stmt->value)) + ";")};
    }
    vector<string> _transpile_assign(pycs::cpp_module::ast::StmtPtr stmt, pycs::gc::RcHandle<Scope> scope)
    {
        if ((py_len(stmt->targets) != 1))
        {
            return {"// unsupported assignment"};
        }
        if (py_isinstance<pycs::cpp_module::ast::Tuple>(stmt->targets[0]))
        {
            auto tuple_target = stmt->targets[0];
            for (const auto& elt : tuple_target->elts)
            {
                if ((!py_isinstance<pycs::cpp_module::ast::Name>(elt)))
                {
                    return {"// unsupported tuple assignment"};
                }
            }
            auto tmp_name = "_tmp_tuple";
            vector<string> lines = {("auto " + py_to_string(tmp_name) + " = " + py_to_string(this->transpile_expr(stmt->value)) + ";")};
            auto i = 0;
            for (const auto& elt : tuple_target->elts)
            {
                auto name = elt->id;
                if ((!py_in(name, scope->declared)))
                {
                    scope->declared.insert(name);
                    lines.push_back(("auto " + py_to_string(name) + " = std::get<" + py_to_string(i) + ">(" + py_to_string(tmp_name) + ");"));
                }
                else
                {
                    lines.push_back((py_to_string(name) + " = std::get<" + py_to_string(i) + ">(" + py_to_string(tmp_name) + ");"));
                }
                i = (i + 1);
            }
            return lines;
        }
        if (py_isinstance<pycs::cpp_module::ast::Attribute>(stmt->targets[0]))
        {
            auto target = this->transpile_expr(stmt->targets[0]);
            return {(py_to_string(target) + " = " + py_to_string(this->transpile_expr(stmt->value)) + ";")};
        }
        if ((!py_isinstance<pycs::cpp_module::ast::Name>(stmt->targets[0])))
        {
            return {"// unsupported assignment"};
        }
        auto name = stmt->targets[0]->id;
        if ((!py_in(name, scope->declared)))
        {
            scope->declared.insert(name);
            return {("auto " + py_to_string(name) + " = " + py_to_string(this->transpile_expr(stmt->value)) + ";")};
        }
        return {(py_to_string(name) + " = " + py_to_string(this->transpile_expr(stmt->value)) + ";")};
    }
    vector<string> _transpile_for(std::shared_ptr<pycs::cpp_module::ast::For> stmt, pycs::gc::RcHandle<Scope> scope)
    {
        vector<string> tuple_names = {};
        string target_name = "";
        if (py_isinstance<pycs::cpp_module::ast::Name>(stmt->target))
        {
            target_name = stmt->target->id;
        }
        else
        {
            if (py_isinstance<pycs::cpp_module::ast::Tuple>(stmt->target))
            {
                auto only_names = true;
                for (const auto& elt : stmt->target->elts)
                {
                    if ((!py_isinstance<pycs::cpp_module::ast::Name>(elt)))
                    {
                        only_names = false;
                        break;
                    }
                }
                if (only_names)
                {
                    target_name = "_for_item";
                    for (const auto& elt : stmt->target->elts)
                    {
                        tuple_names.push_back(elt->id);
                    }
                }
                else
                {
                    return {"// unsupported for-loop target"};
                }
            }
            else
            {
                return {"// unsupported for-loop target"};
            }
        }
        vector<string> lines = {("for (const auto& " + py_to_string(target_name) + " : " + py_to_string(this->transpile_expr(stmt->iter)) + ")"), "{"};
        auto body_scope = pycs::gc::RcHandle<Scope>::adopt(pycs::gc::rc_new<Scope>(unordered_set<std::remove_cvref_t<decltype(*scope->declared.begin())>>(scope->declared.begin(), scope->declared.end())));
        body_scope->declared.insert(target_name);
        if ((py_len(tuple_names) > 0))
        {
            auto i = 0;
            for (const auto& elt_name : tuple_names)
            {
                py_extend(lines, this->_indent_block({("auto " + py_to_string(elt_name) + " = std::get<" + py_to_string(i) + ">(" + py_to_string(target_name) + ");")}));
                body_scope->declared.insert(elt_name);
                i = (i + 1);
            }
        }
        auto body_lines = this->transpile_statements(stmt->body, body_scope);
        py_extend(lines, this->_indent_block(body_lines));
        lines.push_back("}");
        if ((py_len(stmt->orelse) > 0))
        {
            lines.push_back("// for-else is not directly supported; else body emitted below");
            py_extend(lines, this->transpile_statements(stmt->orelse, pycs::gc::RcHandle<Scope>::adopt(pycs::gc::rc_new<Scope>(unordered_set<std::remove_cvref_t<decltype(*scope->declared.begin())>>(scope->declared.begin(), scope->declared.end())))));
        }
        return lines;
    }
    vector<string> _transpile_try(std::shared_ptr<pycs::cpp_module::ast::Try> stmt, pycs::gc::RcHandle<Scope> scope)
    {
        vector<string> lines = {"try", "{"};
        py_extend(lines, this->_indent_block(this->transpile_statements(stmt->body, pycs::gc::RcHandle<Scope>::adopt(pycs::gc::rc_new<Scope>(unordered_set<std::remove_cvref_t<decltype(*scope->declared.begin())>>(scope->declared.begin(), scope->declared.end()))))));
        lines.push_back("}");
        for (const auto& handler : stmt->handlers)
        {
            string ex_type = "std::exception";
            if ((handler->type != nullptr))
            {
                if ((py_isinstance<pycs::cpp_module::ast::Name>(handler->type) && (handler->type->id == "Exception")))
                {
                    ex_type = "std::exception";
                }
                else
                {
                    ex_type = this->transpile_expr(handler->type);
                }
            }
            string ex_name = "ex";
            if ((handler->name != ""))
            {
                ex_name = handler->name;
            }
            lines.push_back(("catch (const " + py_to_string(ex_type) + "& " + py_to_string(ex_name) + ")"));
            lines.push_back("{");
            auto handler_declared = unordered_set<std::remove_cvref_t<decltype(*scope->declared.begin())>>(scope->declared.begin(), scope->declared.end());
            handler_declared.insert(ex_name);
            auto handler_scope = pycs::gc::RcHandle<Scope>::adopt(pycs::gc::rc_new<Scope>(handler_declared));
            py_extend(lines, this->_indent_block(this->transpile_statements(handler->body, handler_scope)));
            lines.push_back("}");
        }
        if ((py_len(stmt->finalbody) > 0))
        {
            lines.push_back("// finally is not directly supported in C++; emitted as plain block");
            lines.push_back("{");
            py_extend(lines, this->_indent_block(this->transpile_statements(stmt->finalbody, pycs::gc::RcHandle<Scope>::adopt(pycs::gc::rc_new<Scope>(unordered_set<std::remove_cvref_t<decltype(*scope->declared.begin())>>(scope->declared.begin(), scope->declared.end()))))));
            lines.push_back("}");
        }
        if ((py_len(stmt->orelse) > 0))
        {
            lines.push_back("// try-else is not directly supported; else body emitted below");
            py_extend(lines, this->transpile_statements(stmt->orelse, pycs::gc::RcHandle<Scope>::adopt(pycs::gc::rc_new<Scope>(unordered_set<std::remove_cvref_t<decltype(*scope->declared.begin())>>(scope->declared.begin(), scope->declared.end())))));
        }
        return lines;
    }
    vector<string> _transpile_raise(std::shared_ptr<pycs::cpp_module::ast::Raise> stmt)
    {
        if ((stmt->exc == nullptr))
        {
            return {"throw;"};
        }
        if ((py_isinstance<pycs::cpp_module::ast::Call>(stmt->exc) && (py_len(stmt->exc->args) > 0)))
        {
            return {("throw std::runtime_error(py_to_string(" + py_to_string(this->transpile_expr(stmt->exc->args[0])) + "));")};
        }
        return {("throw std::runtime_error(py_to_string(" + py_to_string(this->transpile_expr(stmt->exc)) + "));")};
    }
    vector<string> _transpile_if(std::shared_ptr<pycs::cpp_module::ast::If> stmt, pycs::gc::RcHandle<Scope> scope)
    {
        string cast_var = "";
        string cast_type = "";
        if ((py_isinstance<pycs::cpp_module::ast::Call>(stmt->test) && py_isinstance<pycs::cpp_module::ast::Name>(stmt->test->func) && (stmt->test->func->id == "isinstance") && (py_len(stmt->test->args) == 2) && py_isinstance<pycs::cpp_module::ast::Name>(stmt->test->args[0]) && (py_len(stmt->test->keywords) == 0)))
        {
            cast_var = stmt->test->args[0]->id;
            auto type_arg = stmt->test->args[1];
            if ((py_isinstance<pycs::cpp_module::ast::Attribute>(type_arg) && py_isinstance<pycs::cpp_module::ast::Name>(type_arg->value)))
            {
                cast_type = this->transpile_expr(type_arg);
            }
            else
            {
                if (auto __cast_type_arg = py_cast<pycs::cpp_module::ast::Name>(type_arg))
                {
                    auto type_arg = __cast_type_arg;
                    if (py_in(type_arg->id, this->class_names))
                    {
                        cast_type = type_arg->id;
                    }
                }
            }
        }
        vector<string> lines = {};
        if (((cast_var != "") && (cast_type != "")))
        {
            lines.push_back(("if (auto __cast_" + py_to_string(cast_var) + " = py_cast<" + py_to_string(cast_type) + ">(" + py_to_string(cast_var) + "))"));
            lines.push_back("{");
        }
        else
        {
            lines.push_back(("if (" + py_to_string(this->transpile_expr(stmt->test)) + ")"));
            lines.push_back("{");
        }
        vector<string> then_lines = this->transpile_statements(stmt->body, pycs::gc::RcHandle<Scope>::adopt(pycs::gc::rc_new<Scope>(unordered_set<std::remove_cvref_t<decltype(*scope->declared.begin())>>(scope->declared.begin(), scope->declared.end()))));
        if (((cast_var != "") && (cast_type != "")))
        {
            vector<string> prefixed_then_lines = {("auto " + py_to_string(cast_var) + " = __cast_" + py_to_string(cast_var) + ";")};
            py_extend(prefixed_then_lines, then_lines);
            then_lines = prefixed_then_lines;
        }
        py_extend(lines, this->_indent_block(then_lines));
        lines.push_back("}");
        if ((py_len(stmt->orelse) > 0))
        {
            lines.push_back("else");
            lines.push_back("{");
            auto else_lines = this->transpile_statements(stmt->orelse, pycs::gc::RcHandle<Scope>::adopt(pycs::gc::rc_new<Scope>(unordered_set<std::remove_cvref_t<decltype(*scope->declared.begin())>>(scope->declared.begin(), scope->declared.end()))));
            py_extend(lines, this->_indent_block(else_lines));
            lines.push_back("}");
        }
        return lines;
    }
    string transpile_expr(pycs::cpp_module::ast::ExprPtr expr)
    {
        if (auto __cast_expr = py_cast<pycs::cpp_module::ast::Name>(expr))
        {
            auto expr = __cast_expr;
            if ((expr->id == "self"))
            {
                return "this";
            }
            if ((expr->id == "True"))
            {
                return "true";
            }
            if ((expr->id == "False"))
            {
                return "false";
            }
            return expr->id;
        }
        if (auto __cast_expr = py_cast<pycs::cpp_module::ast::Attribute>(expr))
        {
            auto expr = __cast_expr;
            if ((py_isinstance<pycs::cpp_module::ast::Name>(expr->value) && (expr->value->id == "ast")))
            {
                return ("pycs::cpp_module::ast::" + py_to_string(expr->attr));
            }
            if ((py_isinstance<pycs::cpp_module::ast::Name>(expr->value) && (expr->value->id == "self") && (this->current_class_name != "") && py_in(expr->attr, this->current_static_fields)))
            {
                return (py_to_string(this->current_class_name) + "::" + py_to_string(expr->attr));
            }
            if ((py_isinstance<pycs::cpp_module::ast::Name>(expr->value) && (expr->value->id == "self")))
            {
                return ("this->" + py_to_string(expr->attr));
            }
            if ((py_isinstance<pycs::cpp_module::ast::Name>(expr->value) && py_in(expr->value->id, this->class_names)))
            {
                return (py_to_string(expr->value->id) + "::" + py_to_string(expr->attr));
            }
            return (py_to_string(this->transpile_expr(expr->value)) + "->" + py_to_string(expr->attr));
        }
        if (auto __cast_expr = py_cast<pycs::cpp_module::ast::Constant>(expr))
        {
            auto expr = __cast_expr;
            return this->_constant(expr->value);
        }
        if (auto __cast_expr = py_cast<pycs::cpp_module::ast::List>(expr))
        {
            auto expr = __cast_expr;
            vector<string> items = {};
            for (const auto& e : expr->elts)
            {
                items.push_back(this->transpile_expr(e));
            }
            return (("{" + py_join(", ", items)) + "}");
        }
        if (auto __cast_expr = py_cast<pycs::cpp_module::ast::Set>(expr))
        {
            auto expr = __cast_expr;
            vector<string> items = {};
            for (const auto& e : expr->elts)
            {
                items.push_back(this->transpile_expr(e));
            }
            return (("{" + py_join(", ", items)) + "}");
        }
        if (auto __cast_expr = py_cast<pycs::cpp_module::ast::Tuple>(expr))
        {
            auto expr = __cast_expr;
            vector<string> items = {};
            for (const auto& e : expr->elts)
            {
                items.push_back(this->transpile_expr(e));
            }
            return ("std::make_tuple(" + py_to_string(py_join(", ", items)) + ")");
        }
        if (auto __cast_expr = py_cast<pycs::cpp_module::ast::Dict>(expr))
        {
            auto expr = __cast_expr;
            vector<string> entries = {};
            for (const auto& _for_item : py_zip(expr->keys, expr->values))
            {
                auto k = std::get<0>(_for_item);
                auto v = std::get<1>(_for_item);
                if ((k == nullptr))
                {
                    continue;
                }
                entries.push_back(("{ " + py_to_string(this->transpile_expr(k)) + ", " + py_to_string(this->transpile_expr(v)) + " }"));
            }
            return (("{" + py_join(", ", entries)) + "}");
        }
        if (auto __cast_expr = py_cast<pycs::cpp_module::ast::BinOp>(expr))
        {
            auto expr = __cast_expr;
            auto left = this->transpile_expr(expr->left);
            auto right = this->transpile_expr(expr->right);
            return ("(" + py_to_string(left) + " " + py_to_string(this->_binop(expr->op)) + " " + py_to_string(right) + ")");
        }
        if (auto __cast_expr = py_cast<pycs::cpp_module::ast::UnaryOp>(expr))
        {
            auto expr = __cast_expr;
            return ("(" + py_to_string(this->_unaryop(expr->op)) + py_to_string(this->transpile_expr(expr->operand)) + ")");
        }
        if (auto __cast_expr = py_cast<pycs::cpp_module::ast::BoolOp>(expr))
        {
            auto expr = __cast_expr;
            auto op = this->_boolop(expr->op);
            vector<string> values = {};
            for (const auto& v : expr->values)
            {
                values.push_back(this->transpile_expr(v));
            }
            return (("(" + py_join((" " + py_to_string(op) + " "), values)) + ")");
        }
        if (auto __cast_expr = py_cast<pycs::cpp_module::ast::Compare>(expr))
        {
            auto expr = __cast_expr;
            if (((py_len(expr->ops) != 1) || (py_len(expr->comparators) != 1)))
            {
                return "/* chained-comparison */ false";
            }
            return this->_transpile_compare(expr->left, expr->ops[0], expr->comparators[0]);
        }
        if (auto __cast_expr = py_cast<pycs::cpp_module::ast::Call>(expr))
        {
            auto expr = __cast_expr;
            return this->_transpile_call(expr);
        }
        if (auto __cast_expr = py_cast<pycs::cpp_module::ast::Subscript>(expr))
        {
            auto expr = __cast_expr;
            return (py_to_string(this->transpile_expr(expr->value)) + "[" + py_to_string(this->transpile_expr(expr->slice)) + "]");
        }
        if (auto __cast_expr = py_cast<pycs::cpp_module::ast::IfExp>(expr))
        {
            auto expr = __cast_expr;
            return ("(" + py_to_string(this->transpile_expr(expr->test)) + " ? " + py_to_string(this->transpile_expr(expr->body)) + " : " + py_to_string(this->transpile_expr(expr->orelse)) + ")");
        }
        if (auto __cast_expr = py_cast<pycs::cpp_module::ast::JoinedStr>(expr))
        {
            auto expr = __cast_expr;
            return this->_transpile_joined_str(expr);
        }
        if (py_isinstance_any<decltype(expr), pycs::cpp_module::ast::ListComp, pycs::cpp_module::ast::SetComp, pycs::cpp_module::ast::GeneratorExp>(expr))
        {
            return "/* comprehension */ {}";
        }
        try
        {
            return this->_raw_expr_to_cpp(expr->as_text());
        }
        catch (const std::exception& None)
        {
        }
        throw std::runtime_error(py_to_string("Unsupported expression"));
    }
    string _transpile_call(pycs::cpp_module::ast::ExprPtr call)
    {
        vector<string> args_list = {};
        for (const auto& arg : call->args)
        {
            args_list.push_back(this->transpile_expr(arg));
        }
        for (const auto& kw : call->keywords)
        {
            args_list.push_back(this->transpile_expr(kw->value));
        }
        auto args = py_join(", ", args_list);
        if ((py_isinstance<pycs::cpp_module::ast::Name>(call->func) && (call->func->id == "print")))
        {
            if ((py_len(args_list) == 0))
            {
                return "py_print()";
            }
            return ("py_print(" + py_to_string(args) + ")");
        }
        if ((py_isinstance<pycs::cpp_module::ast::Name>(call->func) && (call->func->id == "len")))
        {
            return ("py_len(" + py_to_string(args) + ")");
        }
        if ((py_isinstance<pycs::cpp_module::ast::Name>(call->func) && (call->func->id == "sorted")))
        {
            return ("py_sorted(" + py_to_string(args) + ")");
        }
        if ((py_isinstance<pycs::cpp_module::ast::Name>(call->func) && (call->func->id == "zip")))
        {
            if ((py_len(args_list) == 2))
            {
                return ("py_zip(" + py_to_string(args_list[0]) + ", " + py_to_string(args_list[1]) + ")");
            }
            return "vector<tuple<int, int>>{}";
        }
        if ((py_isinstance<pycs::cpp_module::ast::Name>(call->func) && (call->func->id == "set")))
        {
            if ((py_len(args_list) == 0))
            {
                return "unordered_set<string>{}";
            }
            return ("unordered_set<std::remove_cvref_t<decltype(*" + (py_to_string(args_list[0]) + ".begin())>>(" + py_to_string(args_list[0]) + ".begin(), " + py_to_string(args_list[0]) + ".end())"));
        }
        if ((py_isinstance<pycs::cpp_module::ast::Name>(call->func) && (call->func->id == "str")))
        {
            if ((py_len(call->args) == 1))
            {
                return ("py_to_string(" + py_to_string(args_list[0]) + ")");
            }
            return "\"\"";
        }
        if ((py_isinstance<pycs::cpp_module::ast::Name>(call->func) && (call->func->id == "isinstance")))
        {
            if ((py_len(call->args) == 2))
            {
                auto obj = this->transpile_expr(call->args[0]);
                auto type_arg = call->args[1];
                if (auto __cast_type_arg = py_cast<pycs::cpp_module::ast::Tuple>(type_arg))
                {
                    auto type_arg = __cast_type_arg;
                    vector<string> types = {};
                    for (const auto& elt : type_arg->elts)
                    {
                        if ((py_isinstance<pycs::cpp_module::ast::Attribute>(elt) && py_isinstance<pycs::cpp_module::ast::Name>(elt->value) && (elt->value->id == "ast")))
                        {
                            types.push_back(("pycs::cpp_module::ast::" + py_to_string(elt->attr)));
                        }
                        else
                        {
                            if (auto __cast_elt = py_cast<pycs::cpp_module::ast::Name>(elt))
                            {
                                auto elt = __cast_elt;
                                types.push_back(elt->id);
                            }
                        }
                    }
                    if ((py_len(types) > 0))
                    {
                        return ("py_isinstance_any<decltype(" + py_to_string(obj) + "), " + py_to_string(py_join(", ", types)) + ">(" + py_to_string(obj) + ")");
                    }
                }
                if ((py_isinstance<pycs::cpp_module::ast::Attribute>(type_arg) && py_isinstance<pycs::cpp_module::ast::Name>(type_arg->value) && (type_arg->value->id == "ast")))
                {
                    return ("py_isinstance<pycs::cpp_module::ast::" + py_to_string(type_arg->attr) + ">(" + py_to_string(obj) + ")");
                }
                if (auto __cast_type_arg = py_cast<pycs::cpp_module::ast::Name>(type_arg))
                {
                    auto type_arg = __cast_type_arg;
                    if ((type_arg->id == "str"))
                    {
                        return ("py_isinstance<string>(" + py_to_string(obj) + ")");
                    }
                    return ("py_isinstance<" + py_to_string(type_arg->id) + ">(" + py_to_string(obj) + ")");
                }
            }
            return "false";
        }
        if (py_isinstance<pycs::cpp_module::ast::Name>(call->func))
        {
            if ((py_in(call->func->id, this->class_names) && (!py_in(call->func->id, this->exception_class_names))))
            {
                return ("pycs::gc::RcHandle<" + py_to_string(call->func->id) + ">::adopt(pycs::gc::rc_new<" + py_to_string(call->func->id) + ">(" + py_to_string(args) + "))");
            }
            return (py_to_string(call->func->id) + "(" + py_to_string(args) + ")");
        }
        if (py_isinstance<pycs::cpp_module::ast::Attribute>(call->func))
        {
            auto obj = this->transpile_expr(call->func->value);
            auto method = call->func->attr;
            if (((method == "append") && (py_len(args_list) == 1)))
            {
                return (py_to_string(obj) + ".push_back(" + py_to_string(args_list[0]) + ")");
            }
            if (((method == "extend") && (py_len(args_list) == 1)))
            {
                return ("py_extend(" + py_to_string(obj) + ", " + py_to_string(args_list[0]) + ")");
            }
            if (((method == "add") && (py_len(args_list) == 1)))
            {
                return (py_to_string(obj) + ".insert(" + py_to_string(args_list[0]) + ")");
            }
            if (((method == "union") && (py_len(args_list) == 1)))
            {
                return ("py_set_union(" + py_to_string(obj) + ", " + py_to_string(args_list[0]) + ")");
            }
            if ((method == "splitlines"))
            {
                return ("py_splitlines(" + py_to_string(obj) + ")");
            }
            if (((method == "join") && (py_len(args_list) == 1)))
            {
                return ("py_join(" + py_to_string(obj) + ", " + py_to_string(args_list[0]) + ")");
            }
            if (((method == "replace") && (py_len(args_list) == 2)))
            {
                return ("py_replace(" + py_to_string(obj) + ", " + py_to_string(args_list[0]) + ", " + py_to_string(args_list[1]) + ")");
            }
            return (py_to_string(this->transpile_expr(call->func)) + "(" + py_to_string(args) + ")");
        }
        throw std::runtime_error(py_to_string("Only direct function calls are supported"));
    }
    string _map_annotation(pycs::cpp_module::ast::ExprPtr annotation)
    {
        if ((py_isinstance<pycs::cpp_module::ast::Constant>(annotation) && (annotation->value == nullptr)))
        {
            return "void";
        }
        if ((py_isinstance<pycs::cpp_module::ast::BinOp>(annotation) && py_isinstance<pycs::cpp_module::ast::BitOr>(annotation->op)))
        {
            auto left = this->_map_annotation(annotation->left);
            auto right = this->_map_annotation(annotation->right);
            if ((left == "void"))
            {
                return right;
            }
            if ((right == "void"))
            {
                return left;
            }
            return "auto";
        }
        if (auto __cast_annotation = py_cast<pycs::cpp_module::ast::Name>(annotation))
        {
            auto annotation = __cast_annotation;
            if ((annotation->id == "int"))
            {
                return "int";
            }
            if ((annotation->id == "float"))
            {
                return "double";
            }
            if ((annotation->id == "str"))
            {
                return "string";
            }
            if ((annotation->id == "bool"))
            {
                return "bool";
            }
            if ((annotation->id == "None"))
            {
                return "void";
            }
            if (py_in(annotation->id, this->class_names))
            {
                return ("pycs::gc::RcHandle<" + py_to_string(annotation->id) + ">");
            }
            return "auto";
        }
        if (auto __cast_annotation = py_cast<pycs::cpp_module::ast::Attribute>(annotation))
        {
            auto annotation = __cast_annotation;
            if ((py_isinstance<pycs::cpp_module::ast::Name>(annotation->value) && (annotation->value->id == "ast")))
            {
                if ((annotation->attr == "Module"))
                {
                    return "pycs::cpp_module::ast::ModulePtr";
                }
                if ((annotation->attr == "stmt"))
                {
                    return "pycs::cpp_module::ast::StmtPtr";
                }
                if ((annotation->attr == "expr"))
                {
                    return "pycs::cpp_module::ast::ExprPtr";
                }
                if ((annotation->attr == "FunctionDef"))
                {
                    return "std::shared_ptr<pycs::cpp_module::ast::FunctionDef>";
                }
                if ((annotation->attr == "ClassDef"))
                {
                    return "std::shared_ptr<pycs::cpp_module::ast::ClassDef>";
                }
                if ((annotation->attr == "Assign"))
                {
                    return "std::shared_ptr<pycs::cpp_module::ast::Assign>";
                }
                if ((annotation->attr == "AnnAssign"))
                {
                    return "std::shared_ptr<pycs::cpp_module::ast::AnnAssign>";
                }
                if ((annotation->attr == "For"))
                {
                    return "std::shared_ptr<pycs::cpp_module::ast::For>";
                }
                if ((annotation->attr == "If"))
                {
                    return "std::shared_ptr<pycs::cpp_module::ast::If>";
                }
                if ((annotation->attr == "Try"))
                {
                    return "std::shared_ptr<pycs::cpp_module::ast::Try>";
                }
                if ((annotation->attr == "Raise"))
                {
                    return "std::shared_ptr<pycs::cpp_module::ast::Raise>";
                }
                if ((annotation->attr == "Call"))
                {
                    return "std::shared_ptr<pycs::cpp_module::ast::Call>";
                }
                if ((annotation->attr == "JoinedStr"))
                {
                    return "std::shared_ptr<pycs::cpp_module::ast::JoinedStr>";
                }
                if ((annotation->attr == "boolop"))
                {
                    return "std::shared_ptr<pycs::cpp_module::ast::boolop>";
                }
                if ((annotation->attr == "cmpop"))
                {
                    return "std::shared_ptr<pycs::cpp_module::ast::cmpop>";
                }
                if ((annotation->attr == "unaryop"))
                {
                    return "std::shared_ptr<pycs::cpp_module::ast::unaryop>";
                }
                if ((annotation->attr == "operator"))
                {
                    return "std::shared_ptr<pycs::cpp_module::ast::operator_>";
                }
                return "auto";
            }
            return "auto";
        }
        if (auto __cast_annotation = py_cast<pycs::cpp_module::ast::Subscript>(annotation))
        {
            auto annotation = __cast_annotation;
            string raw_base = "";
            if (py_isinstance<pycs::cpp_module::ast::Name>(annotation->value))
            {
                raw_base = annotation->value->id;
            }
            else
            {
                if (py_isinstance<pycs::cpp_module::ast::Attribute>(annotation->value))
                {
                    raw_base = this->transpile_expr(annotation->value);
                }
                else
                {
                    return "auto";
                }
            }
            string base = "";
            if (((raw_base == "list") || (raw_base == "List")))
            {
                base = "vector";
            }
            else
            {
                if (((raw_base == "set") || (raw_base == "Set")))
                {
                    base = "unordered_set";
                }
                else
                {
                    if (((raw_base == "dict") || (raw_base == "Dict")))
                    {
                        base = "unordered_map";
                    }
                    else
                    {
                        if (((raw_base == "tuple") || (raw_base == "Tuple")))
                        {
                            base = "tuple";
                        }
                        else
                        {
                            base = raw_base;
                        }
                    }
                }
            }
            vector<string> args;
            if (py_isinstance<pycs::cpp_module::ast::Tuple>(annotation->slice))
            {
                args = {};
                for (const auto& e : annotation->slice->elts)
                {
                    args.push_back(this->_map_annotation(e));
                }
            }
            else
            {
                args = {this->_map_annotation(annotation->slice)};
            }
            return (py_to_string(base) + "<" + py_to_string(py_join(", ", args)) + ">");
        }
        return "auto";
    }
    bool _is_main_guard(pycs::cpp_module::ast::StmtPtr stmt)
    {
        if ((!py_isinstance<pycs::cpp_module::ast::If>(stmt)))
        {
            return false;
        }
        auto test = stmt->test;
        if ((!py_isinstance<pycs::cpp_module::ast::Compare>(test)))
        {
            try
            {
                return (test->as_text() == "__name__ == \"__main__\"");
            }
            catch (const std::exception& None)
            {
                return false;
            }
        }
        if (((py_len(test->ops) != 1) || (py_len(test->comparators) != 1)))
        {
            return false;
        }
        if ((!py_isinstance<pycs::cpp_module::ast::Eq>(test->ops[0])))
        {
            return false;
        }
        if ((!py_isinstance<pycs::cpp_module::ast::Name>(test->left)))
        {
            return false;
        }
        if ((test->left->id != "__name__"))
        {
            return false;
        }
        if ((!py_isinstance<pycs::cpp_module::ast::Constant>(test->comparators[0])))
        {
            return false;
        }
        return (this->transpile_expr(test->comparators[0]) == "\"__main__\"");
    }
    string _raw_expr_to_cpp(string text)
    {
        if ((text == "True"))
        {
            return "true";
        }
        if ((text == "False"))
        {
            return "false";
        }
        if ((text == "None"))
        {
            return "nullptr";
        }
        return py_replace(py_replace(py_replace(py_replace(py_replace(py_replace(text, "(True)", "(true)"), "(False)", "(false)"), "(None)", "(nullptr)"), " True", " true"), " False", " false"), " None", " nullptr");
    }
    string _constant(auto value)
    {
        if (py_isinstance<string>(value))
        {
            auto text = py_to_string(value);
            auto escaped = py_replace(py_replace(py_replace(py_replace(py_replace(text, "\\", "\\\\"), "\"", "\\\""), "\n", "\\n"), "\t", "\\t"), "\r", "\\r");
            return ("\"" + py_to_string(escaped) + "\"");
        }
        auto text = py_to_string(value);
        if ((text == "True"))
        {
            return "true";
        }
        if ((text == "False"))
        {
            return "false";
        }
        if ((text == "None"))
        {
            return "nullptr";
        }
        return text;
    }
    string _binop(std::shared_ptr<pycs::cpp_module::ast::operator_> op)
    {
        if (auto __cast_op = py_cast<pycs::cpp_module::ast::Add>(op))
        {
            auto op = __cast_op;
            return "+";
        }
        if (auto __cast_op = py_cast<pycs::cpp_module::ast::Sub>(op))
        {
            auto op = __cast_op;
            return "-";
        }
        if (auto __cast_op = py_cast<pycs::cpp_module::ast::Mult>(op))
        {
            auto op = __cast_op;
            return "*";
        }
        if (auto __cast_op = py_cast<pycs::cpp_module::ast::Div>(op))
        {
            auto op = __cast_op;
            return "/";
        }
        if (auto __cast_op = py_cast<pycs::cpp_module::ast::Mod>(op))
        {
            auto op = __cast_op;
            return "%";
        }
        if (auto __cast_op = py_cast<pycs::cpp_module::ast::BitOr>(op))
        {
            auto op = __cast_op;
            return "|";
        }
        throw std::runtime_error(py_to_string("Unsupported binary operator"));
    }
    string _unaryop(std::shared_ptr<pycs::cpp_module::ast::unaryop> op)
    {
        if (auto __cast_op = py_cast<pycs::cpp_module::ast::UAdd>(op))
        {
            auto op = __cast_op;
            return "+";
        }
        if (auto __cast_op = py_cast<pycs::cpp_module::ast::USub>(op))
        {
            auto op = __cast_op;
            return "-";
        }
        if (auto __cast_op = py_cast<pycs::cpp_module::ast::Not>(op))
        {
            auto op = __cast_op;
            return "!";
        }
        throw std::runtime_error(py_to_string("Unsupported unary operator"));
    }
    string _cmpop(std::shared_ptr<pycs::cpp_module::ast::cmpop> op)
    {
        if (auto __cast_op = py_cast<pycs::cpp_module::ast::Eq>(op))
        {
            auto op = __cast_op;
            return "==";
        }
        if (auto __cast_op = py_cast<pycs::cpp_module::ast::NotEq>(op))
        {
            auto op = __cast_op;
            return "!=";
        }
        if (auto __cast_op = py_cast<pycs::cpp_module::ast::Lt>(op))
        {
            auto op = __cast_op;
            return "<";
        }
        if (auto __cast_op = py_cast<pycs::cpp_module::ast::LtE>(op))
        {
            auto op = __cast_op;
            return "<=";
        }
        if (auto __cast_op = py_cast<pycs::cpp_module::ast::Gt>(op))
        {
            auto op = __cast_op;
            return ">";
        }
        if (auto __cast_op = py_cast<pycs::cpp_module::ast::GtE>(op))
        {
            auto op = __cast_op;
            return ">=";
        }
        throw std::runtime_error(py_to_string("Unsupported comparison operator"));
    }
    string _transpile_compare(pycs::cpp_module::ast::ExprPtr left_expr, std::shared_ptr<pycs::cpp_module::ast::cmpop> op, pycs::cpp_module::ast::ExprPtr right_expr)
    {
        auto left = this->transpile_expr(left_expr);
        auto right = this->transpile_expr(right_expr);
        if (auto __cast_op = py_cast<pycs::cpp_module::ast::In>(op))
        {
            auto op = __cast_op;
            return ("py_in(" + py_to_string(left) + ", " + py_to_string(right) + ")");
        }
        if (auto __cast_op = py_cast<pycs::cpp_module::ast::NotIn>(op))
        {
            auto op = __cast_op;
            return ("(!py_in(" + py_to_string(left) + ", " + py_to_string(right) + "))");
        }
        if (auto __cast_op = py_cast<pycs::cpp_module::ast::Is>(op))
        {
            auto op = __cast_op;
            return ("(" + py_to_string(left) + " == " + py_to_string(right) + ")");
        }
        if (auto __cast_op = py_cast<pycs::cpp_module::ast::IsNot>(op))
        {
            auto op = __cast_op;
            return ("(" + py_to_string(left) + " != " + py_to_string(right) + ")");
        }
        return ("(" + py_to_string(left) + " " + py_to_string(this->_cmpop(op)) + " " + py_to_string(right) + ")");
    }
    string _boolop(std::shared_ptr<pycs::cpp_module::ast::boolop> op)
    {
        if (auto __cast_op = py_cast<pycs::cpp_module::ast::And>(op))
        {
            auto op = __cast_op;
            return "&&";
        }
        if (auto __cast_op = py_cast<pycs::cpp_module::ast::Or>(op))
        {
            auto op = __cast_op;
            return "||";
        }
        throw std::runtime_error(py_to_string("Unsupported boolean operator"));
    }
    string _transpile_joined_str(std::shared_ptr<pycs::cpp_module::ast::JoinedStr> expr)
    {
        vector<string> parts = {};
        for (const auto& value : expr->values)
        {
            if ((py_isinstance<pycs::cpp_module::ast::Constant>(value) && py_isinstance<string>(value->value)))
            {
                parts.push_back(this->_constant(value->value));
            }
            else
            {
                if (auto __cast_value = py_cast<pycs::cpp_module::ast::FormattedValue>(value))
                {
                    auto value = __cast_value;
                    parts.push_back(("py_to_string(" + py_to_string(this->transpile_expr(value->value)) + ")"));
                }
                else
                {
                    parts.push_back("\"\"");
                }
            }
        }
        if ((py_len(parts) == 0))
        {
            return "\"\"";
        }
        return (("(" + py_join(" + ", parts)) + ")");
    }
    bool _is_dataclass_class(pycs::cpp_module::ast::StmtPtr cls)
    {
        for (const auto& decorator : cls->decorator_list)
        {
            if ((py_isinstance<pycs::cpp_module::ast::Name>(decorator) && (decorator->id == "dataclass")))
            {
                return true;
            }
            if ((py_isinstance<pycs::cpp_module::ast::Attribute>(decorator) && (decorator->attr == "dataclass")))
            {
                return true;
            }
        }
        return false;
    }
    vector<string> _indent_block(vector<string> lines)
    {
        vector<string> out = {};
        for (const auto& line : lines)
        {
            if ((line != ""))
            {
                out.push_back((py_to_string(CppTranspiler::INDENT) + py_to_string(line)));
            }
            else
            {
                out.push_back("");
            }
        }
        return out;
    }
};

void transpile(string input_file, string output_file)
{
    auto transpiler = pycs::gc::RcHandle<CppTranspiler>::adopt(pycs::gc::rc_new<CppTranspiler>());
    transpiler->transpile_file(Path(input_file), Path(output_file));
}

int main()
{
    auto __all__ = {"TranspileError", "CppTranspiler", "transpile"};
    return 0;
}
