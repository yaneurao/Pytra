// fallback: unsupported annotation: Subscript(value=Name(id='list', ctx=Load()), slice=Name(id='int', ctx=Load()), ctx=Load())
// このファイルは自動生成です。編集しないでください。
// 入力 Python: case22_comprehension.py

#[path = "../../src/rs_module/py_runtime.rs"]
mod py_runtime;

fn main() {
    let source: &str = r#"# このファイルは `test/py/case22_comprehension.py` のテスト/実装コードです。
# 役割が分かりやすいように、読み手向けの説明コメントを付与しています。
# 変更時は、既存仕様との整合性とテスト結果を必ず確認してください。

def comp_like_24(x: int) -> int:
    values: list[int] = [i for i in [1, 2, 3, 4]]
    return x + 1


if __name__ == "__main__":
    print(comp_like_24(5))
"#;
    std::process::exit(py_runtime::run_embedded_python(source));
}
