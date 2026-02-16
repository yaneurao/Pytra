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
const pytraEmbeddedSourceBase64 = "IyAwNjog44K444Ol44Oq44Ki6ZuG5ZCI44Gu44OR44Op44Oh44O844K/44KS5Zue44GX44GmR0lG5Ye65Yqb44GZ44KL44K144Oz44OX44Or44CCCgpmcm9tIF9fZnV0dXJlX18gaW1wb3J0IGFubm90YXRpb25zCgppbXBvcnQgbWF0aApmcm9tIHRpbWUgaW1wb3J0IHBlcmZfY291bnRlcgoKZnJvbSBweV9tb2R1bGUuZ2lmX2hlbHBlciBpbXBvcnQgc2F2ZV9naWYKCgpkZWYganVsaWFfcGFsZXR0ZSgpIC0+IGJ5dGVzOgogICAgIyDlhYjpoK3oibLjga/pm4blkIjlhoXpg6jnlKjjgavpu5Llm7rlrprjgIHmrovjgorjga/pq5jlvanluqbjgrDjg6njg4fjg7zjgrfjg6fjg7PjgpLkvZzjgovjgIIKICAgIHBhbGV0dGUgPSBieXRlYXJyYXkoMjU2ICogMykKICAgIHBhbGV0dGVbMF0gPSAwCiAgICBwYWxldHRlWzFdID0gMAogICAgcGFsZXR0ZVsyXSA9IDAKICAgIGZvciBpIGluIHJhbmdlKDEsIDI1Nik6CiAgICAgICAgdCA9IChpIC0gMSkgLyAyNTQuMAogICAgICAgIHIgPSBpbnQoMjU1LjAgKiAoOS4wICogKDEuMCAtIHQpICogdCAqIHQgKiB0KSkKICAgICAgICBnID0gaW50KDI1NS4wICogKDE1LjAgKiAoMS4wIC0gdCkgKiAoMS4wIC0gdCkgKiB0ICogdCkpCiAgICAgICAgYiA9IGludCgyNTUuMCAqICg4LjUgKiAoMS4wIC0gdCkgKiAoMS4wIC0gdCkgKiAoMS4wIC0gdCkgKiB0KSkKICAgICAgICBwYWxldHRlW2kgKiAzICsgMF0gPSByCiAgICAgICAgcGFsZXR0ZVtpICogMyArIDFdID0gZwogICAgICAgIHBhbGV0dGVbaSAqIDMgKyAyXSA9IGIKICAgIHJldHVybiBieXRlcyhwYWxldHRlKQoKCmRlZiByZW5kZXJfZnJhbWUod2lkdGg6IGludCwgaGVpZ2h0OiBpbnQsIGNyOiBmbG9hdCwgY2k6IGZsb2F0LCBtYXhfaXRlcjogaW50LCBwaGFzZTogaW50KSAtPiBieXRlczoKICAgIGZyYW1lID0gYnl0ZWFycmF5KHdpZHRoICogaGVpZ2h0KQogICAgaWR4ID0gMAogICAgZm9yIHkgaW4gcmFuZ2UoaGVpZ2h0KToKICAgICAgICB6eTAgPSAtMS4yICsgMi40ICogKHkgLyAoaGVpZ2h0IC0gMSkpCiAgICAgICAgZm9yIHggaW4gcmFuZ2Uod2lkdGgpOgogICAgICAgICAgICB6eCA9IC0xLjggKyAzLjYgKiAoeCAvICh3aWR0aCAtIDEpKQogICAgICAgICAgICB6eSA9IHp5MAogICAgICAgICAgICBpID0gMAogICAgICAgICAgICB3aGlsZSBpIDwgbWF4X2l0ZXI6CiAgICAgICAgICAgICAgICB6eDIgPSB6eCAqIHp4CiAgICAgICAgICAgICAgICB6eTIgPSB6eSAqIHp5CiAgICAgICAgICAgICAgICBpZiB6eDIgKyB6eTIgPiA0LjA6CiAgICAgICAgICAgICAgICAgICAgYnJlYWsKICAgICAgICAgICAgICAgIHp5ID0gMi4wICogenggKiB6eSArIGNpCiAgICAgICAgICAgICAgICB6eCA9IHp4MiAtIHp5MiArIGNyCiAgICAgICAgICAgICAgICBpICs9IDEKICAgICAgICAgICAgaWYgaSA+PSBtYXhfaXRlcjoKICAgICAgICAgICAgICAgIGZyYW1lW2lkeF0gPSAwCiAgICAgICAgICAgIGVsc2U6CiAgICAgICAgICAgICAgICAjIOODleODrOODvOODoOS9jeebuOOCkuWwkeOBl+WKoOOBiOOBpuiJsuOBjOa7keOCieOBi+OBq+a1geOCjOOCi+OCiOOBhuOBq+OBmeOCi+OAggogICAgICAgICAgICAgICAgY29sb3JfaW5kZXggPSAxICsgKCgoaSAqIDIyNCkgLy8gbWF4X2l0ZXIgKyBwaGFzZSkgJSAyNTUpCiAgICAgICAgICAgICAgICBmcmFtZVtpZHhdID0gY29sb3JfaW5kZXgKICAgICAgICAgICAgaWR4ICs9IDEKICAgIHJldHVybiBieXRlcyhmcmFtZSkKCgpkZWYgcnVuXzA2X2p1bGlhX3BhcmFtZXRlcl9zd2VlcCgpIC0+IE5vbmU6CiAgICB3aWR0aCA9IDMyMAogICAgaGVpZ2h0ID0gMjQwCiAgICBmcmFtZXNfbiA9IDcyCiAgICBtYXhfaXRlciA9IDE4MAogICAgb3V0X3BhdGggPSAic2FtcGxlL291dC8wNl9qdWxpYV9wYXJhbWV0ZXJfc3dlZXAuZ2lmIgoKICAgIHN0YXJ0ID0gcGVyZl9jb3VudGVyKCkKICAgIGZyYW1lczogbGlzdFtieXRlc10gPSBbXQogICAgIyDml6Lnn6Xjga7opovmoITjgYjjgYzoia/jgYTov5Hlgo3jgpLmpZXlhobou4zpgZPjgaflt6Hlm57jgZfjgIHljZjoqr/jgarnmb3po5vjgbPjgpLmipHjgYjjgovjgIIKICAgIGNlbnRlcl9jciA9IC0wLjc0NQogICAgY2VudGVyX2NpID0gMC4xODYKICAgIHJhZGl1c19jciA9IDAuMTIKICAgIHJhZGl1c19jaSA9IDAuMTAKICAgIGZvciBpIGluIHJhbmdlKGZyYW1lc19uKToKICAgICAgICB0ID0gaSAvIGZyYW1lc19uCiAgICAgICAgYW5nbGUgPSAyLjAgKiBtYXRoLnBpICogdAogICAgICAgIGNyID0gY2VudGVyX2NyICsgcmFkaXVzX2NyICogbWF0aC5jb3MoYW5nbGUpCiAgICAgICAgY2kgPSBjZW50ZXJfY2kgKyByYWRpdXNfY2kgKiBtYXRoLnNpbihhbmdsZSkKICAgICAgICBwaGFzZSA9IChpICogNSkgJSAyNTUKICAgICAgICBmcmFtZXMuYXBwZW5kKHJlbmRlcl9mcmFtZSh3aWR0aCwgaGVpZ2h0LCBjciwgY2ksIG1heF9pdGVyLCBwaGFzZSkpCgogICAgc2F2ZV9naWYob3V0X3BhdGgsIHdpZHRoLCBoZWlnaHQsIGZyYW1lcywganVsaWFfcGFsZXR0ZSgpLCBkZWxheV9jcz04LCBsb29wPTApCiAgICBlbGFwc2VkID0gcGVyZl9jb3VudGVyKCkgLSBzdGFydAogICAgcHJpbnQoIm91dHB1dDoiLCBvdXRfcGF0aCkKICAgIHByaW50KCJmcmFtZXM6IiwgZnJhbWVzX24pCiAgICBwcmludCgiZWxhcHNlZF9zZWM6IiwgZWxhcHNlZCkKCgppZiBfX25hbWVfXyA9PSAiX19tYWluX18iOgogICAgcnVuXzA2X2p1bGlhX3BhcmFtZXRlcl9zd2VlcCgpCg=="

// main は埋め込み Python を実行するエントリポイント。
func main() {
	os.Exit(pytraRunEmbeddedPython(pytraEmbeddedSourceBase64, os.Args[1:]))
}
