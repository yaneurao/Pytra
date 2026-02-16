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
const pytraEmbeddedSourceBase64 = "IyAwMzog44K444Ol44Oq44Ki6ZuG5ZCI44KSIFBORyDlvaLlvI/jgaflh7rlipvjgZnjgovjgrXjg7Pjg5fjg6vjgafjgZnjgIIKIyDjg4jjg6njg7Pjgrnjg5HjgqTjg6vkupLmj5vjgpLmhI/orZjjgZfjgIHljZjntJTjgarjg6vjg7zjg5fkuK3lv4Pjgaflrp/oo4XjgZfjgabjgYTjgb7jgZnjgIIKCmZyb20gdGltZSBpbXBvcnQgcGVyZl9jb3VudGVyCmZyb20gcHlfbW9kdWxlIGltcG9ydCBwbmdfaGVscGVyCgoKZGVmIHJlbmRlcl9qdWxpYSh3aWR0aDogaW50LCBoZWlnaHQ6IGludCwgbWF4X2l0ZXI6IGludCwgY3g6IGZsb2F0LCBjeTogZmxvYXQpIC0+IGJ5dGVhcnJheToKICAgIHBpeGVsczogYnl0ZWFycmF5ID0gYnl0ZWFycmF5KCkKCiAgICBmb3IgeSBpbiByYW5nZShoZWlnaHQpOgogICAgICAgIHp5MDogZmxvYXQgPSAtMS4yICsgMi40ICogKHkgLyAoaGVpZ2h0IC0gMSkpCgogICAgICAgIGZvciB4IGluIHJhbmdlKHdpZHRoKToKICAgICAgICAgICAgeng6IGZsb2F0ID0gLTEuOCArIDMuNiAqICh4IC8gKHdpZHRoIC0gMSkpCiAgICAgICAgICAgIHp5OiBmbG9hdCA9IHp5MAoKICAgICAgICAgICAgaTogaW50ID0gMAogICAgICAgICAgICB3aGlsZSBpIDwgbWF4X2l0ZXI6CiAgICAgICAgICAgICAgICB6eDI6IGZsb2F0ID0genggKiB6eAogICAgICAgICAgICAgICAgenkyOiBmbG9hdCA9IHp5ICogenkKICAgICAgICAgICAgICAgIGlmIHp4MiArIHp5MiA+IDQuMDoKICAgICAgICAgICAgICAgICAgICBicmVhawogICAgICAgICAgICAgICAgenkgPSAyLjAgKiB6eCAqIHp5ICsgY3kKICAgICAgICAgICAgICAgIHp4ID0gengyIC0genkyICsgY3gKICAgICAgICAgICAgICAgIGkgKz0gMQoKICAgICAgICAgICAgcjogaW50ID0gMAogICAgICAgICAgICBnOiBpbnQgPSAwCiAgICAgICAgICAgIGI6IGludCA9IDAKICAgICAgICAgICAgaWYgaSA+PSBtYXhfaXRlcjoKICAgICAgICAgICAgICAgIHIgPSAwCiAgICAgICAgICAgICAgICBnID0gMAogICAgICAgICAgICAgICAgYiA9IDAKICAgICAgICAgICAgZWxzZToKICAgICAgICAgICAgICAgIHQ6IGZsb2F0ID0gaSAvIG1heF9pdGVyCiAgICAgICAgICAgICAgICByID0gaW50KDI1NS4wICogKDAuMiArIDAuOCAqIHQpKQogICAgICAgICAgICAgICAgZyA9IGludCgyNTUuMCAqICgwLjEgKyAwLjkgKiAodCAqIHQpKSkKICAgICAgICAgICAgICAgIGIgPSBpbnQoMjU1LjAgKiAoMS4wIC0gdCkpCgogICAgICAgICAgICBwaXhlbHMuYXBwZW5kKHIpCiAgICAgICAgICAgIHBpeGVscy5hcHBlbmQoZykKICAgICAgICAgICAgcGl4ZWxzLmFwcGVuZChiKQoKICAgIHJldHVybiBwaXhlbHMKCgpkZWYgcnVuX2p1bGlhKCkgLT4gTm9uZToKICAgIHdpZHRoOiBpbnQgPSAzODQwCiAgICBoZWlnaHQ6IGludCA9IDIxNjAKICAgIG1heF9pdGVyOiBpbnQgPSAyMDAwMAogICAgb3V0X3BhdGg6IHN0ciA9ICJzYW1wbGUvb3V0L2p1bGlhXzAzLnBuZyIKCiAgICBzdGFydDogZmxvYXQgPSBwZXJmX2NvdW50ZXIoKQogICAgcGl4ZWxzOiBieXRlYXJyYXkgPSByZW5kZXJfanVsaWEod2lkdGgsIGhlaWdodCwgbWF4X2l0ZXIsIC0wLjgsIDAuMTU2KQogICAgcG5nX2hlbHBlci53cml0ZV9yZ2JfcG5nKG91dF9wYXRoLCB3aWR0aCwgaGVpZ2h0LCBwaXhlbHMpCiAgICBlbGFwc2VkOiBmbG9hdCA9IHBlcmZfY291bnRlcigpIC0gc3RhcnQKCiAgICBwcmludCgib3V0cHV0OiIsIG91dF9wYXRoKQogICAgcHJpbnQoInNpemU6Iiwgd2lkdGgsICJ4IiwgaGVpZ2h0KQogICAgcHJpbnQoIm1heF9pdGVyOiIsIG1heF9pdGVyKQogICAgcHJpbnQoImVsYXBzZWRfc2VjOiIsIGVsYXBzZWQpCgoKaWYgX19uYW1lX18gPT0gIl9fbWFpbl9fIjoKICAgIHJ1bl9qdWxpYSgpCg=="

// main は埋め込み Python を実行するエントリポイント。
func main() {
	os.Exit(pytraRunEmbeddedPython(pytraEmbeddedSourceBase64, os.Args[1:]))
}
