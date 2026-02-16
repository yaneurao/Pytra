// fallback: unsupported annotation: Subscript(value=Name(id='list', ctx=Load()), slice=Name(id='int', ctx=Load()), ctx=Load())
// このファイルは自動生成です。編集しないでください。
// 入力 Python: case17_loop.py

#[path = "../../src/rs_module/py_runtime.rs"]
mod py_runtime;

fn main() {
    let source: &str = r#"# このファイルは `test/py/case17_loop.py` のテスト/実装コードです。
# 役割が分かりやすいように、読み手向けの説明コメントを付与しています。
# 変更時は、既存仕様との整合性とテスト結果を必ず確認してください。

def calc_17(values: list[int]) -> int:
    total: int = 0
    for v in values:
        if v % 2 == 0:
            total += v
        else:
            total += (v * 2)
    return total


if __name__ == "__main__":
    print(calc_17([1, 2, 3, 4]))
"#;
    std::process::exit(py_runtime::run_embedded_python(source));
}
