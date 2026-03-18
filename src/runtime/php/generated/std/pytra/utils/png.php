<?php
// AUTO-GENERATED FILE. DO NOT EDIT.
// source: src/pytra/utils/png.py
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

function _png_append_list(&$dst, $src) {
    $i = 0;
    $n = __pytra_len($src);
    while (($i < $n)) {
        $dst[] = $src[__pytra_index($src, $i)];
        $i += 1;
    }
}

function _crc32($data) {
    $crc = 4294967295;
    $poly = 3988292384;
    foreach ($data as $b) {
        $crc = ($crc ^ $b);
        $i = 0;
        while (($i < 8)) {
            $lowbit = ($crc & 1);
            if (($lowbit != 0)) {
                $crc = (($crc >> 1) ^ $poly);
            } else {
                $crc = ($crc >> 1);
            }
            $i += 1;
        }
    }
    return ($crc ^ 4294967295);
}

function _adler32($data) {
    $mod = 65521;
    $s1 = 1;
    $s2 = 0;
    foreach ($data as $b) {
        $s1 += $b;
        if (($s1 >= $mod)) {
            $s1 -= $mod;
        }
        $s2 += $s1;
        $s2 = ($s2 % $mod);
    }
    return ((($s2 << 16) | $s1) & 4294967295);
}

function _png_u16le($v) {
    return [($v & 255), (($v >> 8) & 255)];
}

function _png_u32be($v) {
    return [(($v >> 24) & 255), (($v >> 16) & 255), (($v >> 8) & 255), ($v & 255)];
}

function _zlib_deflate_store($data) {
    $out = [];
    _png_append_list($out, [120, 1]);
    $n = __pytra_len($data);
    $pos = 0;
    while (($pos < $n)) {
        $remain = ($n - $pos);
        $chunk_len = (($remain > 65535) ? 65535 : $remain);
        $final_ = ((($pos + $chunk_len) >= $n) ? 1 : 0);
        $out[] = $final_;
        _png_append_list($out, _png_u16le($chunk_len));
        _png_append_list($out, _png_u16le((65535 ^ $chunk_len)));
        $i = $pos;
        $end = ($pos + $chunk_len);
        while (($i < $end)) {
            $out[] = $data[__pytra_index($data, $i)];
            $i += 1;
        }
        $pos += $chunk_len;
    }
    _png_append_list($out, _png_u32be(_adler32($data)));
    return $out;
}

function _chunk($chunk_type, $data) {
    $crc_input = [];
    _png_append_list($crc_input, $chunk_type);
    _png_append_list($crc_input, $data);
    $crc = (_crc32($crc_input) & 4294967295);
    $out = [];
    _png_append_list($out, _png_u32be(__pytra_len($data)));
    _png_append_list($out, $chunk_type);
    _png_append_list($out, $data);
    _png_append_list($out, _png_u32be($crc));
    return $out;
}

function write_rgb_png($path, $width, $height, $pixels) {
    $raw = [];
    foreach ($pixels as $b) {
        $raw[] = ((int)($b));
    }
    $expected = (($width * $height) * 3);
    if ((__pytra_len($raw) != $expected)) {
        throw new Exception(strval(ValueError(((("pixels length mismatch: got=" . strval(__pytra_len($raw))) . " expected=") . strval($expected)))));
    }
    $scanlines = [];
    $row_bytes = ($width * 3);
    $y = 0;
    while (($y < $height)) {
        $scanlines[] = 0;
        $start = ($y * $row_bytes);
        $end = ($start + $row_bytes);
        $i = $start;
        while (($i < $end)) {
            $scanlines[] = $raw[__pytra_index($raw, $i)];
            $i += 1;
        }
        $y += 1;
    }
    $ihdr = [];
    _png_append_list($ihdr, _png_u32be($width));
    _png_append_list($ihdr, _png_u32be($height));
    _png_append_list($ihdr, [8, 2, 0, 0, 0]);
    $idat = _zlib_deflate_store($scanlines);
    $png = [];
    _png_append_list($png, [137, 80, 78, 71, 13, 10, 26, 10]);
    _png_append_list($png, _chunk([73, 72, 68, 82], $ihdr));
    _png_append_list($png, _chunk([73, 68, 65, 84], $idat));
    $iend_data = [];
    _png_append_list($png, _chunk([73, 69, 78, 68], $iend_data));
    $f = open($path, "wb");
    $f->write(bytes($png));
    $f->close();
}
