// このファイルは `test/cs/self_pycs_transpiler.cs` の変換結果（C#サンプル）です。
// Python入力との対応関係を追いやすくするため、日本語コメントを付与しています。
// 仕様変更時は、対応する Python 側ケースと合わせて更新してください。

using System;

public static class Program
{
    public static void transpile(string input_file, string output_file)
    {
        var transpiler = new CSharpTranspiler();
        transpiler.transpile_file(Path(input_file), Path(output_file));
    }

    public class TranspileError : Exception
    {
    }

    public class Scope
    {
        public static Set<string> declared;

    }

    public class CSharpTranspiler
    {
        public static string INDENT = "    ";
        public Set<string> class_names;
        public string current_class_name;
        public Set<string> current_static_fields;

        public CSharpTranspiler()
        {
            this.class_names = set();
            this.current_class_name = null;
            this.current_static_fields = set();
        }
        public void transpile_file(Path input_path, Path output_path)
        {
            var source = input_path.read_text(encoding: "utf-8");
            var tree = ast.parse(source, filename: str(input_path));
            var csharp = this.transpile_module(tree);
            output_path.write_text(csharp, encoding: "utf-8");
        }
        public string transpile_module(ast.Module module)
        {
            List<string> function_defs = new List<object> {  };
            List<string> class_defs = new List<object> {  };
            List<ast.stmt> top_level_body = new List<object> {  };
            this.class_names = /* comprehension */ null;
            foreach (var stmt in module.body)
            {
                if (isinstance(stmt, ast.FunctionDef))
                {
                    function_defs.append(this.transpile_function(stmt));
                }
                else
                {
                    if (isinstance(stmt, ast.ClassDef))
                    {
                        class_defs.append(this.transpile_class(stmt));
                    }
                    else
                    {
                        top_level_body.append(stmt);
                    }
                }
            }
            List<ast.stmt> main_stmts = new List<object> {  };
            foreach (var stmt in top_level_body)
            {
                if (this._is_main_guard(stmt))
                {
                    main_stmts.extend(stmt.body);
                }
                else
                {
                    main_stmts.append(stmt);
                }
            }
            var main_method = this.transpile_main(main_stmts);
            var parts = new List<object> { "using System;", "", "public static class Program", "{" };
            foreach (var fn in function_defs)
            {
                parts.extend(this._indent_block(fn.splitlines()));
                parts.append("");
            }
            foreach (var cls in class_defs)
            {
                parts.extend(this._indent_block(cls.splitlines()));
                parts.append("");
            }
            parts.extend(this._indent_block(main_method.splitlines()));
            parts.append("}");
            parts.append("");
            return "
        ".join(parts);
        }
        public string transpile_class(ast.ClassDef cls)
        {
            if ((len(cls.bases) > 1))
            {
                throw new Exception(new TranspileError($"Class '{cls.name}' multiple inheritance is not supported"));
            }
            var base = "";
            if (cls.bases)
            {
                if ((!isinstance(cls.bases[0], ast.Name)))
                {
                    throw new Exception(new TranspileError($"Class '{cls.name}' base class must be a simple name"));
                }
                base = $" : {cls.bases[0].id}";
            }
            List<string> static_fields = new List<object> {  };
            Set<string> static_field_names = set();
            List<ast.FunctionDef> methods = new List<object> {  };
            foreach (var stmt in cls.body)
            {
                if (isinstance(stmt, ast.FunctionDef))
                {
                    methods.append(stmt);
                }
                else
                {
                    if (isinstance(stmt, ast.AnnAssign))
                    {
                        var _tmp_tuple = this._transpile_class_static_field(stmt);
                        var field_line = _tmp_tuple.Item1;
                        var field_name = _tmp_tuple.Item2;
                        static_fields.append(field_line);
                        static_field_names.add(field_name);
                    }
                    else
                    {
                        if (isinstance(stmt, ast.Assign))
                        {
                            var _tmp_tuple = this._transpile_class_static_assign(stmt);
                            var field_line = _tmp_tuple.Item1;
                            var field_name = _tmp_tuple.Item2;
                            static_fields.append(field_line);
                            static_field_names.add(field_name);
                        }
                        else
                        {
                            if (isinstance(stmt, ast.Pass))
                            {
                                continue;
                            }
                            else
                            {
                                throw new Exception(new TranspileError($"Unsupported class member in '{cls.name}': {type(stmt).__name__}"));
                            }
                        }
                    }
                }
            }
            var instance_fields = this._collect_instance_fields(cls, static_field_names);
            var lines = new List<object> { $"public class {cls.name}{base}", "{" };
            foreach (var static_field in static_fields)
            {
                lines.extend(this._indent_block(new List<object> { static_field }));
            }
            foreach (var _for_item in instance_fields)
            {
                var _ = _for_item.Item1;
                var field_type = _for_item.Item2;
                var field_name = _for_item.Item3;
                lines.extend(this._indent_block(new List<object> { $"public {field_type} {field_name};" }));
            }
            if ((static_fields || instance_fields))
            {
                lines.extend(this._indent_block(new List<object> { "" }));
            }
            var prev_class_name = this.current_class_name;
            var prev_static_fields = this.current_static_fields;
            this.current_class_name = cls.name;
            this.current_static_fields = static_field_names;
            try
            {
                foreach (var method in methods)
                {
                    lines.extend(this._indent_block(this.transpile_function(method, in_class: true).splitlines()));
                }
            }
            finally
            {
                this.current_class_name = prev_class_name;
                this.current_static_fields = prev_static_fields;
            }
            lines.append("}");
            return "
        ".join(lines);
        }
        public Tuple<string, string> _transpile_class_static_field(ast.AnnAssign stmt)
        {
            if ((!isinstance(stmt.target, ast.Name)))
            {
                throw new Exception(new TranspileError("Class field declaration must be a simple name"));
            }
            var field_type = this._map_annotation(stmt.annotation);
            var field_name = stmt.target.id;
            if (object.ReferenceEquals(stmt.value, null))
            {
                return Tuple.Create($"public static {field_type} {field_name};", field_name);
            }
            return Tuple.Create($"public static {field_type} {field_name} = {this.transpile_expr(stmt.value)};", field_name);
        }
        public Tuple<string, string> _transpile_class_static_assign(ast.Assign stmt)
        {
            if (((len(stmt.targets) != 1) || (!isinstance(stmt.targets[0], ast.Name))))
            {
                throw new Exception(new TranspileError("Class static assignment must be a simple name assignment"));
            }
            var field_name = stmt.targets[0].id;
            var field_type = (this._infer_expr_csharp_type(stmt.value) || "object");
            return Tuple.Create($"public static {field_type} {field_name} = {this.transpile_expr(stmt.value)};", field_name);
        }
        public List<Tuple<string, string, string>> _collect_instance_fields(ast.ClassDef cls, Set<string> static_field_names)
        {
            List<Tuple<string, string, string>> fields = new List<object> {  };
            Set<string> seen = set();
            var init_fn = null;
            foreach (var stmt in cls.body)
            {
                if ((isinstance(stmt, ast.FunctionDef) && (stmt.name == "__init__")))
                {
                    init_fn = stmt;
                    break;
                }
            }
            if (object.ReferenceEquals(init_fn, null))
            {
                return fields;
            }
            Dictionary<string, string> arg_types = new Dictionary<object, object> {  };
            foreach (var _for_item in enumerate(init_fn.args.args))
            {
                var idx = _for_item.Item1;
                var arg = _for_item.Item2;
                if (((idx == 0) && (arg.arg == "self")))
                {
                    continue;
                }
                if (!object.ReferenceEquals(arg.annotation, null))
                {
                    // unsupported assignment: arg_types[arg.arg] = self._map_annotation(arg.annotation)
                }
            }
            foreach (var stmt in init_fn.body)
            {
                string field_name = null;
                string field_type = null;
                if (isinstance(stmt, ast.AnnAssign))
                {
                    if ((isinstance(stmt.target, ast.Attribute) && isinstance(stmt.target.value, ast.Name) && (stmt.target.value.id == "self")))
                    {
                        field_name = stmt.target.attr;
                        field_type = this._map_annotation(stmt.annotation);
                    }
                }
                else
                {
                    if (isinstance(stmt, ast.Assign))
                    {
                        if (((len(stmt.targets) == 1) && isinstance(stmt.targets[0], ast.Attribute) && isinstance(stmt.targets[0].value, ast.Name) && (stmt.targets[0].value.id == "self")))
                        {
                            field_name = stmt.targets[0].attr;
                            field_type = this._infer_type(stmt.value, arg_types);
                        }
                    }
                }
                if ((object.ReferenceEquals(field_name, null) || object.ReferenceEquals(field_type, null)))
                {
                    continue;
                }
                if (static_field_names.Contains(field_name))
                {
                    continue;
                }
                if (seen.Contains(field_name))
                {
                    continue;
                }
                seen.add(field_name);
                fields.append(Tuple.Create(cls.name, field_type, field_name));
            }
            return fields;
        }
        public string _infer_type(ast.expr expr, Dictionary<string, string> arg_types)
        {
            if (isinstance(expr, ast.Name))
            {
                return arg_types.get(expr.id);
            }
            if (isinstance(expr, ast.Constant))
            {
                return this._infer_expr_csharp_type(expr);
            }
            if ((isinstance(expr, ast.Call) && isinstance(expr.func, ast.Name)))
            {
                if (this.class_names.Contains(expr.func.id))
                {
                    return expr.func.id;
                }
            }
            return null;
        }
        public string _infer_expr_csharp_type(ast.expr expr)
        {
            if (isinstance(expr, ast.Constant))
            {
                if (isinstance(expr.value, bool))
                {
                    return "bool";
                }
                if (isinstance(expr.value, int))
                {
                    return "int";
                }
                if (isinstance(expr.value, float))
                {
                    return "double";
                }
                if (isinstance(expr.value, str))
                {
                    return "string";
                }
                return null;
            }
            return null;
        }
        public string transpile_function(ast.FunctionDef fn, bool in_class)
        {
            var is_constructor = (in_class && (fn.name == "__init__"));
            if (object.ReferenceEquals(fn.returns, null))
            {
                throw new Exception(new TranspileError($"Function '{fn.name}' requires return type annotation"));
            }
            var return_type = this._map_annotation(fn.returns);
            List<string> params = new List<object> {  };
            var declared = set();
            foreach (var _for_item in enumerate(fn.args.args))
            {
                var idx = _for_item.Item1;
                var arg = _for_item.Item2;
                if ((in_class && (idx == 0) && (arg.arg == "self")))
                {
                    declared.add("self");
                    continue;
                }
                if (object.ReferenceEquals(arg.annotation, null))
                {
                    throw new Exception(new TranspileError($"Function '{fn.name}' argument '{arg.arg}' requires type annotation"));
                }
                params.append($"{this._map_annotation(arg.annotation)} {arg.arg}");
                declared.add(arg.arg);
            }
            var body_lines = this.transpile_statements(fn.body, new Scope(declared: declared));
            if (is_constructor)
            {
                if (object.ReferenceEquals(this.current_class_name, null))
                {
                    throw new Exception(new TranspileError("Constructor conversion requires class context"));
                }
                if ((return_type != "void"))
                {
                    throw new Exception(new TranspileError("__init__ return type must be None"));
                }
                var signature = $"public {this.current_class_name}({\", \".join(params)})";
            }
            else
            {
                var modifier = (in_class ? "public" : "public static");
                var signature = $"{modifier} {return_type} {fn.name}({\", \".join(params)})";
            }
            var lines = new List<object> { signature, "{" };
            lines.extend(this._indent_block(body_lines));
            lines.append("}");
            return "
        ".join(lines);
        }
        public string transpile_main(List<ast.stmt> body)
        {
            var lines = new List<object> { "public static void Main(string[] args)", "{" };
            var body_lines = this.transpile_statements(body, new Scope(declared: new HashSet<object> { "args" }));
            lines.extend(this._indent_block(body_lines));
            lines.append("}");
            return "
        ".join(lines);
        }
        public List<string> transpile_statements(List<ast.stmt> stmts, Scope scope)
        {
            List<string> lines = new List<object> {  };
            foreach (var stmt in stmts)
            {
                if (isinstance(stmt, Tuple.Create(ast.Import, ast.ImportFrom)))
                {
                    lines.append($"// {ast.unparse(stmt)}");
                    continue;
                }
                if (isinstance(stmt, ast.Return))
                {
                    if (object.ReferenceEquals(stmt.value, null))
                    {
                        lines.append("return;");
                    }
                    else
                    {
                        lines.append($"return {this.transpile_expr(stmt.value)};");
                    }
                }
                else
                {
                    if (isinstance(stmt, ast.Expr))
                    {
                        lines.append($"{this.transpile_expr(stmt.value)};");
                    }
                    else
                    {
                        if (isinstance(stmt, ast.AnnAssign))
                        {
                            lines.extend(this._transpile_ann_assign(stmt, scope));
                        }
                        else
                        {
                            if (isinstance(stmt, ast.Assign))
                            {
                                lines.extend(this._transpile_assign(stmt, scope));
                            }
                            else
                            {
                                if (isinstance(stmt, ast.If))
                                {
                                    lines.extend(this._transpile_if(stmt, scope));
                                }
                                else
                                {
                                    if (isinstance(stmt, ast.For))
                                    {
                                        lines.extend(this._transpile_for(stmt, scope));
                                    }
                                    else
                                    {
                                        if (isinstance(stmt, ast.Try))
                                        {
                                            lines.extend(this._transpile_try(stmt, scope));
                                        }
                                        else
                                        {
                                            if (isinstance(stmt, ast.Raise))
                                            {
                                                lines.extend(this._transpile_raise(stmt));
                                            }
                                            else
                                            {
                                                if (isinstance(stmt, ast.Break))
                                                {
                                                    lines.append("break;");
                                                }
                                                else
                                                {
                                                    if (isinstance(stmt, ast.Continue))
                                                    {
                                                        lines.append("continue;");
                                                    }
                                                    else
                                                    {
                                                        if (isinstance(stmt, ast.Pass))
                                                        {
                                                            continue;
                                                        }
                                                        else
                                                        {
                                                            throw new Exception(new TranspileError($"Unsupported statement: {type(stmt).__name__}"));
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
        public List<string> _transpile_ann_assign(ast.AnnAssign stmt, Scope scope)
        {
            if (isinstance(stmt.target, ast.Attribute))
            {
                if ((isinstance(stmt.target.value, ast.Name) && (stmt.target.value.id == "self")))
                {
                    if (object.ReferenceEquals(stmt.value, null))
                    {
                        throw new Exception(new TranspileError("Annotated assignment to self attributes requires an initializer"));
                    }
                    return new List<object> { $"{this.transpile_expr(stmt.target)} = {this.transpile_expr(stmt.value)};" };
                }
                throw new Exception(new TranspileError("Annotated assignment to attributes is not supported"));
            }
            if ((!isinstance(stmt.target, ast.Name)))
            {
                throw new Exception(new TranspileError("Only simple annotated assignments are supported"));
            }
            var name = stmt.target.id;
            var csharp_type = this._map_annotation(stmt.annotation);
            if (object.ReferenceEquals(stmt.value, null))
            {
                var line = $"{csharp_type} {name};";
            }
            else
            {
                var line = $"{csharp_type} {name} = {this.transpile_expr(stmt.value)};";
            }
            scope.declared.add(name);
            return new List<object> { line };
        }
        public List<string> _transpile_assign(ast.Assign stmt, Scope scope)
        {
            if ((len(stmt.targets) != 1))
            {
                return new List<object> { $"// unsupported assignment: {ast.unparse(stmt)}" };
            }
            if (isinstance(stmt.targets[0], ast.Tuple))
            {
                var tuple_target = stmt.targets[0];
                if ((!all(/* comprehension */ null)))
                {
                    return new List<object> { $"// unsupported tuple assignment: {ast.unparse(stmt)}" };
                }
                var tmp_name = "_tmp_tuple";
                var lines = new List<object> { $"var {tmp_name} = {this.transpile_expr(stmt.value)};" };
                foreach (var _for_item in enumerate(tuple_target.elts, start: 1))
                {
                    var i = _for_item.Item1;
                    var elt = _for_item.Item2;
                    var name = elt.id;
                    if (!scope.declared.Contains(name))
                    {
                        scope.declared.add(name);
                        lines.append($"var {name} = {tmp_name}.Item{i};");
                    }
                    else
                    {
                        lines.append($"{name} = {tmp_name}.Item{i};");
                    }
                }
                return lines;
            }
            if (isinstance(stmt.targets[0], ast.Attribute))
            {
                var target = this.transpile_expr(stmt.targets[0]);
                return new List<object> { $"{target} = {this.transpile_expr(stmt.value)};" };
            }
            if ((!isinstance(stmt.targets[0], ast.Name)))
            {
                return new List<object> { $"// unsupported assignment: {ast.unparse(stmt)}" };
            }
            var name = stmt.targets[0].id;
            if (!scope.declared.Contains(name))
            {
                scope.declared.add(name);
                return new List<object> { $"var {name} = {this.transpile_expr(stmt.value)};" };
            }
            return new List<object> { $"{name} = {this.transpile_expr(stmt.value)};" };
        }
        public List<string> _transpile_for(ast.For stmt, Scope scope)
        {
            var tuple_target = null;
            var target_name = "";
            if (isinstance(stmt.target, ast.Name))
            {
                target_name = stmt.target.id;
            }
            else
            {
                if ((isinstance(stmt.target, ast.Tuple) && all(/* comprehension */ null)))
                {
                    target_name = "_for_item";
                    tuple_target = stmt.target;
                }
                else
                {
                    return new List<object> { $"// unsupported for-loop target: {ast.unparse(stmt.target)}" };
                }
            }
            var lines = new List<object> { $"foreach (var {target_name} in {this.transpile_expr(stmt.iter)})", "{" };
            var body_scope = new Scope(declared: set(scope.declared));
            body_scope.declared.add(target_name);
            if (!object.ReferenceEquals(tuple_target, null))
            {
                foreach (var _for_item in enumerate(tuple_target.elts, start: 1))
                {
                    var i = _for_item.Item1;
                    var elt = _for_item.Item2;
                    lines.extend(this._indent_block(new List<object> { $"var {elt.id} = {target_name}.Item{i};" }));
                    body_scope.declared.add(elt.id);
                }
            }
            var body_lines = this.transpile_statements(stmt.body, body_scope);
            lines.extend(this._indent_block(body_lines));
            lines.append("}");
            if (stmt.orelse)
            {
                lines.append("// for-else is not directly supported; else body emitted below");
                lines.extend(this.transpile_statements(stmt.orelse, new Scope(declared: set(scope.declared))));
            }
            return lines;
        }
        public List<string> _transpile_try(ast.Try stmt, Scope scope)
        {
            var lines = new List<object> { "try", "{" };
            lines.extend(this._indent_block(this.transpile_statements(stmt.body, new Scope(declared: set(scope.declared)))));
            lines.append("}");
            foreach (var handler in stmt.handlers)
            {
                var ex_type = "Exception";
                if (!object.ReferenceEquals(handler.type, null))
                {
                    ex_type = this.transpile_expr(handler.type);
                }
                var ex_name = (handler.name ? handler.name : "ex");
                lines.append($"catch ({ex_type} {ex_name})");
                lines.append("{");
                var handler_scope = new Scope(declared: (set(scope.declared) | new HashSet<object> { ex_name }));
                lines.extend(this._indent_block(this.transpile_statements(handler.body, handler_scope)));
                lines.append("}");
            }
            if (stmt.finalbody)
            {
                lines.append("finally");
                lines.append("{");
                lines.extend(this._indent_block(this.transpile_statements(stmt.finalbody, new Scope(declared: set(scope.declared)))));
                lines.append("}");
            }
            if (stmt.orelse)
            {
                lines.append("// try-else is not directly supported; else body emitted below");
                lines.extend(this.transpile_statements(stmt.orelse, new Scope(declared: set(scope.declared))));
            }
            return lines;
        }
        public List<string> _transpile_raise(ast.Raise stmt)
        {
            if (object.ReferenceEquals(stmt.exc, null))
            {
                return new List<object> { "throw;" };
            }
            return new List<object> { $"throw new Exception({this.transpile_expr(stmt.exc)});" };
        }
        public List<string> _transpile_if(ast.If stmt, Scope scope)
        {
            var lines = new List<object> { $"if ({this.transpile_expr(stmt.test)})", "{" };
            var then_lines = this.transpile_statements(stmt.body, new Scope(declared: set(scope.declared)));
            lines.extend(this._indent_block(then_lines));
            lines.append("}");
            if (stmt.orelse)
            {
                lines.append("else");
                lines.append("{");
                var else_lines = this.transpile_statements(stmt.orelse, new Scope(declared: set(scope.declared)));
                lines.extend(this._indent_block(else_lines));
                lines.append("}");
            }
            return lines;
        }
        public string transpile_expr(ast.expr expr)
        {
            if (isinstance(expr, ast.Name))
            {
                if ((expr.id == "self"))
                {
                    return "this";
                }
                return expr.id;
            }
            if (isinstance(expr, ast.Attribute))
            {
                if ((isinstance(expr.value, ast.Name) && (expr.value.id == "self") && !object.ReferenceEquals(this.current_class_name, null) && this.current_static_fields.Contains(expr.attr)))
                {
                    return $"{this.current_class_name}.{expr.attr}";
                }
                return $"{this.transpile_expr(expr.value)}.{expr.attr}";
            }
            if (isinstance(expr, ast.Constant))
            {
                return this._constant(expr.value);
            }
            if (isinstance(expr, ast.List))
            {
                return $"new List<object> {{ {\", \".join(/* comprehension */ null)} }}";
            }
            if (isinstance(expr, ast.Set))
            {
                return $"new HashSet<object> {{ {\", \".join(/* comprehension */ null)} }}";
            }
            if (isinstance(expr, ast.Tuple))
            {
                return $"Tuple.Create({\", \".join(/* comprehension */ null)})";
            }
            if (isinstance(expr, ast.Dict))
            {
                List<string> entries = new List<object> {  };
                foreach (var _for_item in zip(expr.keys, expr.values))
                {
                    var k = _for_item.Item1;
                    var v = _for_item.Item2;
                    if (object.ReferenceEquals(k, null))
                    {
                        continue;
                    }
                    entries.append($"{{ {this.transpile_expr(k)}, {this.transpile_expr(v)} }}");
                }
                return $"new Dictionary<object, object> {{ {\", \".join(entries)} }}";
            }
            if (isinstance(expr, ast.BinOp))
            {
                var left = this.transpile_expr(expr.left);
                var right = this.transpile_expr(expr.right);
                return $"({left} {this._binop(expr.op)} {right})";
            }
            if (isinstance(expr, ast.UnaryOp))
            {
                return $"({this._unaryop(expr.op)}{this.transpile_expr(expr.operand)})";
            }
            if (isinstance(expr, ast.BoolOp))
            {
                var op = this._boolop(expr.op);
                return (("(" + $" {op} ".join(/* comprehension */ null)) + ")");
            }
            if (isinstance(expr, ast.Compare))
            {
                if (((len(expr.ops) != 1) || (len(expr.comparators) != 1)))
                {
                    return "/* chained-comparison */ false";
                }
                return this._transpile_compare(expr.left, expr.ops[0], expr.comparators[0]);
            }
            if (isinstance(expr, ast.Call))
            {
                return this._transpile_call(expr);
            }
            if (isinstance(expr, ast.Subscript))
            {
                return $"{this.transpile_expr(expr.value)}[{this.transpile_expr(expr.slice)}]";
            }
            if (isinstance(expr, ast.IfExp))
            {
                return $"({this.transpile_expr(expr.test)} ? {this.transpile_expr(expr.body)} : {this.transpile_expr(expr.orelse)})";
            }
            if (isinstance(expr, ast.JoinedStr))
            {
                return this._transpile_joined_str(expr);
            }
            if (isinstance(expr, Tuple.Create(ast.ListComp, ast.SetComp, ast.GeneratorExp)))
            {
                return "/* comprehension */ null";
            }
            throw new Exception(new TranspileError($"Unsupported expression: {type(expr).__name__}"));
        }
        public string _transpile_call(ast.Call call)
        {
            var args_list = /* comprehension */ null;
            foreach (var kw in call.keywords)
            {
                if (object.ReferenceEquals(kw.arg, null))
                {
                    args_list.append(this.transpile_expr(kw.value));
                }
                else
                {
                    args_list.append($"{kw.arg}: {this.transpile_expr(kw.value)}");
                }
            }
            var args = ", ".join(args_list);
            if ((isinstance(call.func, ast.Name) && (call.func.id == "print")))
            {
                return $"Console.WriteLine({args})";
            }
            if (isinstance(call.func, ast.Name))
            {
                if (this.class_names.Contains(call.func.id))
                {
                    return $"new {call.func.id}({args})";
                }
                return $"{call.func.id}({args})";
            }
            if (isinstance(call.func, ast.Attribute))
            {
                return $"{this.transpile_expr(call.func)}({args})";
            }
            throw new Exception(new TranspileError("Only direct function calls are supported"));
        }
        public string _map_annotation(ast.expr annotation)
        {
            if ((isinstance(annotation, ast.Constant) && object.ReferenceEquals(annotation.value, null)))
            {
                return "void";
            }
            if ((isinstance(annotation, ast.BinOp) && isinstance(annotation.op, ast.BitOr)))
            {
                var left = this._map_annotation(annotation.left);
                var right = this._map_annotation(annotation.right);
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
            if (isinstance(annotation, ast.Name))
            {
                var mapping = new Dictionary<object, object> { { "int", "int" }, { "float", "double" }, { "str", "string" }, { "bool", "bool" }, { "None", "void" } };
                if (mapping.Contains(annotation.id))
                {
                    return mapping[annotation.id];
                }
                return annotation.id;
            }
            if (isinstance(annotation, ast.Attribute))
            {
                return this.transpile_expr(annotation);
            }
            if (isinstance(annotation, ast.Subscript))
            {
                if (isinstance(annotation.value, ast.Name))
                {
                    var raw_base = annotation.value.id;
                }
                else
                {
                    if (isinstance(annotation.value, ast.Attribute))
                    {
                        var raw_base = this.transpile_expr(annotation.value);
                    }
                    else
                    {
                        return "object";
                    }
                }
                var base_map = new Dictionary<object, object> { { "list", "List" }, { "set", "HashSet" }, { "dict", "Dictionary" }, { "tuple", "Tuple" } };
                var base = base_map.get(raw_base, raw_base);
                List<string> args;
                if (isinstance(annotation.slice, ast.Tuple))
                {
                    args = /* comprehension */ null;
                }
                else
                {
                    args = new List<object> { this._map_annotation(annotation.slice) };
                }
                return $"{base}<{\", \".join(args)}>";
            }
            throw new Exception(new TranspileError($"Unsupported type annotation: {ast.unparse(annotation)}"));
        }
        public bool _is_main_guard(ast.stmt stmt)
        {
            if ((!isinstance(stmt, ast.If)))
            {
                return false;
            }
            var test = stmt.test;
            if ((!isinstance(test, ast.Compare)))
            {
                return false;
            }
            if (((len(test.ops) != 1) || (len(test.comparators) != 1)))
            {
                return false;
            }
            if ((!isinstance(test.ops[0], ast.Eq)))
            {
                return false;
            }
            return (isinstance(test.left, ast.Name) && (test.left.id == "__name__") && isinstance(test.comparators[0], ast.Constant) && (test.comparators[0].value == "__main__"));
        }
        public string _constant(object value)
        {
            if (isinstance(value, bool))
            {
                return (value ? "true" : "false");
            }
            if (object.ReferenceEquals(value, null))
            {
                return "null";
            }
            if (isinstance(value, str))
            {
                var escaped = value.replace("\\", "\\\\").replace("\"", "\\\"");
                return $"\"{escaped}\"";
            }
            return repr(value);
        }
        public string _binop(ast.operator op)
        {
            var mapping = new Dictionary<object, object> { { ast.Add, "+" }, { ast.Sub, "-" }, { ast.Mult, "*" }, { ast.Div, "/" }, { ast.Mod, "%" }, { ast.BitOr, "|" } };
            foreach (var _for_item in mapping.items())
            {
                var op_type = _for_item.Item1;
                var symbol = _for_item.Item2;
                if (isinstance(op, op_type))
                {
                    return symbol;
                }
            }
            throw new Exception(new TranspileError($"Unsupported binary operator: {type(op).__name__}"));
        }
        public string _unaryop(ast.unaryop op)
        {
            var mapping = new Dictionary<object, object> { { ast.UAdd, "+" }, { ast.USub, "-" }, { ast.Not, "!" } };
            foreach (var _for_item in mapping.items())
            {
                var op_type = _for_item.Item1;
                var symbol = _for_item.Item2;
                if (isinstance(op, op_type))
                {
                    return symbol;
                }
            }
            throw new Exception(new TranspileError($"Unsupported unary operator: {type(op).__name__}"));
        }
        public string _cmpop(ast.cmpop op)
        {
            var mapping = new Dictionary<object, object> { { ast.Eq, "==" }, { ast.NotEq, "!=" }, { ast.Lt, "<" }, { ast.LtE, "<=" }, { ast.Gt, ">" }, { ast.GtE, ">=" } };
            foreach (var _for_item in mapping.items())
            {
                var op_type = _for_item.Item1;
                var symbol = _for_item.Item2;
                if (isinstance(op, op_type))
                {
                    return symbol;
                }
            }
            throw new Exception(new TranspileError($"Unsupported comparison operator: {type(op).__name__}"));
        }
        public string _transpile_compare(ast.expr left_expr, ast.cmpop op, ast.expr right_expr)
        {
            var left = this.transpile_expr(left_expr);
            var right = this.transpile_expr(right_expr);
            if (isinstance(op, ast.In))
            {
                return $"{right}.Contains({left})";
            }
            if (isinstance(op, ast.NotIn))
            {
                return $"!{right}.Contains({left})";
            }
            if (isinstance(op, ast.Is))
            {
                return $"object.ReferenceEquals({left}, {right})";
            }
            if (isinstance(op, ast.IsNot))
            {
                return $"!object.ReferenceEquals({left}, {right})";
            }
            return $"({left} {this._cmpop(op)} {right})";
        }
        public string _boolop(ast.boolop op)
        {
            if (isinstance(op, ast.And))
            {
                return "&&";
            }
            if (isinstance(op, ast.Or))
            {
                return "||";
            }
            throw new Exception(new TranspileError($"Unsupported boolean operator: {type(op).__name__}"));
        }
        public string _transpile_joined_str(ast.JoinedStr expr)
        {
            List<string> parts = new List<object> {  };
            foreach (var value in expr.values)
            {
                if ((isinstance(value, ast.Constant) && isinstance(value.value, str)))
                {
                    parts.append(value.value.replace("{", "{{").replace("}", "}}"));
                }
                else
                {
                    if (isinstance(value, ast.FormattedValue))
                    {
                        parts.append((("{" + this.transpile_expr(value.value)) + "}"));
                    }
                    else
                    {
                        parts.append("{/*unsupported*/}");
                    }
                }
            }
            return (("$\"" + "".join(parts).replace("\"", "\\\"")) + "\"");
        }
        public List<string> _indent_block(List<string> lines)
        {
            return /* comprehension */ null;
        }
    }

    public static void Main(string[] args)
    {
        // import ast
        // from dataclasses import dataclass
        // from pathlib import Path
        // from typing import List, Set
        var __all__ = new List<object> { "TranspileError", "CSharpTranspiler", "transpile" };
    }
}
