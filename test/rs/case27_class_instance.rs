// fallback: class is not supported in native Rust mode
// このファイルは自動生成です。編集しないでください。
// 入力 Python: case27_class_instance.py

#[path = "../../src/rs_module/py_runtime.rs"]
mod py_runtime;

fn main() {
    let source: &str = r#"# このファイルは `test/py/case27_class_instance.py` のテスト/実装コードです。
# 役割が分かりやすいように、読み手向けの説明コメントを付与しています。
# 変更時は、既存仕様との整合性とテスト結果を必ず確認してください。

class Box100:
    def __init__(self, seed: int) -> None:
        self.seed = seed

    def next(self) -> int:
        self.seed += 1
        return self.seed


if __name__ == "__main__":
    b: Box100 = Box100(3)
    print(b.next())
"#;
    std::process::exit(py_runtime::run_embedded_python(source));
}
