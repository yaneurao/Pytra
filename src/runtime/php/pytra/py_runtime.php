<?php
declare(strict_types=1);

function __pytra_print(...$args): void {
    if (count($args) === 0) {
        echo PHP_EOL;
        return;
    }
    $parts = [];
    foreach ($args as $arg) {
        if (is_bool($arg)) {
            $parts[] = $arg ? "True" : "False";
            continue;
        }
        if ($arg === null) {
            $parts[] = "None";
            continue;
        }
        $parts[] = (string)$arg;
    }
    echo implode(" ", $parts) . PHP_EOL;
}

