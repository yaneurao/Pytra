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
const pytraEmbeddedSourceBase64 = "IyAxMDog44Oi44Oz44OG44Kr44Or44Ot5rOV44Gn5YaG5ZGo546H44KS5o6o5a6a44GZ44KL44K144Oz44OX44Or44Gn44GZ44CCCiMgaW1wb3J0IHJhbmRvbSDjgpLkvb/jgo/jgZrjgIFMQ0cg44KS6Ieq5YmN5a6f6KOF44GX44Gm44OI44Op44Oz44K544OR44Kk44Or5LqS5o+b5oCn44KS6auY44KB44Gm44GE44G+44GZ44CCCgpmcm9tIHRpbWUgaW1wb3J0IHBlcmZfY291bnRlcgoKCmRlZiBsY2dfbmV4dChzdGF0ZTogaW50KSAtPiBpbnQ6CiAgICAjIDMyYml0IExDRwogICAgcmV0dXJuICgxNjY0NTI1ICogc3RhdGUgKyAxMDEzOTA0MjIzKSAlIDQyOTQ5NjcyOTYKCgpkZWYgcnVuX3BpX3RyaWFsKHRvdGFsX3NhbXBsZXM6IGludCwgc2VlZDogaW50KSAtPiBmbG9hdDoKICAgIGluc2lkZTogaW50ID0gMAogICAgc3RhdGU6IGludCA9IHNlZWQKCiAgICBmb3IgXyBpbiByYW5nZSh0b3RhbF9zYW1wbGVzKToKICAgICAgICBzdGF0ZSA9IGxjZ19uZXh0KHN0YXRlKQogICAgICAgIHg6IGZsb2F0ID0gc3RhdGUgLyA0Mjk0OTY3Mjk2LjAKCiAgICAgICAgc3RhdGUgPSBsY2dfbmV4dChzdGF0ZSkKICAgICAgICB5OiBmbG9hdCA9IHN0YXRlIC8gNDI5NDk2NzI5Ni4wCgogICAgICAgIGR4OiBmbG9hdCA9IHggLSAwLjUKICAgICAgICBkeTogZmxvYXQgPSB5IC0gMC41CiAgICAgICAgaWYgZHggKiBkeCArIGR5ICogZHkgPD0gMC4yNToKICAgICAgICAgICAgaW5zaWRlICs9IDEKCiAgICByZXR1cm4gNC4wICogaW5zaWRlIC8gdG90YWxfc2FtcGxlcwoKCmRlZiBydW5fbW9udGVfY2FybG9fcGkoKSAtPiBOb25lOgogICAgc2FtcGxlczogaW50ID0gNTQwMDAwMDAKICAgIHNlZWQ6IGludCA9IDEyMzQ1Njc4OQoKICAgIHN0YXJ0OiBmbG9hdCA9IHBlcmZfY291bnRlcigpCiAgICBwaV9lc3Q6IGZsb2F0ID0gcnVuX3BpX3RyaWFsKHNhbXBsZXMsIHNlZWQpCiAgICBlbGFwc2VkOiBmbG9hdCA9IHBlcmZfY291bnRlcigpIC0gc3RhcnQKCiAgICBwcmludCgic2FtcGxlczoiLCBzYW1wbGVzKQogICAgcHJpbnQoInBpX2VzdGltYXRlOiIsIHBpX2VzdCkKICAgIHByaW50KCJlbGFwc2VkX3NlYzoiLCBlbGFwc2VkKQoKCmlmIF9fbmFtZV9fID09ICJfX21haW5fXyI6CiAgICBydW5fbW9udGVfY2FybG9fcGkoKQo="

// main は埋め込み Python を実行するエントリポイント。
func main() {
	os.Exit(pytraRunEmbeddedPython(pytraEmbeddedSourceBase64, os.Args[1:]))
}
