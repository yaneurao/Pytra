<?php
declare(strict_types=1);

if (!function_exists('__pytra_math_float')) {
    function __pytra_math_float($value): float {
        if (is_float($value)) {
            return $value;
        }
        if (is_int($value) || is_bool($value)) {
            return (float)$value;
        }
        if (is_string($value) && is_numeric($value)) {
            return (float)$value;
        }
        return 0.0;
    }
}

if (!function_exists('__pytra_math_pi')) {
    function __pytra_math_pi(): float {
        return pi();
    }
}

if (!function_exists('__pytra_math_e')) {
    function __pytra_math_e(): float {
        return exp(1.0);
    }
}

if (!function_exists('__pytra_math_sqrt')) {
    function __pytra_math_sqrt($value): float {
        return sqrt(__pytra_math_float($value));
    }
}

if (!function_exists('__pytra_math_sin')) {
    function __pytra_math_sin($value): float {
        return sin(__pytra_math_float($value));
    }
}

if (!function_exists('__pytra_math_cos')) {
    function __pytra_math_cos($value): float {
        return cos(__pytra_math_float($value));
    }
}

if (!function_exists('__pytra_math_tan')) {
    function __pytra_math_tan($value): float {
        return tan(__pytra_math_float($value));
    }
}

if (!function_exists('__pytra_math_exp')) {
    function __pytra_math_exp($value): float {
        return exp(__pytra_math_float($value));
    }
}

if (!function_exists('__pytra_math_log')) {
    function __pytra_math_log($value): float {
        return log(__pytra_math_float($value));
    }
}

if (!function_exists('__pytra_math_log10')) {
    function __pytra_math_log10($value): float {
        return log10(__pytra_math_float($value));
    }
}

if (!function_exists('__pytra_math_fabs')) {
    function __pytra_math_fabs($value): float {
        return abs(__pytra_math_float($value));
    }
}

if (!function_exists('__pytra_math_floor')) {
    function __pytra_math_floor($value): float {
        return floor(__pytra_math_float($value));
    }
}

if (!function_exists('__pytra_math_ceil')) {
    function __pytra_math_ceil($value): float {
        return ceil(__pytra_math_float($value));
    }
}

if (!function_exists('__pytra_math_pow')) {
    function __pytra_math_pow($left, $right): float {
        return pow(__pytra_math_float($left), __pytra_math_float($right));
    }
}
