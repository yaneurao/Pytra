# json_native.ps1 — native seam for pytra.std.json

function __pytra_json_dumps_value {
    param($obj, $indent, $level)
    if ($null -eq $obj) { return "null" }
    if ($obj -is [bool]) { if ($obj) { return "true" } else { return "false" } }
    if ($obj -is [string]) {
        $s = $obj.Replace('\', '\\').Replace('"', '\"').Replace("`n", '\n').Replace("`r", '\r').Replace("`t", '\t')
        return '"' + $s + '"'
    }
    if ($obj -is [System.Collections.IList] -or $obj -is [array]) {
        $arr = @($obj)
        if ($arr.Count -eq 0) { return "[]" }
        if ($null -eq $indent) {
            $parts = @(); foreach ($item in $arr) { $parts += (__pytra_json_dumps_value $item $null 0) }
            return "[" + ($parts -join ", ") + "]"
        }
        $pad = " " * ($indent * ($level + 1))
        $closePad = " " * ($indent * $level)
        $inner = @(); foreach ($item in $arr) { $inner += ($pad + (__pytra_json_dumps_value $item $indent ($level + 1))) }
        return ("[`n" + ($inner -join (",`n")) + "`n" + $closePad + "]")
    }
    if ($obj -is [System.Collections.IDictionary]) {
        $keys = @($obj.Keys)
        if ($keys.Count -eq 0) { return "{}" }
        if ($null -eq $indent) {
            $parts = @()
            foreach ($key in $keys) { $parts += ('"' + [string]$key + '": ' + (__pytra_json_dumps_value $obj[$key] $null 0)) }
            return "{" + ($parts -join ", ") + "}"
        }
        $pad = " " * ($indent * ($level + 1))
        $closePad = " " * ($indent * $level)
        $inner = @()
        foreach ($key in $keys) { $inner += ($pad + '"' + [string]$key + '": ' + (__pytra_json_dumps_value $obj[$key] $indent ($level + 1))) }
        return ("{`n" + ($inner -join (",`n")) + "`n" + $closePad + "}")
    }
    return [string]$obj
}

function __pytra_json_dumps {
    param($obj, $ensure_ascii = $true, $indent = $null, $separators = $null)
    return (__pytra_json_dumps_value $obj $indent 0)
}

function __pytra_json_loads {
    param($text)
    try {
        $parsed = ConvertFrom-Json $text -AsHashtable -ErrorAction Stop
        return (JsonValue $parsed)
    } catch { }
    try {
        $parsed = ConvertFrom-Json $text -ErrorAction Stop
        return (JsonValue $parsed)
    } catch { return $null }
}

function __pytra_json_loads_obj {
    param($text)
    $value = (__pytra_json_loads $text)
    if ($null -eq $value) { return $null }
    return (JsonValue_as_obj $value)
}

function JsonValue {
    param($raw)
    $result = @{}
    $result["__type__"] = "JsonValue"
    $result["raw"] = $raw
    return $result
}

function __pytra_json_raw {
    param($self)
    if ($self -is [hashtable] -and $self.ContainsKey("__type__") -and $self.ContainsKey("raw")) {
        return $self["raw"]
    }
    return $self
}

function __pytra_json_get_raw {
    param($self, $key)
    $raw = __pytra_json_raw $self
    if ($raw -is [hashtable] -or $raw -is [System.Collections.IDictionary]) {
        if ($raw.Contains($key)) { return $raw[$key] }
        return $null
    }
    if ($raw -is [array] -or $raw -is [System.Collections.IList]) {
        $idx = [int]$key
        if ($idx -ge 0 -and $idx -lt $raw.Count) { return $raw[$idx] }
        return $null
    }
    return $null
}

function JsonValue_as_str {
    param($self)
    $raw = $self["raw"]
    if ($raw -is [string]) { return $raw }
    return $null
}

function JsonValue_as_int {
    param($self)
    $raw = $self["raw"]
    if ($raw -is [int] -or $raw -is [long]) { return [long]$raw }
    return $null
}

function JsonValue_as_float {
    param($self)
    $raw = $self["raw"]
    if ($raw -is [double] -or $raw -is [float] -or $raw -is [decimal]) { return [double]$raw }
    return $null
}

function JsonValue_as_bool {
    param($self)
    $raw = $self["raw"]
    if ($raw -is [bool]) { return $raw }
    return $null
}

function JsonValue_as_obj {
    param($self)
    $raw = $self["raw"]
    if ($raw -is [hashtable] -or $raw -is [System.Collections.IDictionary]) {
        $result = @{}; $result["__type__"] = "JsonObj"; $result["raw"] = $raw; return $result
    }
    if ($null -ne $raw -and $raw.GetType().Name -eq "PSCustomObject") {
        $ht = @{}; foreach ($prop in $raw.PSObject.Properties) { $ht[$prop.Name] = $prop.Value }
        $result = @{}; $result["__type__"] = "JsonObj"; $result["raw"] = $ht; return $result
    }
    return $null
}

function JsonValue_as_arr {
    param($self)
    $raw = $self["raw"]
    if ($raw -is [array] -or $raw -is [System.Collections.IList]) {
        $result = @{}; $result["__type__"] = "JsonArr"; $result["raw"] = $raw; return $result
    }
    return $null
}

function JsonObj_get_obj {
    param($self, $key)
    return (JsonValue_as_obj (JsonValue (__pytra_json_get_raw $self $key)))
}

function JsonObj_get_arr {
    param($self, $key)
    return (JsonValue_as_arr (JsonValue (__pytra_json_get_raw $self $key)))
}

function JsonObj_get_str {
    param($self, $key)
    return (JsonValue_as_str (JsonValue (__pytra_json_get_raw $self $key)))
}

function JsonObj_get_int {
    param($self, $key)
    return (JsonValue_as_int (JsonValue (__pytra_json_get_raw $self $key)))
}

function JsonObj_get_float {
    param($self, $key)
    return (JsonValue_as_float (JsonValue (__pytra_json_get_raw $self $key)))
}

function JsonObj_get_bool {
    param($self, $key)
    return (JsonValue_as_bool (JsonValue (__pytra_json_get_raw $self $key)))
}

function JsonArr_get_obj { param($self, $index) return (JsonObj_get_obj $self $index) }
function JsonArr_get_arr { param($self, $index) return (JsonObj_get_arr $self $index) }
function JsonArr_get_str { param($self, $index) return (JsonObj_get_str $self $index) }
function JsonArr_get_int { param($self, $index) return (JsonObj_get_int $self $index) }
function JsonArr_get_float { param($self, $index) return (JsonObj_get_float $self $index) }
function JsonArr_get_bool { param($self, $index) return (JsonObj_get_bool $self $index) }

function __pytra_json_loads_arr {
    param($text)
    try {
        $parsed = ConvertFrom-Json $text -ErrorAction Stop
        if ($parsed -is [System.Array] -or $parsed -is [System.Collections.IList]) {
            $result = @{}
            $result["__type__"] = "JsonArr"
            $result["raw"] = $parsed
            return $result
        }
        return $null
    } catch { return $null }
}
