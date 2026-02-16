// fallback: class is not supported in native Rust mode
// このファイルは自動生成です。編集しないでください。
// 入力 Python: case27_class_instance.py

use std::env;
use std::process::Command;

fn run_with(interpreter: &str, source: &str) -> Option<i32> {
    let mut cmd = Command::new(interpreter);
    cmd.arg("-c").arg(source);

    // sample/py が `from py_module ...` を使うため `PYTHONPATH=src` を付与する。
    let py_path = match env::var("PYTHONPATH") {
        Ok(v) if !v.is_empty() => format!("src:{}", v),
        _ => "src".to_string(),
    };
    cmd.env("PYTHONPATH", py_path);

    // 親プロセスの標準入出力をそのまま使う。
    let status = cmd.status().ok()?;
    Some(status.code().unwrap_or(1))
}

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

    // python3 を優先し、無ければ python を試す。
    if let Some(code) = run_with("python3", source) {
        std::process::exit(code);
    }
    if let Some(code) = run_with("python", source) {
        std::process::exit(code);
    }

    eprintln!("error: python interpreter not found (python3/python)");
    std::process::exit(1);
}
