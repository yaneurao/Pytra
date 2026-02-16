// fallback: function has unsupported annotation in native Rust mode: make_msg_22
// このファイルは自動生成です。編集しないでください。
// 入力 Python: case20_fstring.py

#[path = "../../src/rs_module/py_runtime.rs"]
mod py_runtime;

fn main() {
    let source: &str = r#"# このファイルは `test/py/case20_fstring.py` のテスト/実装コードです。
# 役割が分かりやすいように、読み手向けの説明コメントを付与しています。
# 変更時は、既存仕様との整合性とテスト結果を必ず確認してください。

def make_msg_22(name: str, count: int) -> str:
    return f"{name}:22:{count}"


if __name__ == "__main__":
    print(make_msg_22("user", 7))
"#;
    std::process::exit(py_runtime::run_embedded_python(source));
}
