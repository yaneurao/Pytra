<?php
// AUTO-GENERATED FILE. DO NOT EDIT.
// source: src/pytra/utils/gif.py
// generated-by: tools/gen_runtime_from_manifest.py

declare(strict_types=1);

$__pytra_runtime_candidates = [
    dirname(__DIR__) . '/py_runtime.php',
    dirname(__DIR__, 2) . '/native/built_in/py_runtime.php',
];
foreach ($__pytra_runtime_candidates as $__pytra_runtime_path) {
    if (is_file($__pytra_runtime_path)) {
        require_once $__pytra_runtime_path;
        break;
    }
}
if (!function_exists('__pytra_len')) {
    throw new RuntimeException('py_runtime.php not found for generated PHP runtime lane');
}

function _gif_append_list(&$dst, $src) {
    $i = 0;
    $n = __pytra_len($src);
    while (($i < $n)) {
        $dst[] = $src[__pytra_index($src, $i)];
        $i += 1;
    }
}

function _gif_u16le($v) {
    return [($v & 255), (($v >> 8) & 255)];
}

function _lzw_encode($data, $min_code_size) {
    if ((__pytra_len($data) == 0)) {
        $empty_ = [];
        return bytes($empty_);
    }
    $clear_code = (1 << $min_code_size);
    $end_code = ($clear_code + 1);
    $code_size = ($min_code_size + 1);
    $out = [];
    $bit_buffer = 0;
    $bit_count = 0;
    $bit_buffer |= ($clear_code << $bit_count);
    $bit_count += $code_size;
    while (($bit_count >= 8)) {
        $out[] = ($bit_buffer & 255);
        $bit_buffer = ($bit_buffer >> 8);
        $bit_count -= 8;
    }
    $code_size = ($min_code_size + 1);
    foreach ($data as $v) {
        $bit_buffer |= ($v << $bit_count);
        $bit_count += $code_size;
        while (($bit_count >= 8)) {
            $out[] = ($bit_buffer & 255);
            $bit_buffer = ($bit_buffer >> 8);
            $bit_count -= 8;
        }
        $bit_buffer |= ($clear_code << $bit_count);
        $bit_count += $code_size;
        while (($bit_count >= 8)) {
            $out[] = ($bit_buffer & 255);
            $bit_buffer = ($bit_buffer >> 8);
            $bit_count -= 8;
        }
        $code_size = ($min_code_size + 1);
    }
    $bit_buffer |= ($end_code << $bit_count);
    $bit_count += $code_size;
    while (($bit_count >= 8)) {
        $out[] = ($bit_buffer & 255);
        $bit_buffer = ($bit_buffer >> 8);
        $bit_count -= 8;
    }
    if (($bit_count > 0)) {
        $out[] = ($bit_buffer & 255);
    }
    return bytes($out);
}

function grayscale_palette() {
    $p = [];
    $i = 0;
    while (($i < 256)) {
        $p[] = $i;
        $p[] = $i;
        $p[] = $i;
        $i += 1;
    }
    return bytes($p);
}

function save_gif($path, $width, $height, $frames, $palette, $delay_cs, $loop) {
    if ((__pytra_len($palette) != (256 * 3))) {
        throw new Exception(strval(ValueError("palette must be 256*3 bytes")));
    }
    $frame_lists = [];
    foreach ($frames as $fr) {
        $fr_list = [];
        foreach ($fr as $v) {
            $fr_list[] = ((int)($v));
        }
        if ((__pytra_len($fr_list) != ($width * $height))) {
            throw new Exception(strval(ValueError("frame size mismatch")));
        }
        $frame_lists[] = $fr_list;
    }
    $palette_list = [];
    foreach ($palette as $v) {
        $palette_list[] = ((int)($v));
    }
    $out = [];
    _gif_append_list($out, [71, 73, 70, 56, 57, 97]);
    _gif_append_list($out, _gif_u16le($width));
    _gif_append_list($out, _gif_u16le($height));
    $out[] = 247;
    $out[] = 0;
    $out[] = 0;
    _gif_append_list($out, $palette_list);
    _gif_append_list($out, [33, 255, 11, 78, 69, 84, 83, 67, 65, 80, 69, 50, 46, 48, 3, 1]);
    _gif_append_list($out, _gif_u16le($loop));
    $out[] = 0;
    foreach ($frame_lists as $fr_list) {
        _gif_append_list($out, [33, 249, 4, 0]);
        _gif_append_list($out, _gif_u16le($delay_cs));
        _gif_append_list($out, [0, 0]);
        $out[] = 44;
        _gif_append_list($out, _gif_u16le(0));
        _gif_append_list($out, _gif_u16le(0));
        _gif_append_list($out, _gif_u16le($width));
        _gif_append_list($out, _gif_u16le($height));
        $out[] = 0;
        $out[] = 8;
        $compressed = _lzw_encode(bytes($fr_list), 8);
        $pos = 0;
        while (($pos < __pytra_len($compressed))) {
            $remain = (__pytra_len($compressed) - $pos);
            $chunk_len = (($remain > 255) ? 255 : $remain);
            $out[] = $chunk_len;
            $i = 0;
            while (($i < $chunk_len)) {
                $out[] = $compressed[__pytra_index($compressed, ($pos + $i))];
                $i += 1;
            }
            $pos += $chunk_len;
        }
        $out[] = 0;
    }
    $out[] = 59;
    $f = open($path, "wb");
    $f->write(bytes($out));
    $f->close();
}
