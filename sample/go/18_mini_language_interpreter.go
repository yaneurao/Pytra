// このファイルは EAST ベース Go プレビュー出力です。
// TODO: 専用 GoEmitter 実装へ段階移行する。
package main

func main() {
    // C# ベース中間出力のシグネチャ要約:
    // public class Token
    // public string kind;
    // public string text;
    // public long pos;
    // public static string kind;
    // public static string text;
    // public static long pos;
    //
    // public class ExprNode
    // public string kind;
    // public long value;
    // public string name;
    // public string op;
    // public long left;
    // public long right;
    // public static string kind;
    // public static long value;
    // public static string name;
    // public static string op;
    // public static long left;
    // public static long right;
    //
    // public class StmtNode
    // public string kind;
    // public string name;
    // public long expr_index;
    // public static string kind;
    // public static string name;
    // public static long expr_index;
    //
    // public class Parser
    // public System.Collections.Generic.List<Token> tokens;
    // public long pos;
    // public System.Collections.Generic.List<ExprNode> expr_nodes;
    //
    // public Parser(System.Collections.Generic.List<Token> tokens)
    //
    // public System.Collections.Generic.List<ExprNode> new_expr_nodes()
    //
    // public string peek_kind()
    //
    // public bool match(string kind)
    //
    // public Token expect(string kind)
    //
    // public void skip_newlines()
    // // pass
    //
    // public long add_expr(ExprNode node)
    //
    // public System.Collections.Generic.List<StmtNode> parse_program()
    //
    // public StmtNode parse_stmt()
    //
    // public long parse_expr()
    //
    // public long parse_add()
    //
    // public long parse_mul()
    //
    // public long parse_unary()
    //
    // public long parse_primary()
    //
    // public static class Program
    // public static System.Collections.Generic.List<Token> tokenize(System.Collections.Generic.List<string> lines)
    //
    //
    // public static long eval_expr(long expr_index, System.Collections.Generic.List<ExprNode> expr_nodes, System.Collections.Generic.Dictionary<string, long> env)
    //
    //
    // public static long execute(System.Collections.Generic.List<StmtNode> stmts, System.Collections.Generic.List<ExprNode> expr_nodes, bool trace)
    //
    //
    // public static System.Collections.Generic.List<string> build_benchmark_source(long var_count, long loops)
    //
    // // Declare initial variables.
    // // Force evaluation of many arithmetic expressions.
    // // Print final values together.
    //
    // public static void run_demo()
    //
    //
    // public static void run_benchmark()
    //
    //
    // public static void __pytra_main()
    //
    //
    // public static void Main(string[] args)
}
