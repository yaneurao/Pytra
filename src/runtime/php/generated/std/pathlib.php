<?php
// AUTO-GENERATED FILE. DO NOT EDIT.
// source: src/pytra/std/pathlib.py
// generated-by: tools/gen_runtime_from_manifest.py

declare(strict_types=1);

require_once dirname(__DIR__) . '/py_runtime.php';

if (!class_exists('Path', false)) {
    class Path {
        public string $path;
        public string $name;
        public string $stem;
        public string $suffix;
        public $parent;

        public function __construct($value) {
            $this->path = (string)$value;
            $this->name = basename($this->path);
            $dot = strrpos($this->name, '.');
            $this->stem = ($dot === false || $dot === 0) ? $this->name : substr($this->name, 0, $dot);
            $this->suffix = ($dot === false || $dot === 0) ? '' : substr($this->name, $dot);
            $parentTxt = dirname($this->path);
            if ($parentTxt === '' || $parentTxt === $this->path) {
                $this->parent = null;
            } else {
                $this->parent = new Path($parentTxt);
            }
        }

        public function __toString(): string {
            return $this->path;
        }

        public function __fspath__(): string {
            return $this->path;
        }

        public function __truediv__($rhs): Path {
            $rhsText = (string)$rhs;
            if ($this->path === '') {
                return new Path($rhsText);
            }
            return new Path(rtrim($this->path, DIRECTORY_SEPARATOR) . DIRECTORY_SEPARATOR . ltrim($rhsText, DIRECTORY_SEPARATOR));
        }

        public function resolve(): Path {
            $resolved = realpath($this->path);
            if ($resolved === false) {
                $resolved = $this->path;
            }
            return new Path($resolved);
        }

        public function exists(): bool {
            return file_exists($this->path);
        }

        public function mkdir($parents = false, $exist_ok = false): void {
            if ($exist_ok && file_exists($this->path)) {
                return;
            }
            if ((bool)$parents) {
                if (@mkdir($this->path, 0777, true)) {
                    return;
                }
                if ((bool)$exist_ok && is_dir($this->path)) {
                    return;
                }
                throw new RuntimeException('mkdir failed: ' . $this->path);
            }
            if (@mkdir($this->path)) {
                return;
            }
            if ((bool)$exist_ok && is_dir($this->path)) {
                return;
            }
            throw new RuntimeException('mkdir failed: ' . $this->path);
        }

        public function write_text($text, $encoding = 'utf-8'): int {
            $bytes = file_put_contents($this->path, (string)$text);
            if ($bytes === false) {
                throw new RuntimeException('write_text failed: ' . $this->path);
            }
            return $bytes;
        }

        public function read_text($encoding = 'utf-8'): string {
            $data = file_get_contents($this->path);
            if ($data === false) {
                throw new RuntimeException('read_text failed: ' . $this->path);
            }
            return $data;
        }

        public function glob($pattern): array {
            $prefix = rtrim($this->path, DIRECTORY_SEPARATOR);
            $items = glob($prefix . DIRECTORY_SEPARATOR . (string)$pattern);
            if (!is_array($items)) {
                return [];
            }
            return array_map(fn($item) => new Path($item), $items);
        }

        public static function cwd(): Path {
            return new Path(getcwd());
        }
    }
}
