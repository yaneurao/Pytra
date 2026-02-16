// このファイルは自動生成です（Python -> Go embedded mode）。

// Python 埋め込み実行向けの Go ランタイム補助。
// 生成された Go コードから呼び出し、Python ソースを一時ファイルに展開して実行する。

package main

import (
	"encoding/base64"
	"fmt"
	"os"
	"os/exec"
	"path/filepath"
)

// pytraRunEmbeddedPython は、Base64 で埋め込まれた Python ソースを実行する。
//
// Args:
//   sourceBase64: 埋め込み Python ソースコード（Base64 文字列）。
//   args: Python スクリプトへ渡す引数。
//
// Returns:
//   Python プロセスの終了コード。異常時は 1 を返す。
func pytraRunEmbeddedPython(sourceBase64 string, args []string) int {
	sourceBytes, decodeErr := base64.StdEncoding.DecodeString(sourceBase64)
	if decodeErr != nil {
		fmt.Fprintln(os.Stderr, "error: failed to decode embedded python source")
		return 1
	}

	tempDir, mkErr := os.MkdirTemp("", "pytra_go_")
	if mkErr != nil {
		fmt.Fprintln(os.Stderr, "error: failed to create temp directory")
		return 1
	}
	defer os.RemoveAll(tempDir)

	scriptPath := filepath.Join(tempDir, "embedded.py")
	if writeErr := os.WriteFile(scriptPath, sourceBytes, 0o600); writeErr != nil {
		fmt.Fprintln(os.Stderr, "error: failed to write temp python script")
		return 1
	}

	pythonPath := "src"
	if current, ok := os.LookupEnv("PYTHONPATH"); ok && current != "" {
		pythonPath = pythonPath + string(os.PathListSeparator) + current
	}

	run := func(interpreter string) (int, error) {
		cmd := exec.Command(interpreter, append([]string{scriptPath}, args...)...)
		cmd.Stdout = os.Stdout
		cmd.Stderr = os.Stderr
		cmd.Stdin = os.Stdin
		env := os.Environ()
		env = append(env, "PYTHONPATH="+pythonPath)
		cmd.Env = env
		err := cmd.Run()
		if err == nil {
			return 0, nil
		}
		if exitErr, ok := err.(*exec.ExitError); ok {
			return exitErr.ExitCode(), nil
		}
		return 0, err
	}

	if code, err := run("python3"); err == nil {
		return code
	}
	if code, err := run("python"); err == nil {
		return code
	}

	fmt.Fprintln(os.Stderr, "error: python interpreter not found (python3/python)")
	return 1
}

// 埋め込み Python ソース（Base64）。
const pytraEmbeddedSourceBase64 = "IyDjgZPjga7jg5XjgqHjgqTjg6vjga8gYHRlc3QvcHkvY2FzZTE0X2luaGVyaXRhbmNlLnB5YCDjga7jg4bjgrnjg4gv5a6f6KOF44Kz44O844OJ44Gn44GZ44CCCiMg5b255Ymy44GM5YiG44GL44KK44KE44GZ44GE44KI44GG44Gr44CB6Kqt44G/5omL5ZCR44GR44Gu6Kqs5piO44Kz44Oh44Oz44OI44KS5LuY5LiO44GX44Gm44GE44G+44GZ44CCCiMg5aSJ5pu05pmC44Gv44CB5pei5a2Y5LuV5qeY44Go44Gu5pW05ZCI5oCn44Go44OG44K544OI57WQ5p6c44KS5b+F44Ga56K66KqN44GX44Gm44GP44Gg44GV44GE44CCCgpjbGFzcyBBbmltYWw6CiAgICBkZWYgc291bmQoc2VsZikgLT4gc3RyOgogICAgICAgIHJldHVybiAiZ2VuZXJpYyIKCgpjbGFzcyBEb2coQW5pbWFsKToKICAgIGRlZiBiYXJrKHNlbGYpIC0+IHN0cjoKICAgICAgICByZXR1cm4gc2VsZi5zb3VuZCgpICsgIi1iYXJrIgoKCmlmIF9fbmFtZV9fID09ICJfX21haW5fXyI6CiAgICBkOiBEb2cgPSBEb2coKQogICAgcHJpbnQoZC5iYXJrKCkpCg=="

// main は埋め込み Python を実行するエントリポイント。
func main() {
	os.Exit(pytraRunEmbeddedPython(pytraEmbeddedSourceBase64, os.Args[1:]))
}
