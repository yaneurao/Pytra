// fallback: function has unsupported annotation in native Rust mode: half
// このファイルは自動生成です。編集しないでください。
// 入力 Python: case07_float.py

#[path = "../../src/rs_module/py_runtime.rs"]
mod py_runtime;

fn main() {
    let source: &str = r#"# このファイルは `test/py/case07_float.py` のテスト/実装コードです。
# 役割が分かりやすいように、読み手向けの説明コメントを付与しています。
# 変更時は、既存仕様との整合性とテスト結果を必ず確認してください。

def half(x: float) -> float:
    return x / 2.0


if __name__ == "__main__":
    print(half(5.0))
"#;
    std::process::exit(py_runtime::run_embedded_python(source));
}
