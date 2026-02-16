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
const pytraEmbeddedSourceBase64 = "IyAxMTog44Oq44K144O844K444Ol6YGL5YuV44GZ44KL57KS5a2Q44KSR0lG5Ye65Yqb44GZ44KL44K144Oz44OX44Or44CCCgpmcm9tIF9fZnV0dXJlX18gaW1wb3J0IGFubm90YXRpb25zCgppbXBvcnQgbWF0aApmcm9tIHRpbWUgaW1wb3J0IHBlcmZfY291bnRlcgoKZnJvbSBweV9tb2R1bGUuZ2lmX2hlbHBlciBpbXBvcnQgc2F2ZV9naWYKCgpkZWYgY29sb3JfcGFsZXR0ZSgpIC0+IGJ5dGVzOgogICAgcCA9IGJ5dGVhcnJheSgpCiAgICBmb3IgaSBpbiByYW5nZSgyNTYpOgogICAgICAgIHIgPSBpCiAgICAgICAgZyA9IChpICogMykgJSAyNTYKICAgICAgICBiID0gMjU1IC0gaQogICAgICAgIHAuYXBwZW5kKHIpCiAgICAgICAgcC5hcHBlbmQoZykKICAgICAgICBwLmFwcGVuZChiKQogICAgcmV0dXJuIGJ5dGVzKHApCgoKZGVmIHJ1bl8xMV9saXNzYWpvdXNfcGFydGljbGVzKCkgLT4gTm9uZToKICAgIHcgPSAzMjAKICAgIGggPSAyNDAKICAgIGZyYW1lc19uID0gMzYwCiAgICBwYXJ0aWNsZXMgPSA0OAogICAgb3V0X3BhdGggPSAic2FtcGxlL291dC8xMV9saXNzYWpvdXNfcGFydGljbGVzLmdpZiIKCiAgICBzdGFydCA9IHBlcmZfY291bnRlcigpCiAgICBmcmFtZXM6IGxpc3RbYnl0ZXNdID0gW10KCiAgICBmb3IgdCBpbiByYW5nZShmcmFtZXNfbik6CiAgICAgICAgZnJhbWUgPSBieXRlYXJyYXkodyAqIGgpCgogICAgICAgIGZvciBwIGluIHJhbmdlKHBhcnRpY2xlcyk6CiAgICAgICAgICAgIHBoYXNlID0gcCAqIDAuMjYxNzk5CiAgICAgICAgICAgIHggPSBpbnQoKHcgKiAwLjUpICsgKHcgKiAwLjM4KSAqIG1hdGguc2luKDAuMTEgKiB0ICsgcGhhc2UgKiAyLjApKQogICAgICAgICAgICB5ID0gaW50KChoICogMC41KSArIChoICogMC4zOCkgKiBtYXRoLnNpbigwLjE3ICogdCArIHBoYXNlICogMy4wKSkKICAgICAgICAgICAgY29sb3IgPSAzMCArIChwICogOSkgJSAyMjAKCiAgICAgICAgICAgIGZvciBkeSBpbiByYW5nZSgtMiwgMyk6CiAgICAgICAgICAgICAgICBmb3IgZHggaW4gcmFuZ2UoLTIsIDMpOgogICAgICAgICAgICAgICAgICAgIHh4ID0geCArIGR4CiAgICAgICAgICAgICAgICAgICAgeXkgPSB5ICsgZHkKICAgICAgICAgICAgICAgICAgICBpZiB4eCA+PSAwIGFuZCB4eCA8IHcgYW5kIHl5ID49IDAgYW5kIHl5IDwgaDoKICAgICAgICAgICAgICAgICAgICAgICAgZDIgPSBkeCAqIGR4ICsgZHkgKiBkeQogICAgICAgICAgICAgICAgICAgICAgICBpZiBkMiA8PSA0OgogICAgICAgICAgICAgICAgICAgICAgICAgICAgaWR4ID0geXkgKiB3ICsgeHgKICAgICAgICAgICAgICAgICAgICAgICAgICAgIHYgPSBjb2xvciAtIGQyICogMjAKICAgICAgICAgICAgICAgICAgICAgICAgICAgIGlmIHYgPCAwOgogICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgIHYgPSAwCiAgICAgICAgICAgICAgICAgICAgICAgICAgICBpZiB2ID4gZnJhbWVbaWR4XToKICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICBmcmFtZVtpZHhdID0gdgoKICAgICAgICBmcmFtZXMuYXBwZW5kKGJ5dGVzKGZyYW1lKSkKCiAgICBzYXZlX2dpZihvdXRfcGF0aCwgdywgaCwgZnJhbWVzLCBjb2xvcl9wYWxldHRlKCksIGRlbGF5X2NzPTMsIGxvb3A9MCkKICAgIGVsYXBzZWQgPSBwZXJmX2NvdW50ZXIoKSAtIHN0YXJ0CiAgICBwcmludCgib3V0cHV0OiIsIG91dF9wYXRoKQogICAgcHJpbnQoImZyYW1lczoiLCBmcmFtZXNfbikKICAgIHByaW50KCJlbGFwc2VkX3NlYzoiLCBlbGFwc2VkKQoKCmlmIF9fbmFtZV9fID09ICJfX21haW5fXyI6CiAgICBydW5fMTFfbGlzc2Fqb3VzX3BhcnRpY2xlcygpCg=="

// main は埋め込み Python を実行するエントリポイント。
func main() {
	os.Exit(pytraRunEmbeddedPython(pytraEmbeddedSourceBase64, os.Args[1:]))
}
