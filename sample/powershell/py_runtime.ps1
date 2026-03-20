Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function __pytra_print {
    param(
        [Parameter(ValueFromRemainingArguments = $true)]
        [object[]] $items
    )

    if ($items.Count -eq 0) {
        Write-Output ""
        return
    }

    $parts = New-Object System.Collections.Generic.List[string]
    foreach ($item in $items) {
        if ($item -eq $null) {
            $parts.Add("None")
        } elseif ($item -is [bool]) {
            $parts.Add((if ($item) { "True" } else { "False" }))
        } else {
            $parts.Add([string]$item)
        }
    }
    Write-Output ($parts -join " ")
}

function __pytra_len {
    param([object]$value)
    if ($value -eq $null) { return 0 }
    if ($value -is [string]) { return $value.Length }
    if ($value -is [array]) { return $value.Length }
    if ($value -is [System.Collections.ICollection]) { return $value.Count }
    return 0
}

function __pytra_str {
    param([object]$value)
    if ($value -eq $null) { return "None" }
    if ($value -is [bool]) { return (if ($value) { "True" } else { "False" }) }
    return [string]$value
}

function __pytra_int {
    param([object]$value)
    if ($value -eq $null) { return 0 }
    try {
        return [int]$value
    } catch {
        if ($value -is [bool]) { return (if ($value) { 1 } else { 0 }) }
        return 0
    }
}

function __pytra_bytearray {
    param([object]$size = 0)
    $count = __pytra_int $size
    if ($count -lt 0) {
        throw "[PowerShell backend experimental] negative bytearray size"
    }

    $result = New-Object System.Collections.Generic.List[int]
    for ($i = 0; $i -lt $count; $i++) {
        [void]$result.Add(0)
    }
    return [int[]]$result
}

function __pytra_bytes {
    param([object]$value)
    if ($value -is [string]) {
        $result = New-Object System.Collections.Generic.List[int]
        foreach ($ch in $value.ToCharArray()) {
            [void]$result.Add([int][char]$ch)
        }
        return [int[]]$result
    }
    if ($value -is [System.Collections.ICollection]) {
        $result = New-Object System.Collections.Generic.List[object]
        foreach ($item in $value) {
            [void]$result.Add(__pytra_int $item)
        }
        return $result.ToArray()
    }
    if ($value -is [int] -or $value -is [long]) {
        return __pytra_bytearray $value
    }
    return @()
}

function __pytra_ord {
    param([object]$value)
    if ($value -isnot [string] -or $value.Length -eq 0) {
        throw "[PowerShell backend experimental] ord() expected a non-empty string"
    }
    return [int][char]$value[0]
}

function __pytra_chr {
    param([object]$value)
    $codepoint = __pytra_int $value
    if ($codepoint -lt 0 -or $codepoint -gt 0x10FFFF) {
        throw "[PowerShell backend experimental] chr() argument out of range"
    }
    return [string]([char]$codepoint)
}

function __pytra_list {
    param([object]$value = 0)
    if ($value -is [int] -or $value -is [long]) {
        $count = __pytra_int $value
        $result = New-Object System.Collections.Generic.List[object]
        for ($i = 0; $i -lt $count; $i++) {
            [void]$result.Add($null)
        }
        return $result.ToArray()
    }
    if ($value -is [System.Collections.ICollection]) {
        $result = New-Object System.Collections.Generic.List[object]
        foreach ($item in $value) {
            [void]$result.Add($item)
        }
        return $result.ToArray()
    }
    return @()
}

function __pytra_set {
    param([object[]]$values)
    $result = @{}
    foreach ($item in $values) {
        $result["$item"] = $true
    }
    return $result
}

function __pytra_dict {
    param([object]$value = $null)
    if ($value -is [hashtable]) {
        $copy = @{}
        foreach ($key in $value.Keys) {
            $copy[$key] = $value[$key]
        }
        return $copy
    }
    if ($value -is [System.Collections.IDictionary]) {
        $copy = @{}
        foreach ($entry in $value.GetEnumerator()) {
            $copy[$entry.Key] = $entry.Value
        }
        return $copy
    }
    return @{}
}

function __pytra_error {
    param([object]$message = "")
    if ($message -eq $null) { return "" }
    if ($message -is [string]) { return $message }
    return [string]$message
}

function __pytra_bool {
    param([object]$value)
    if ($value -eq $null) { return $false }
    if ($value -is [bool]) { return $value }
    if ($value -is [int] -or $value -is [float] -or $value -is [double] -or $value -is [decimal]) { return [bool]$value }
    if ($value -is [string]) {
        $trimmed = $value.Trim().ToLowerInvariant()
        if ($trimmed -eq "true" -or $trimmed -eq "1") { return $true }
        if ($trimmed -eq "false" -or $trimmed -eq "0") { return $false }
        return $true
    }
    if ($value -is [System.Collections.ICollection]) {
        return $value.Count -ne 0
    }
    return [bool]$value
}

function __pytra_float {
    param([object]$value)
    if ($value -eq $null) { return 0.0 }
    try {
        return [double]$value
    } catch {
        if ($value -is [bool]) { return (if ($value) { 1.0 } else { 0.0 }) }
        return 0.0
    }
}

function __pytra_pow {
    param([object]$base, [object]$exp)
    $left = __pytra_float $base
    $right = __pytra_float $exp
    return [Math]::Pow($left, $right)
}

function __pytra_range {
    param(
        [object]$start,
        [object]$stop = $null,
        [object]$step = 1
    )

    $from = 0
    $to = 0
    if ($stop -eq $null) {
        $to = __pytra_int $start
    } else {
        $from = __pytra_int $start
        $to = __pytra_int $stop
    }
    $step_value = __pytra_int $step
    if ($step_value -eq 0) {
        throw "[PowerShell backend experimental] range step must not be 0"
    }

    $result = New-Object System.Collections.Generic.List[int]
    if ($step_value -gt 0) {
        for ($i = $from; $i -lt $to; $i += $step_value) {
            [void]$result.Add($i)
        }
        return [int[]]$result
    }

    $current = $from
    while ($current -gt $to) {
        [void]$result.Add($current)
        $current += $step_value
    }
    return [int[]]$result
}

function PytraNotImplemented {
    param([string]$Feature = "")
    if ($Feature -ne "") {
        throw "[PowerShell backend experimental] Not implemented: $Feature"
    }
    throw "[PowerShell backend experimental] Not implemented feature"
}
