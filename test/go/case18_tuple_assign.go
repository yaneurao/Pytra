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
const pytraEmbeddedSourceBase64 = "IyDjgZPjga7jg5XjgqHjgqTjg6vjga8gYHRlc3QvcHkvY2FzZTE4X3R1cGxlX2Fzc2lnbi5weWAg44Gu44OG44K544OIL+Wun+ijheOCs+ODvOODieOBp+OBmeOAggojIOW9ueWJsuOBjOWIhuOBi+OCiuOChOOBmeOBhOOCiOOBhuOBq+OAgeiqreOBv+aJi+WQkeOBkeOBruiqrOaYjuOCs+ODoeODs+ODiOOCkuS7mOS4juOBl+OBpuOBhOOBvuOBmeOAggojIOWkieabtOaZguOBr+OAgeaXouWtmOS7leanmOOBqOOBruaVtOWQiOaAp+OBqOODhuOCueODiOe1kOaenOOCkuW/heOBmueiuuiqjeOBl+OBpuOBj+OBoOOBleOBhOOAggoKZGVmIHN3YXBfc3VtXzE4KGE6IGludCwgYjogaW50KSAtPiBpbnQ6CiAgICB4OiBpbnQgPSBhCiAgICB5OiBpbnQgPSBiCiAgICB4LCB5ID0geSwgeAogICAgcmV0dXJuIHggKyB5CgoKaWYgX19uYW1lX18gPT0gIl9fbWFpbl9fIjoKICAgIHByaW50KHN3YXBfc3VtXzE4KDEwLCAyMCkpCg=="

// main は埋め込み Python を実行するエントリポイント。
func main() {
	os.Exit(pytraRunEmbeddedPython(pytraEmbeddedSourceBase64, os.Args[1:]))
}
