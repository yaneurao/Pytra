#include "gc.h"
#include <any>
#include <filesystem>
#include <iostream>
#include <sstream>
#include <stdexcept>
#include <string>
#include <tuple>
#include <unordered_map>
#include <unordered_set>
#include <utility>
#include <vector>

using namespace std;
using namespace pycs::gc;

template <typename T>
string py_to_string(const T& value)
{
    std::ostringstream oss;
    oss << value;
    return oss.str();
}

template <typename T>
bool py_in(const T& key, const unordered_set<T>& s)
{
    return s.find(key) != s.end();
}

template <typename K, typename V>
bool py_in(const K& key, const unordered_map<K, V>& m)
{
    return m.find(key) != m.end();
}

template <typename T>
bool py_in(const T& key, const vector<T>& v)
{
    for (const auto& item : v) {
        if (item == key) {
            return true;
        }
    }
    return false;
}

inline void py_print()
{
    std::cout << std::endl;
}

template <typename T>
void py_print_one(const T& value)
{
    std::cout << value;
}

inline void py_print_one(bool value)
{
    std::cout << (value ? "True" : "False");
}

template <typename T, typename... Rest>
void py_print(const T& first, const Rest&... rest)
{
    py_print_one(first);
    ((std::cout << " ", py_print_one(rest)), ...);
    std::cout << std::endl;
}

class TranspileError : public Exception
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

class CSharpTranspiler : public pycs::gc::PyObj
{
public:
    inline static string INDENT = "    ";
    unordered_set<string> class_names;
    string current_class_name;
    unordered_set<string> current_static_fields;
    CSharpTranspiler()
    {
        this->class_names = set();
        this->current_class_name = nullptr;
        this->current_static_fields = set();
    }
    void transpile_file(Path input_path, Path output_path)
    {
        auto source = input_path->read_text("utf-8");
        auto tree = ast->parse(source, str(input_path));
        auto csharp = this->transpile_module(tree);
        output_path->write_text(csharp, "utf-8");
    }
    string transpile_module(ast->Module module)
    {
        vector<string> function_defs = {};
        vector<string> class_defs = {};
        vector<ast->stmt> top_level_body = {};
        unordered_set<string> using_lines = {"using System;"};
        this->class_names = /* comprehension */ {};
        for (const auto& stmt : module->body)
        {
            if (isinstance(stmt, std::make_tuple(ast->Import, ast->ImportFrom)))
            {
                using_lines = using_lines->union(this->_using_lines_from_import(stmt));
            }
            else
            {
                if (isinstance(stmt, ast->FunctionDef))
                {
                    function_defs->append(this->transpile_function(stmt));
                }
                else
                {
                    if (isinstance(stmt, ast->ClassDef))
                    {
                        class_defs->append(this->transpile_class(stmt));
                    }
                    else
                    {
                        top_level_body->append(stmt);
                    }
                }
            }
        }
        vector<ast->stmt> main_stmts = {};
        for (const auto& stmt : top_level_body)
        {
            if (this->_is_main_guard(stmt))
            {
                main_stmts->extend(stmt->body);
            }
            else
            {
                main_stmts->append(stmt);
            }
        }
        auto main_method = this->transpile_main(main_stmts);
        auto parts = sorted(using_lines);
        parts->extend({"", "public static class Program", "{"});
        for (const auto& fn : function_defs)
        {
            parts->extend(this->_indent_block(fn->splitlines()));
            parts->append("");
        }
        for (const auto& cls : class_defs)
        {
            parts->extend(this->_indent_block(cls->splitlines()));
            parts->append("");
        }
        parts->extend(this->_indent_block(main_method->splitlines()));
        parts->append("}");
        parts->append("");
        return "
    "->join(parts);
    }
    unordered_set<string> _using_lines_from_import(ast->stmt stmt)
    {
        unordered_set<string> lines = set();
        if (isinstance(stmt, ast->Import))
        {
            for (const auto& alias : stmt->names)
            {
                auto module_name = this->_map_python_module(alias->name);
                if (alias->asname)
                {
                    lines->add(("using " + py_to_string(alias->asname) + " = " + py_to_string(module_name) + ";"));
                }
                else
                {
                    lines->add(("using " + py_to_string(module_name) + ";"));
                }
            }
            return lines;
        }
        if (isinstance(stmt, ast->ImportFrom))
        {
            if ((stmt->level != 0))
            {
                return lines;
            }
            if (stmt->module)
            {
                auto module_name = this->_map_python_module(stmt->module);
                lines->add(("using " + py_to_string(module_name) + ";"));
                for (const auto& alias : stmt->names)
                {
                    if ((alias->name == "*"))
                    {
                        continue;
                    }
                    auto full_name = (py_to_string(module_name) + "." + py_to_string(alias->name));
                    if (alias->asname)
                    {
                        lines->add(("using " + py_to_string(alias->asname) + " = " + py_to_string(full_name) + ";"));
                    }
                }
            }
            return lines;
        }
        return lines;
    }
    string _map_python_module(string module_name)
    {
        auto mapping = {{ "math", "System" }, { "pathlib", "System.IO" }, { "typing", "System.Collections.Generic" }, { "collections", "System.Collections.Generic" }, { "itertools", "System.Linq" }};
        return mapping->get(module_name, module_name);
    }
    string transpile_class(ast->ClassDef cls)
    {
        if ((len(cls->bases) > 1))
        {
            throw std::runtime_error(py_to_string(pycs::gc::RcHandle<TranspileError>::adopt(pycs::gc::rc_new<TranspileError>(("Class '" + py_to_string(cls->name) + "' multiple inheritance is not supported")))));
        }
        auto base = "";
        if (cls->bases)
        {
            if ((!isinstance(cls->bases[0], ast->Name)))
            {
                throw std::runtime_error(py_to_string(pycs::gc::RcHandle<TranspileError>::adopt(pycs::gc::rc_new<TranspileError>(("Class '" + py_to_string(cls->name) + "' base class must be a simple name")))));
            }
            base = (" : " + py_to_string(cls->bases[0]->id));
        }
        auto is_dataclass = this->_is_dataclass_class(cls);
        vector<string> static_fields = {};
        vector<tuple<string, string, string>> dataclass_fields = {};
        unordered_set<string> static_field_names = set();
        vector<ast->FunctionDef> methods = {};
        for (const auto& stmt : cls->body)
        {
            if (isinstance(stmt, ast->FunctionDef))
            {
                methods->append(stmt);
            }
            else
            {
                if (isinstance(stmt, ast->AnnAssign))
                {
                    if (is_dataclass)
                    {
                        dataclass_fields->append(this->_transpile_dataclass_field(stmt));
                    }
                    else
                    {
                        auto _tmp_tuple = this->_transpile_class_static_field(stmt);
                        auto field_line = std::get<0>(_tmp_tuple);
                        auto field_name = std::get<1>(_tmp_tuple);
                        static_fields->append(field_line);
                        static_field_names->add(field_name);
                    }
                }
                else
                {
                    if (isinstance(stmt, ast->Assign))
                    {
                        auto _tmp_tuple = this->_transpile_class_static_assign(stmt);
                        auto field_line = std::get<0>(_tmp_tuple);
                        auto field_name = std::get<1>(_tmp_tuple);
                        static_fields->append(field_line);
                        static_field_names->add(field_name);
                    }
                    else
                    {
                        if (isinstance(stmt, ast->Pass))
                        {
                            continue;
                        }
                        else
                        {
                            throw std::runtime_error(py_to_string(pycs::gc::RcHandle<TranspileError>::adopt(pycs::gc::rc_new<TranspileError>(("Unsupported class member in '" + py_to_string(cls->name) + "': " + py_to_string(type(stmt)->__name__))))));
                        }
                    }
                }
            }
        }
        auto instance_fields = this->_collect_instance_fields(cls, static_field_names);
        auto has_init = any(/* comprehension */ {});
        auto lines = {("public class " + py_to_string(cls->name) + py_to_string(base)), "{"};
        for (const auto& static_field : static_fields)
        {
            lines->extend(this->_indent_block({static_field}));
        }
        for (const auto& _for_item : dataclass_fields)
        {
            auto field_type = std::get<0>(_for_item);
            auto field_name = std::get<1>(_for_item);
            auto default_value = std::get<2>(_for_item);
            if ((default_value == nullptr))
            {
                lines->extend(this->_indent_block({("public " + py_to_string(field_type) + " " + py_to_string(field_name) + ";")}));
            }
            else
            {
                lines->extend(this->_indent_block({("public " + py_to_string(field_type) + " " + py_to_string(field_name) + " = " + py_to_string(default_value) + ";")}));
            }
        }
        for (const auto& _for_item : instance_fields)
        {
            auto _ = std::get<0>(_for_item);
            auto field_type = std::get<1>(_for_item);
            auto field_name = std::get<2>(_for_item);
            lines->extend(this->_indent_block({("public " + py_to_string(field_type) + " " + py_to_string(field_name) + ";")}));
        }
        if ((is_dataclass && dataclass_fields && (!has_init)))
        {
            vector<string> ctor_params = {};
            vector<string> ctor_body = {};
            for (const auto& _for_item : dataclass_fields)
            {
                auto field_type = std::get<0>(_for_item);
                auto field_name = std::get<1>(_for_item);
                auto default_value = std::get<2>(_for_item);
                if ((default_value == nullptr))
                {
                    ctor_params->append((py_to_string(field_type) + " " + py_to_string(field_name)));
                }
                else
                {
                    ctor_params->append((py_to_string(field_type) + " " + py_to_string(field_name) + " = " + py_to_string(default_value)));
                }
                ctor_body->append(("this." + py_to_string(field_name) + " = " + py_to_string(field_name) + ";"));
            }
            lines->extend(this->_indent_block({("public " + py_to_string(cls->name) + "(" + py_to_string(", "->join(ctor_params)) + ")")}));
            lines->extend(this->_indent_block({"{"}));
            lines->extend(this->_indent_block(this->_indent_block(ctor_body)));
            lines->extend(this->_indent_block({"}"}));
        }
        if ((static_fields || dataclass_fields || instance_fields))
        {
            lines->extend(this->_indent_block({""}));
        }
        auto prev_class_name = this->current_class_name;
        auto prev_static_fields = this->current_static_fields;
        this->current_class_name = cls->name;
        this->current_static_fields = static_field_names;
        try
        {
            for (const auto& method : methods)
            {
                lines->extend(this->_indent_block(this->transpile_function(method, true)->splitlines()));
            }
        }
        // finally is not directly supported in C++; emitted as plain block
        {
            this->current_class_name = prev_class_name;
            this->current_static_fields = prev_static_fields;
        }
        lines->append("}");
        return "
    "->join(lines);
    }
    tuple<string, string> _transpile_class_static_field(ast->AnnAssign stmt)
    {
        if ((!isinstance(stmt->target, ast->Name)))
        {
            throw std::runtime_error(py_to_string(pycs::gc::RcHandle<TranspileError>::adopt(pycs::gc::rc_new<TranspileError>("Class field declaration must be a simple name"))));
        }
        auto field_type = this->_map_annotation(stmt->annotation);
        auto field_name = stmt->target->id;
        if ((stmt->value == nullptr))
        {
            return std::make_tuple(("public static " + py_to_string(field_type) + " " + py_to_string(field_name) + ";"), field_name);
        }
        return std::make_tuple(("public static " + py_to_string(field_type) + " " + py_to_string(field_name) + " = " + py_to_string(this->transpile_expr(stmt->value)) + ";"), field_name);
    }
    tuple<string, string, string> _transpile_dataclass_field(ast->AnnAssign stmt)
    {
        if ((!isinstance(stmt->target, ast->Name)))
        {
            throw std::runtime_error(py_to_string(pycs::gc::RcHandle<TranspileError>::adopt(pycs::gc::rc_new<TranspileError>("Dataclass field declaration must be a simple name"))));
        }
        auto field_type = this->_map_annotation(stmt->annotation);
        auto field_name = stmt->target->id;
        if ((stmt->value == nullptr))
        {
            return std::make_tuple(field_type, field_name, nullptr);
        }
        return std::make_tuple(field_type, field_name, this->transpile_expr(stmt->value));
    }
    tuple<string, string> _transpile_class_static_assign(ast->Assign stmt)
    {
        if (((len(stmt->targets) != 1) || (!isinstance(stmt->targets[0], ast->Name))))
        {
            throw std::runtime_error(py_to_string(pycs::gc::RcHandle<TranspileError>::adopt(pycs::gc::rc_new<TranspileError>("Class static assignment must be a simple name assignment"))));
        }
        auto field_name = stmt->targets[0]->id;
        auto field_type = (this->_infer_expr_csharp_type(stmt->value) || "object");
        return std::make_tuple(("public static " + py_to_string(field_type) + " " + py_to_string(field_name) + " = " + py_to_string(this->transpile_expr(stmt->value)) + ";"), field_name);
    }
    vector<tuple<string, string, string>> _collect_instance_fields(ast->ClassDef cls, unordered_set<string> static_field_names)
    {
        vector<tuple<string, string, string>> fields = {};
        unordered_set<string> seen = set();
        auto init_fn = nullptr;
        for (const auto& stmt : cls->body)
        {
            if ((isinstance(stmt, ast->FunctionDef) && (stmt->name == "__init__")))
            {
                init_fn = stmt;
                break;
            }
        }
        if ((init_fn == nullptr))
        {
            return fields;
        }
        unordered_map<string, string> arg_types = {};
        for (const auto& _for_item : enumerate(init_fn->args->args))
        {
            auto idx = std::get<0>(_for_item);
            auto arg = std::get<1>(_for_item);
            if (((idx == 0) && (arg->arg == "self")))
            {
                continue;
            }
            if ((arg->annotation != nullptr))
            {
                // unsupported assignment: arg_types[arg.arg] = self._map_annotation(arg.annotation)
            }
        }
        for (const auto& stmt : init_fn->body)
        {
            string field_name = nullptr;
            string field_type = nullptr;
            if (isinstance(stmt, ast->AnnAssign))
            {
                if ((isinstance(stmt->target, ast->Attribute) && isinstance(stmt->target->value, ast->Name) && (stmt->target->value->id == "self")))
                {
                    field_name = stmt->target->attr;
                    field_type = this->_map_annotation(stmt->annotation);
                }
            }
            else
            {
                if (isinstance(stmt, ast->Assign))
                {
                    if (((len(stmt->targets) == 1) && isinstance(stmt->targets[0], ast->Attribute) && isinstance(stmt->targets[0]->value, ast->Name) && (stmt->targets[0]->value->id == "self")))
                    {
                        field_name = stmt->targets[0]->attr;
                        field_type = this->_infer_type(stmt->value, arg_types);
                    }
                }
            }
            if (((field_name == nullptr) || (field_type == nullptr)))
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
            seen->add(field_name);
            fields->append(std::make_tuple(cls->name, field_type, field_name));
        }
        return fields;
    }
    string _infer_type(ast->expr expr, unordered_map<string, string> arg_types)
    {
        if (isinstance(expr, ast->Name))
        {
            return arg_types->get(expr->id);
        }
        if (isinstance(expr, ast->Constant))
        {
            return this->_infer_expr_csharp_type(expr);
        }
        if ((isinstance(expr, ast->Call) && isinstance(expr->func, ast->Name)))
        {
            if (py_in(expr->func->id, this->class_names))
            {
                return expr->func->id;
            }
        }
        return nullptr;
    }
    string _infer_expr_csharp_type(ast->expr expr)
    {
        if (isinstance(expr, ast->Constant))
        {
            if (isinstance(expr->value, bool))
            {
                return "bool";
            }
            if (isinstance(expr->value, int))
            {
                return "int";
            }
            if (isinstance(expr->value, float))
            {
                return "double";
            }
            if (isinstance(expr->value, str))
            {
                return "string";
            }
            return nullptr;
        }
        return nullptr;
    }
    string transpile_function(ast->FunctionDef fn, bool in_class)
    {
        auto is_constructor = (in_class && (fn->name == "__init__"));
        if ((fn->returns == nullptr))
        {
            throw std::runtime_error(py_to_string(pycs::gc::RcHandle<TranspileError>::adopt(pycs::gc::rc_new<TranspileError>(("Function '" + py_to_string(fn->name) + "' requires return type annotation")))));
        }
        auto return_type = this->_map_annotation(fn->returns);
        vector<string> params = {};
        auto declared = set();
        for (const auto& _for_item : enumerate(fn->args->args))
        {
            auto idx = std::get<0>(_for_item);
            auto arg = std::get<1>(_for_item);
            if ((in_class && (idx == 0) && (arg->arg == "self")))
            {
                declared->add("self");
                continue;
            }
            if ((arg->annotation == nullptr))
            {
                throw std::runtime_error(py_to_string(pycs::gc::RcHandle<TranspileError>::adopt(pycs::gc::rc_new<TranspileError>(("Function '" + py_to_string(fn->name) + "' argument '" + py_to_string(arg->arg) + "' requires type annotation")))));
            }
            params->append((py_to_string(this->_map_annotation(arg->annotation)) + " " + py_to_string(arg->arg)));
            declared->add(arg->arg);
        }
        auto body_lines = this->transpile_statements(fn->body, pycs::gc::RcHandle<Scope>::adopt(pycs::gc::rc_new<Scope>(declared)));
        if (is_constructor)
        {
            if ((this->current_class_name == nullptr))
            {
                throw std::runtime_error(py_to_string(pycs::gc::RcHandle<TranspileError>::adopt(pycs::gc::rc_new<TranspileError>("Constructor conversion requires class context"))));
            }
            if ((return_type != "void"))
            {
                throw std::runtime_error(py_to_string(pycs::gc::RcHandle<TranspileError>::adopt(pycs::gc::rc_new<TranspileError>("__init__ return type must be None"))));
            }
            auto signature = ("public " + py_to_string(this->current_class_name) + "(" + py_to_string(", "->join(params)) + ")");
        }
        else
        {
            auto modifier = (in_class ? "public" : "public static");
            auto signature = (py_to_string(modifier) + " " + py_to_string(return_type) + " " + py_to_string(fn->name) + "(" + py_to_string(", "->join(params)) + ")");
        }
        auto lines = {signature, "{"};
        lines->extend(this->_indent_block(body_lines));
        lines->append("}");
        return "
    "->join(lines);
    }
    string transpile_main(vector<ast->stmt> body)
    {
        auto lines = {"public static void Main(string[] args)", "{"};
        auto body_lines = this->transpile_statements(body, pycs::gc::RcHandle<Scope>::adopt(pycs::gc::rc_new<Scope>({"args"})));
        lines->extend(this->_indent_block(body_lines));
        lines->append("}");
        return "
    "->join(lines);
    }
    vector<string> transpile_statements(vector<ast->stmt> stmts, pycs::gc::RcHandle<Scope> scope)
    {
        vector<string> lines = {};
        for (const auto& stmt : stmts)
        {
            if (isinstance(stmt, std::make_tuple(ast->Import, ast->ImportFrom)))
            {
                lines->append(("// " + py_to_string(ast->unparse(stmt))));
                continue;
            }
            if (isinstance(stmt, ast->Return))
            {
                if ((stmt->value == nullptr))
                {
                    lines->append("return;");
                }
                else
                {
                    lines->append(("return " + py_to_string(this->transpile_expr(stmt->value)) + ";"));
                }
            }
            else
            {
                if (isinstance(stmt, ast->Expr))
                {
                    lines->append((py_to_string(this->transpile_expr(stmt->value)) + ";"));
                }
                else
                {
                    if (isinstance(stmt, ast->AnnAssign))
                    {
                        lines->extend(this->_transpile_ann_assign(stmt, scope));
                    }
                    else
                    {
                        if (isinstance(stmt, ast->Assign))
                        {
                            lines->extend(this->_transpile_assign(stmt, scope));
                        }
                        else
                        {
                            if (isinstance(stmt, ast->If))
                            {
                                lines->extend(this->_transpile_if(stmt, scope));
                            }
                            else
                            {
                                if (isinstance(stmt, ast->For))
                                {
                                    lines->extend(this->_transpile_for(stmt, scope));
                                }
                                else
                                {
                                    if (isinstance(stmt, ast->Try))
                                    {
                                        lines->extend(this->_transpile_try(stmt, scope));
                                    }
                                    else
                                    {
                                        if (isinstance(stmt, ast->Raise))
                                        {
                                            lines->extend(this->_transpile_raise(stmt));
                                        }
                                        else
                                        {
                                            if (isinstance(stmt, ast->Break))
                                            {
                                                lines->append("break;");
                                            }
                                            else
                                            {
                                                if (isinstance(stmt, ast->Continue))
                                                {
                                                    lines->append("continue;");
                                                }
                                                else
                                                {
                                                    if (isinstance(stmt, ast->Pass))
                                                    {
                                                        continue;
                                                    }
                                                    else
                                                    {
                                                        throw std::runtime_error(py_to_string(pycs::gc::RcHandle<TranspileError>::adopt(pycs::gc::rc_new<TranspileError>(("Unsupported statement: " + py_to_string(type(stmt)->__name__))))));
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
    vector<string> _transpile_ann_assign(ast->AnnAssign stmt, pycs::gc::RcHandle<Scope> scope)
    {
        if (isinstance(stmt->target, ast->Attribute))
        {
            if ((isinstance(stmt->target->value, ast->Name) && (stmt->target->value->id == "self")))
            {
                if ((stmt->value == nullptr))
                {
                    throw std::runtime_error(py_to_string(pycs::gc::RcHandle<TranspileError>::adopt(pycs::gc::rc_new<TranspileError>("Annotated assignment to self attributes requires an initializer"))));
                }
                return {(py_to_string(this->transpile_expr(stmt->target)) + " = " + py_to_string(this->transpile_expr(stmt->value)) + ";")};
            }
            throw std::runtime_error(py_to_string(pycs::gc::RcHandle<TranspileError>::adopt(pycs::gc::rc_new<TranspileError>("Annotated assignment to attributes is not supported"))));
        }
        if ((!isinstance(stmt->target, ast->Name)))
        {
            throw std::runtime_error(py_to_string(pycs::gc::RcHandle<TranspileError>::adopt(pycs::gc::rc_new<TranspileError>("Only simple annotated assignments are supported"))));
        }
        auto name = stmt->target->id;
        auto csharp_type = this->_map_annotation(stmt->annotation);
        if ((stmt->value == nullptr))
        {
            auto line = (py_to_string(csharp_type) + " " + py_to_string(name) + ";");
        }
        else
        {
            auto line = (py_to_string(csharp_type) + " " + py_to_string(name) + " = " + py_to_string(this->transpile_expr(stmt->value)) + ";");
        }
        scope->declared->add(name);
        return {line};
    }
    vector<string> _transpile_assign(ast->Assign stmt, pycs::gc::RcHandle<Scope> scope)
    {
        if ((len(stmt->targets) != 1))
        {
            return {("// unsupported assignment: " + py_to_string(ast->unparse(stmt)))};
        }
        if (isinstance(stmt->targets[0], ast->Tuple))
        {
            auto tuple_target = stmt->targets[0];
            if ((!all(/* comprehension */ {})))
            {
                return {("// unsupported tuple assignment: " + py_to_string(ast->unparse(stmt)))};
            }
            auto tmp_name = "_tmp_tuple";
            auto lines = {("var " + py_to_string(tmp_name) + " = " + py_to_string(this->transpile_expr(stmt->value)) + ";")};
            for (const auto& _for_item : enumerate(tuple_target->elts, 1))
            {
                auto i = std::get<0>(_for_item);
                auto elt = std::get<1>(_for_item);
                auto name = elt->id;
                if ((!py_in(name, scope->declared)))
                {
                    scope->declared->add(name);
                    lines->append(("var " + py_to_string(name) + " = " + py_to_string(tmp_name) + ".Item" + py_to_string(i) + ";"));
                }
                else
                {
                    lines->append((py_to_string(name) + " = " + py_to_string(tmp_name) + ".Item" + py_to_string(i) + ";"));
                }
            }
            return lines;
        }
        if (isinstance(stmt->targets[0], ast->Attribute))
        {
            auto target = this->transpile_expr(stmt->targets[0]);
            return {(py_to_string(target) + " = " + py_to_string(this->transpile_expr(stmt->value)) + ";")};
        }
        if ((!isinstance(stmt->targets[0], ast->Name)))
        {
            return {("// unsupported assignment: " + py_to_string(ast->unparse(stmt)))};
        }
        auto name = stmt->targets[0]->id;
        if ((!py_in(name, scope->declared)))
        {
            scope->declared->add(name);
            return {("var " + py_to_string(name) + " = " + py_to_string(this->transpile_expr(stmt->value)) + ";")};
        }
        return {(py_to_string(name) + " = " + py_to_string(this->transpile_expr(stmt->value)) + ";")};
    }
    vector<string> _transpile_for(ast->For stmt, pycs::gc::RcHandle<Scope> scope)
    {
        auto tuple_target = nullptr;
        auto target_name = "";
        if (isinstance(stmt->target, ast->Name))
        {
            target_name = stmt->target->id;
        }
        else
        {
            if ((isinstance(stmt->target, ast->Tuple) && all(/* comprehension */ {})))
            {
                target_name = "_for_item";
                tuple_target = stmt->target;
            }
            else
            {
                return {("// unsupported for-loop target: " + py_to_string(ast->unparse(stmt->target)))};
            }
        }
        auto lines = {("foreach (var " + py_to_string(target_name) + " in " + py_to_string(this->transpile_expr(stmt->iter)) + ")"), "{"};
        auto body_scope = pycs::gc::RcHandle<Scope>::adopt(pycs::gc::rc_new<Scope>(set(scope->declared)));
        body_scope->declared->add(target_name);
        if ((tuple_target != nullptr))
        {
            for (const auto& _for_item : enumerate(tuple_target->elts, 1))
            {
                auto i = std::get<0>(_for_item);
                auto elt = std::get<1>(_for_item);
                lines->extend(this->_indent_block({("var " + py_to_string(elt->id) + " = " + py_to_string(target_name) + ".Item" + py_to_string(i) + ";")}));
                body_scope->declared->add(elt->id);
            }
        }
        auto body_lines = this->transpile_statements(stmt->body, body_scope);
        lines->extend(this->_indent_block(body_lines));
        lines->append("}");
        if (stmt->orelse)
        {
            lines->append("// for-else is not directly supported; else body emitted below");
            lines->extend(this->transpile_statements(stmt->orelse, pycs::gc::RcHandle<Scope>::adopt(pycs::gc::rc_new<Scope>(set(scope->declared)))));
        }
        return lines;
    }
    vector<string> _transpile_try(ast->Try stmt, pycs::gc::RcHandle<Scope> scope)
    {
        auto lines = {"try", "{"};
        lines->extend(this->_indent_block(this->transpile_statements(stmt->body, pycs::gc::RcHandle<Scope>::adopt(pycs::gc::rc_new<Scope>(set(scope->declared))))));
        lines->append("}");
        for (const auto& handler : stmt->handlers)
        {
            auto ex_type = "Exception";
            if ((handler->type != nullptr))
            {
                ex_type = this->transpile_expr(handler->type);
            }
            auto ex_name = (handler->name ? handler->name : "ex");
            lines->append(("catch (" + py_to_string(ex_type) + " " + py_to_string(ex_name) + ")"));
            lines->append("{");
            auto handler_scope = pycs::gc::RcHandle<Scope>::adopt(pycs::gc::rc_new<Scope>((set(scope->declared) | {ex_name})));
            lines->extend(this->_indent_block(this->transpile_statements(handler->body, handler_scope)));
            lines->append("}");
        }
        if (stmt->finalbody)
        {
            lines->append("finally");
            lines->append("{");
            lines->extend(this->_indent_block(this->transpile_statements(stmt->finalbody, pycs::gc::RcHandle<Scope>::adopt(pycs::gc::rc_new<Scope>(set(scope->declared))))));
            lines->append("}");
        }
        if (stmt->orelse)
        {
            lines->append("// try-else is not directly supported; else body emitted below");
            lines->extend(this->transpile_statements(stmt->orelse, pycs::gc::RcHandle<Scope>::adopt(pycs::gc::rc_new<Scope>(set(scope->declared)))));
        }
        return lines;
    }
    vector<string> _transpile_raise(ast->Raise stmt)
    {
        if ((stmt->exc == nullptr))
        {
            return {"throw;"};
        }
        return {("throw new Exception(" + py_to_string(this->transpile_expr(stmt->exc)) + ");")};
    }
    vector<string> _transpile_if(ast->If stmt, pycs::gc::RcHandle<Scope> scope)
    {
        auto lines = {("if (" + py_to_string(this->transpile_expr(stmt->test)) + ")"), "{"};
        auto then_lines = this->transpile_statements(stmt->body, pycs::gc::RcHandle<Scope>::adopt(pycs::gc::rc_new<Scope>(set(scope->declared))));
        lines->extend(this->_indent_block(then_lines));
        lines->append("}");
        if (stmt->orelse)
        {
            lines->append("else");
            lines->append("{");
            auto else_lines = this->transpile_statements(stmt->orelse, pycs::gc::RcHandle<Scope>::adopt(pycs::gc::rc_new<Scope>(set(scope->declared))));
            lines->extend(this->_indent_block(else_lines));
            lines->append("}");
        }
        return lines;
    }
    string transpile_expr(ast->expr expr)
    {
        if (isinstance(expr, ast->Name))
        {
            if ((expr->id == "self"))
            {
                return "this";
            }
            return expr->id;
        }
        if (isinstance(expr, ast->Attribute))
        {
            if ((isinstance(expr->value, ast->Name) && (expr->value->id == "self") && (this->current_class_name != nullptr) && py_in(expr->attr, this->current_static_fields)))
            {
                return (py_to_string(this->current_class_name) + "." + py_to_string(expr->attr));
            }
            return (py_to_string(this->transpile_expr(expr->value)) + "." + py_to_string(expr->attr));
        }
        if (isinstance(expr, ast->Constant))
        {
            return this->_constant(expr->value);
        }
        if (isinstance(expr, ast->List))
        {
            return ("new List<object> { " + py_to_string(", "->join(/* comprehension */ {})) + " }");
        }
        if (isinstance(expr, ast->Set))
        {
            return ("new HashSet<object> { " + py_to_string(", "->join(/* comprehension */ {})) + " }");
        }
        if (isinstance(expr, ast->Tuple))
        {
            return ("Tuple.Create(" + py_to_string(", "->join(/* comprehension */ {})) + ")");
        }
        if (isinstance(expr, ast->Dict))
        {
            vector<string> entries = {};
            for (const auto& _for_item : zip(expr->keys, expr->values))
            {
                auto k = std::get<0>(_for_item);
                auto v = std::get<1>(_for_item);
                if ((k == nullptr))
                {
                    continue;
                }
                entries->append(("{ " + py_to_string(this->transpile_expr(k)) + ", " + py_to_string(this->transpile_expr(v)) + " }"));
            }
            return ("new Dictionary<object, object> { " + py_to_string(", "->join(entries)) + " }");
        }
        if (isinstance(expr, ast->BinOp))
        {
            auto left = this->transpile_expr(expr->left);
            auto right = this->transpile_expr(expr->right);
            return ("(" + py_to_string(left) + " " + py_to_string(this->_binop(expr->op)) + " " + py_to_string(right) + ")");
        }
        if (isinstance(expr, ast->UnaryOp))
        {
            return ("(" + py_to_string(this->_unaryop(expr->op)) + py_to_string(this->transpile_expr(expr->operand)) + ")");
        }
        if (isinstance(expr, ast->BoolOp))
        {
            auto op = this->_boolop(expr->op);
            return (("(" + (" " + py_to_string(op) + " ")->join(/* comprehension */ {})) + ")");
        }
        if (isinstance(expr, ast->Compare))
        {
            if (((len(expr->ops) != 1) || (len(expr->comparators) != 1)))
            {
                return "/* chained-comparison */ false";
            }
            return this->_transpile_compare(expr->left, expr->ops[0], expr->comparators[0]);
        }
        if (isinstance(expr, ast->Call))
        {
            return this->_transpile_call(expr);
        }
        if (isinstance(expr, ast->Subscript))
        {
            return (py_to_string(this->transpile_expr(expr->value)) + "[" + py_to_string(this->transpile_expr(expr->slice)) + "]");
        }
        if (isinstance(expr, ast->IfExp))
        {
            return ("(" + py_to_string(this->transpile_expr(expr->test)) + " ? " + py_to_string(this->transpile_expr(expr->body)) + " : " + py_to_string(this->transpile_expr(expr->orelse)) + ")");
        }
        if (isinstance(expr, ast->JoinedStr))
        {
            return this->_transpile_joined_str(expr);
        }
        if (isinstance(expr, std::make_tuple(ast->ListComp, ast->SetComp, ast->GeneratorExp)))
        {
            return "/* comprehension */ null";
        }
        throw std::runtime_error(py_to_string(pycs::gc::RcHandle<TranspileError>::adopt(pycs::gc::rc_new<TranspileError>(("Unsupported expression: " + py_to_string(type(expr)->__name__))))));
    }
    string _transpile_call(ast->Call call)
    {
        auto args_list = /* comprehension */ {};
        for (const auto& kw : call->keywords)
        {
            if ((kw->arg == nullptr))
            {
                args_list->append(this->transpile_expr(kw->value));
            }
            else
            {
                args_list->append((py_to_string(kw->arg) + ": " + py_to_string(this->transpile_expr(kw->value))));
            }
        }
        auto args = ", "->join(args_list);
        if ((isinstance(call->func, ast->Name) && (call->func->id == "print")))
        {
            return ("Console.WriteLine(" + py_to_string(args) + ")");
        }
        if (isinstance(call->func, ast->Name))
        {
            if (py_in(call->func->id, this->class_names))
            {
                return ("new " + py_to_string(call->func->id) + "(" + py_to_string(args) + ")");
            }
            return (py_to_string(call->func->id) + "(" + py_to_string(args) + ")");
        }
        if (isinstance(call->func, ast->Attribute))
        {
            return (py_to_string(this->transpile_expr(call->func)) + "(" + py_to_string(args) + ")");
        }
        throw std::runtime_error(py_to_string(pycs::gc::RcHandle<TranspileError>::adopt(pycs::gc::rc_new<TranspileError>("Only direct function calls are supported"))));
    }
    string _map_annotation(ast->expr annotation)
    {
        if ((isinstance(annotation, ast->Constant) && (annotation->value == nullptr)))
        {
            return "void";
        }
        if ((isinstance(annotation, ast->BinOp) && isinstance(annotation->op, ast->BitOr)))
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
            return "object";
        }
        if (isinstance(annotation, ast->Name))
        {
            auto mapping = {{ "int", "int" }, { "float", "double" }, { "str", "string" }, { "bool", "bool" }, { "None", "void" }};
            if (py_in(annotation->id, mapping))
            {
                return mapping[annotation->id];
            }
            return annotation->id;
        }
        if (isinstance(annotation, ast->Attribute))
        {
            return this->transpile_expr(annotation);
        }
        if (isinstance(annotation, ast->Subscript))
        {
            if (isinstance(annotation->value, ast->Name))
            {
                auto raw_base = annotation->value->id;
            }
            else
            {
                if (isinstance(annotation->value, ast->Attribute))
                {
                    auto raw_base = this->transpile_expr(annotation->value);
                }
                else
                {
                    return "object";
                }
            }
            auto base_map = {{ "list", "List" }, { "set", "HashSet" }, { "dict", "Dictionary" }, { "tuple", "Tuple" }};
            auto base = base_map->get(raw_base, raw_base);
            vector<string> args;
            if (isinstance(annotation->slice, ast->Tuple))
            {
                args = /* comprehension */ {};
            }
            else
            {
                args = {this->_map_annotation(annotation->slice)};
            }
            return (py_to_string(base) + "<" + py_to_string(", "->join(args)) + ">");
        }
        throw std::runtime_error(py_to_string(pycs::gc::RcHandle<TranspileError>::adopt(pycs::gc::rc_new<TranspileError>(("Unsupported type annotation: " + py_to_string(ast->unparse(annotation)))))));
    }
    bool _is_dataclass_class(ast->ClassDef cls)
    {
        for (const auto& decorator : cls->decorator_list)
        {
            if ((isinstance(decorator, ast->Name) && (decorator->id == "dataclass")))
            {
                return true;
            }
            if ((isinstance(decorator, ast->Attribute) && (decorator->attr == "dataclass")))
            {
                return true;
            }
        }
        return false;
    }
    bool _is_main_guard(ast->stmt stmt)
    {
        if ((!isinstance(stmt, ast->If)))
        {
            return false;
        }
        auto test = stmt->test;
        if ((!isinstance(test, ast->Compare)))
        {
            return false;
        }
        if (((len(test->ops) != 1) || (len(test->comparators) != 1)))
        {
            return false;
        }
        if ((!isinstance(test->ops[0], ast->Eq)))
        {
            return false;
        }
        return (isinstance(test->left, ast->Name) && (test->left->id == "__name__") && isinstance(test->comparators[0], ast->Constant) && (test->comparators[0]->value == "__main__"));
    }
    string _constant(object value)
    {
        if (isinstance(value, bool))
        {
            return (value ? "true" : "false");
        }
        if ((value == nullptr))
        {
            return "null";
        }
        if (isinstance(value, str))
        {
            auto escaped = value->replace("\\", "\\\\")->replace("\"", "\\\"");
            return ("\"" + py_to_string(escaped) + "\"");
        }
        return repr(value);
    }
    string _binop(ast->operator op)
    {
        auto mapping = {{ ast->Add, "+" }, { ast->Sub, "-" }, { ast->Mult, "*" }, { ast->Div, "/" }, { ast->Mod, "%" }, { ast->BitOr, "|" }};
        for (const auto& _for_item : mapping->items())
        {
            auto op_type = std::get<0>(_for_item);
            auto symbol = std::get<1>(_for_item);
            if (isinstance(op, op_type))
            {
                return symbol;
            }
        }
        throw std::runtime_error(py_to_string(pycs::gc::RcHandle<TranspileError>::adopt(pycs::gc::rc_new<TranspileError>(("Unsupported binary operator: " + py_to_string(type(op)->__name__))))));
    }
    string _unaryop(ast->unaryop op)
    {
        auto mapping = {{ ast->UAdd, "+" }, { ast->USub, "-" }, { ast->Not, "!" }};
        for (const auto& _for_item : mapping->items())
        {
            auto op_type = std::get<0>(_for_item);
            auto symbol = std::get<1>(_for_item);
            if (isinstance(op, op_type))
            {
                return symbol;
            }
        }
        throw std::runtime_error(py_to_string(pycs::gc::RcHandle<TranspileError>::adopt(pycs::gc::rc_new<TranspileError>(("Unsupported unary operator: " + py_to_string(type(op)->__name__))))));
    }
    string _cmpop(ast->cmpop op)
    {
        auto mapping = {{ ast->Eq, "==" }, { ast->NotEq, "!=" }, { ast->Lt, "<" }, { ast->LtE, "<=" }, { ast->Gt, ">" }, { ast->GtE, ">=" }};
        for (const auto& _for_item : mapping->items())
        {
            auto op_type = std::get<0>(_for_item);
            auto symbol = std::get<1>(_for_item);
            if (isinstance(op, op_type))
            {
                return symbol;
            }
        }
        throw std::runtime_error(py_to_string(pycs::gc::RcHandle<TranspileError>::adopt(pycs::gc::rc_new<TranspileError>(("Unsupported comparison operator: " + py_to_string(type(op)->__name__))))));
    }
    string _transpile_compare(ast->expr left_expr, ast->cmpop op, ast->expr right_expr)
    {
        auto left = this->transpile_expr(left_expr);
        auto right = this->transpile_expr(right_expr);
        if (isinstance(op, ast->In))
        {
            return (py_to_string(right) + ".Contains(" + py_to_string(left) + ")");
        }
        if (isinstance(op, ast->NotIn))
        {
            return ("!" + py_to_string(right) + ".Contains(" + py_to_string(left) + ")");
        }
        if (isinstance(op, ast->Is))
        {
            return ("object.ReferenceEquals(" + py_to_string(left) + ", " + py_to_string(right) + ")");
        }
        if (isinstance(op, ast->IsNot))
        {
            return ("!object.ReferenceEquals(" + py_to_string(left) + ", " + py_to_string(right) + ")");
        }
        return ("(" + py_to_string(left) + " " + py_to_string(this->_cmpop(op)) + " " + py_to_string(right) + ")");
    }
    string _boolop(ast->boolop op)
    {
        if (isinstance(op, ast->And))
        {
            return "&&";
        }
        if (isinstance(op, ast->Or))
        {
            return "||";
        }
        throw std::runtime_error(py_to_string(pycs::gc::RcHandle<TranspileError>::adopt(pycs::gc::rc_new<TranspileError>(("Unsupported boolean operator: " + py_to_string(type(op)->__name__))))));
    }
    string _transpile_joined_str(ast->JoinedStr expr)
    {
        vector<string> parts = {};
        for (const auto& value : expr->values)
        {
            if ((isinstance(value, ast->Constant) && isinstance(value->value, str)))
            {
                parts->append(value->value->replace("{", "{{")->replace("}", "}}"));
            }
            else
            {
                if (isinstance(value, ast->FormattedValue))
                {
                    parts->append((("{" + this->transpile_expr(value->value)) + "}"));
                }
                else
                {
                    parts->append("{/*unsupported*/}");
                }
            }
        }
        return (("$\"" + ""->join(parts)->replace("\"", "\\\"")) + "\"");
    }
    vector<string> _indent_block(vector<string> lines)
    {
        return /* comprehension */ {};
    }
};

void transpile(string input_file, string output_file)
{
    auto transpiler = pycs::gc::RcHandle<CSharpTranspiler>::adopt(pycs::gc::rc_new<CSharpTranspiler>());
    transpiler->transpile_file(Path(input_file), Path(output_file));
}

int main()
{
    auto __all__ = {"TranspileError", "CSharpTranspiler", "transpile"};
    return 0;
}
