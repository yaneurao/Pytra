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
const pytraEmbeddedSourceBase64 = "IyAxNDog57Ch5piT44Os44Kk44Oe44O844OB6aKo44Gu5YWJ5rqQ56e75YuV44K344O844Oz44KSR0lG5Ye65Yqb44GZ44KL44K144Oz44OX44Or44CCCgpmcm9tIF9fZnV0dXJlX18gaW1wb3J0IGFubm90YXRpb25zCgppbXBvcnQgbWF0aApmcm9tIHRpbWUgaW1wb3J0IHBlcmZfY291bnRlcgoKZnJvbSBweV9tb2R1bGUuZ2lmX2hlbHBlciBpbXBvcnQgc2F2ZV9naWYKCgpkZWYgcGFsZXR0ZSgpIC0+IGJ5dGVzOgogICAgcCA9IGJ5dGVhcnJheSgpCiAgICBmb3IgaSBpbiByYW5nZSgyNTYpOgogICAgICAgIHIgPSBpbnQoMjAgKyBpICogMC45KQogICAgICAgIGlmIHIgPiAyNTU6CiAgICAgICAgICAgIHIgPSAyNTUKICAgICAgICBnID0gaW50KDEwICsgaSAqIDAuNykKICAgICAgICBpZiBnID4gMjU1OgogICAgICAgICAgICBnID0gMjU1CiAgICAgICAgYiA9IGludCgzMCArIGkpCiAgICAgICAgaWYgYiA+IDI1NToKICAgICAgICAgICAgYiA9IDI1NQogICAgICAgIHAuYXBwZW5kKHIpCiAgICAgICAgcC5hcHBlbmQoZykKICAgICAgICBwLmFwcGVuZChiKQogICAgcmV0dXJuIGJ5dGVzKHApCgoKZGVmIHNjZW5lKHg6IGZsb2F0LCB5OiBmbG9hdCwgbGlnaHRfeDogZmxvYXQsIGxpZ2h0X3k6IGZsb2F0KSAtPiBpbnQ6CiAgICB4MSA9IHggKyAwLjQ1CiAgICB5MSA9IHkgKyAwLjIKICAgIHgyID0geCAtIDAuMzUKICAgIHkyID0geSAtIDAuMTUKICAgIHIxID0gbWF0aC5zcXJ0KHgxICogeDEgKyB5MSAqIHkxKQogICAgcjIgPSBtYXRoLnNxcnQoeDIgKiB4MiArIHkyICogeTIpCiAgICBibG9iID0gbWF0aC5leHAoLTcuMCAqIHIxICogcjEpICsgbWF0aC5leHAoLTguMCAqIHIyICogcjIpCgogICAgbHggPSB4IC0gbGlnaHRfeAogICAgbHkgPSB5IC0gbGlnaHRfeQogICAgbCA9IG1hdGguc3FydChseCAqIGx4ICsgbHkgKiBseSkKICAgIGxpdCA9IDEuMCAvICgxLjAgKyAzLjUgKiBsICogbCkKCiAgICB2ID0gaW50KDI1NS4wICogYmxvYiAqIGxpdCAqIDUuMCkKICAgIGlmIHYgPCAwOgogICAgICAgIHJldHVybiAwCiAgICBpZiB2ID4gMjU1OgogICAgICAgIHJldHVybiAyNTUKICAgIHJldHVybiB2CgoKZGVmIHJ1bl8xNF9yYXltYXJjaGluZ19saWdodF9jeWNsZSgpIC0+IE5vbmU6CiAgICB3ID0gMzIwCiAgICBoID0gMjQwCiAgICBmcmFtZXNfbiA9IDg0CiAgICBvdXRfcGF0aCA9ICJzYW1wbGUvb3V0LzE0X3JheW1hcmNoaW5nX2xpZ2h0X2N5Y2xlLmdpZiIKCiAgICBzdGFydCA9IHBlcmZfY291bnRlcigpCiAgICBmcmFtZXM6IGxpc3RbYnl0ZXNdID0gW10KCiAgICBmb3IgdCBpbiByYW5nZShmcmFtZXNfbik6CiAgICAgICAgZnJhbWUgPSBieXRlYXJyYXkodyAqIGgpCiAgICAgICAgYSA9ICh0IC8gZnJhbWVzX24pICogbWF0aC5waSAqIDIuMAogICAgICAgIGxpZ2h0X3ggPSAwLjc1ICogbWF0aC5jb3MoYSkKICAgICAgICBsaWdodF95ID0gMC41NSAqIG1hdGguc2luKGEgKiAxLjIpCgogICAgICAgIGkgPSAwCiAgICAgICAgZm9yIHkgaW4gcmFuZ2UoaCk6CiAgICAgICAgICAgIHB5ID0gKHkgLyAoaCAtIDEpKSAqIDIuMCAtIDEuMAogICAgICAgICAgICBmb3IgeCBpbiByYW5nZSh3KToKICAgICAgICAgICAgICAgIHB4ID0gKHggLyAodyAtIDEpKSAqIDIuMCAtIDEuMAogICAgICAgICAgICAgICAgZnJhbWVbaV0gPSBzY2VuZShweCwgcHksIGxpZ2h0X3gsIGxpZ2h0X3kpCiAgICAgICAgICAgICAgICBpICs9IDEKCiAgICAgICAgZnJhbWVzLmFwcGVuZChieXRlcyhmcmFtZSkpCgogICAgc2F2ZV9naWYob3V0X3BhdGgsIHcsIGgsIGZyYW1lcywgcGFsZXR0ZSgpLCBkZWxheV9jcz0zLCBsb29wPTApCiAgICBlbGFwc2VkID0gcGVyZl9jb3VudGVyKCkgLSBzdGFydAogICAgcHJpbnQoIm91dHB1dDoiLCBvdXRfcGF0aCkKICAgIHByaW50KCJmcmFtZXM6IiwgZnJhbWVzX24pCiAgICBwcmludCgiZWxhcHNlZF9zZWM6IiwgZWxhcHNlZCkKCgppZiBfX25hbWVfXyA9PSAiX19tYWluX18iOgogICAgcnVuXzE0X3JheW1hcmNoaW5nX2xpZ2h0X2N5Y2xlKCkK"

// main は埋め込み Python を実行するエントリポイント。
func main() {
	os.Exit(pytraRunEmbeddedPython(pytraEmbeddedSourceBase64, os.Args[1:]))
}
