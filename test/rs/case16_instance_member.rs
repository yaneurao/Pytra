// fallback: class is not supported in native Rust mode
// このファイルは自動生成です。編集しないでください。
// 入力 Python: case16_instance_member.py

#[path = "../../src/rs_module/py_runtime.rs"]
mod py_runtime;

fn main() {
    let source: &str = r#"# このファイルは `test/py/case16_instance_member.py` のテスト/実装コードです。
# 役割が分かりやすいように、読み手向けの説明コメントを付与しています。
# 変更時は、既存仕様との整合性とテスト結果を必ず確認してください。

class Point:
    def __init__(self, x: int, y: int) -> None:
        self.x = x
        self.y: int = y

    def total(self) -> int:
        return self.x + self.y


if __name__ == "__main__":
    p: Point = Point(2, 5)
    print(p.total())
"#;
    std::process::exit(py_runtime::run_embedded_python(source));
}
