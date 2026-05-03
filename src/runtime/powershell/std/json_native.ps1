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
        $parsed = ConvertFrom-Json $text -AsHashTable -ErrorAction Stop
        $result = @{}
        $result["__type__"] = "JsonValue"
        $result["raw"] = (__pytra_json_to_plain $parsed)
        return ,$result
    } catch { return $null }
}

function __pytra_json_to_plain {
    param($value)
    if ($null -eq $value) { return $null }
    if ($value -is [array] -or $value -is [System.Collections.IList]) {
        $items = [System.Collections.Generic.List[object]]::new()
        foreach ($item in $value) {
            [void]$items.Add((__pytra_json_to_plain $item))
        }
        return ,$items
    }
    if ($value -is [hashtable] -or $value -is [System.Collections.IDictionary]) {
        $out = @{}
        foreach ($entry in $value.GetEnumerator()) {
            $out[$entry.Key] = (__pytra_json_to_plain $entry.Value)
        }
        return ,$out
    }
    if ($value.GetType().Name -eq "PSCustomObject") {
        $out = @{}
        foreach ($prop in $value.PSObject.Properties) {
            $out[$prop.Name] = (__pytra_json_to_plain $prop.Value)
        }
        return ,$out
    }
    return $value
}

function loads {
    param($text)
    $value = __pytra_json_loads $text
    if ($null -eq $value) { return $null }
    return ,$value["raw"]
}

function loads_obj {
    param($text)
    $value = __pytra_json_loads $text
    if ($null -eq $value) { return $null }
    $obj = JsonValue_as_obj $value
    if ($null -eq $obj) { return $null }
    return ,$obj["raw"]
}

function loads_arr {
    param($text)
    $value = __pytra_json_loads $text
    if ($null -eq $value) { return $null }
    $arr = JsonValue_as_arr $value
    if ($null -eq $arr) { return $null }
    return ,$arr["raw"]
}

function dumps {
    param($obj, $ensure_ascii = $true, $indent = $null, $separators = $null)
    return (__pytra_json_dumps $obj $ensure_ascii $indent $separators)
}

function dumps_jv {
    param($jv, $ensure_ascii = $true, $indent = $null, $separators = $null)
    if ($jv -is [hashtable] -and $jv.ContainsKey("raw")) {
        return (__pytra_json_dumps $jv["raw"] $ensure_ascii $indent $separators)
    }
    return (__pytra_json_dumps $jv $ensure_ascii $indent $separators)
}

function JsonValue {
    param($self, $raw = $null)
    $return_self = $false
    if ($null -eq $raw -and $null -ne $self -and -not ($self -is [hashtable])) {
        $raw = $self
        $self = @{}
        $return_self = $true
    }
    if ($null -eq $raw -and $self -is [hashtable] -and $self.ContainsKey("__type__") -and $self["__type__"] -eq "JsonValue" -and $self.ContainsKey("raw")) {
        return ,$self
    }
    if ($null -eq $raw -and $self -is [hashtable]) {
        $raw = $self
        $self = @{}
        $return_self = $true
    }
    if ($null -eq $self) { $self = @{}; $return_self = $true }
    $self["__type__"] = "JsonValue"
    $self["raw"] = $raw
    if ($return_self) { return ,$self }
    return
}

function JsonObj {
    param($self, $raw = @{})
    $return_self = $false
    if ($null -ne $self -and -not ($self -is [hashtable])) {
        $raw = $self
        $self = @{}
        $return_self = $true
    }
    if ($null -eq $self) { $self = @{}; $return_self = $true }
    $self["__type__"] = "JsonObj"
    $self["raw"] = $raw
    if ($return_self) { return ,$self }
    return
}

function JsonArr {
    param($self, $raw = @())
    $return_self = $false
    if ($null -ne $self -and -not ($self -is [hashtable])) {
        $raw = $self
        $self = @{}
        $return_self = $true
    }
    if ($null -eq $self) { $self = @{}; $return_self = $true }
    $self["__type__"] = "JsonArr"
    $self["raw"] = @($raw)
    if ($return_self) { return ,$self }
    return
}

function __pytra_json_value_obj {
    param($value)
    if (($value -is [System.Collections.IList] -or $value -is [array]) -and $value.Count -eq 1) {
        $value = $value[0]
    }
    if ($value -is [hashtable] -and $value.ContainsKey("__type__") -and $value["__type__"] -eq "JsonValue") {
        return ,$value
    }
    $out = @{}
    $out["__type__"] = "JsonValue"
    $out["raw"] = $value
    return ,$out
}

function JsonValue_as_str {
    param($self)
    if (($self -is [System.Collections.IList] -or $self -is [array]) -and $self.Count -eq 1) { $self = $self[0] }
    if (-not ($self -is [hashtable]) -or -not $self.ContainsKey("raw")) { $self = @{ "__type__" = "JsonValue"; "raw" = $self } }
    $raw = $self["raw"]
    if ($raw -is [string]) { return $raw }
    return $null
}

function JsonValue_as_int {
    param($self)
    if (($self -is [System.Collections.IList] -or $self -is [array]) -and $self.Count -eq 1) { $self = $self[0] }
    if (-not ($self -is [hashtable]) -or -not $self.ContainsKey("raw")) { $self = @{ "__type__" = "JsonValue"; "raw" = $self } }
    $raw = $self["raw"]
    if ($raw -is [int] -or $raw -is [long]) { return [long]$raw }
    return $null
}

function JsonValue_as_float {
    param($self)
    if (($self -is [System.Collections.IList] -or $self -is [array]) -and $self.Count -eq 1) { $self = $self[0] }
    if (-not ($self -is [hashtable]) -or -not $self.ContainsKey("raw")) { $self = @{ "__type__" = "JsonValue"; "raw" = $self } }
    $raw = $self["raw"]
    if ($raw -is [double] -or $raw -is [float] -or $raw -is [decimal]) { return [double]$raw }
    return $null
}

function JsonValue_as_bool {
    param($self)
    if (($self -is [System.Collections.IList] -or $self -is [array]) -and $self.Count -eq 1) { $self = $self[0] }
    if (-not ($self -is [hashtable]) -or -not $self.ContainsKey("raw")) { $self = @{ "__type__" = "JsonValue"; "raw" = $self } }
    $raw = $self["raw"]
    if ($raw -is [bool]) { return $raw }
    return $null
}

function JsonValue_as_obj {
    param($self)
    if (($self -is [System.Collections.IList] -or $self -is [array]) -and $self.Count -eq 1) { $self = $self[0] }
    if ($self -is [hashtable] -and $self.ContainsKey("__type__") -and $self["__type__"] -eq "JsonObj") {
        return ,$self
    }
    if ($self -is [hashtable] -and $self.ContainsKey("__type__") -and $self["__type__"] -eq "JsonValue" -and $self.ContainsKey("raw")) {
        $raw = $self["raw"]
    } else {
        $raw = $self
    }
    if ($raw -is [hashtable] -or $raw -is [System.Collections.IDictionary]) {
        $result = @{}; $result["__type__"] = "JsonObj"; $result["raw"] = $raw; return ,$result
    }
    if ($null -ne $raw -and $raw.GetType().Name -eq "PSCustomObject") {
        $ht = @{}; foreach ($prop in $raw.PSObject.Properties) { $ht[$prop.Name] = $prop.Value }
        $result = @{}; $result["__type__"] = "JsonObj"; $result["raw"] = $ht; return ,$result
    }
    return $null
}

function JsonValue_as_arr {
    param($self)
    if (($self -is [System.Collections.IList] -or $self -is [array]) -and $self.Count -eq 1) { $self = $self[0] }
    if ($self -is [hashtable] -and $self.ContainsKey("__type__") -and $self["__type__"] -eq "JsonArr") {
        return ,$self
    }
    if ($self -is [hashtable] -and $self.ContainsKey("__type__") -and $self["__type__"] -eq "JsonValue" -and $self.ContainsKey("raw")) {
        $raw = $self["raw"]
    } else {
        $raw = $self
    }
    if ($raw -is [array] -or $raw -is [System.Collections.IList]) {
        $result = @{}; $result["__type__"] = "JsonArr"; $result["raw"] = $raw; return ,$result
    }
    return $null
}

function __pytra_json_obj_raw {
    param($obj)
    if (($obj -is [System.Collections.IList] -or $obj -is [array]) -and $obj.Count -eq 1) { $obj = $obj[0] }
    if ($obj -is [hashtable] -and $obj.ContainsKey("raw")) { return ,$obj["raw"] }
    return ,$obj
}

function __pytra_json_arr_raw {
    param($arr)
    if (($arr -is [System.Collections.IList] -or $arr -is [array]) -and $arr.Count -eq 1) { $arr = $arr[0] }
    if ($arr -is [hashtable] -and $arr.ContainsKey("raw")) { return ,$arr["raw"] }
    return ,$arr
}

function JsonObj_get_str {
    param($obj, $key)
    if (($obj -is [System.Collections.IList] -or $obj -is [array]) -and $obj.Count -eq 1) { $obj = $obj[0] }
    $raw = $obj
    if ($obj -is [hashtable] -and $obj.ContainsKey("raw")) { $raw = $obj["raw"] }
    if ($null -eq $raw -or -not $raw.ContainsKey($key)) { return $null }
    return JsonValue_as_str (__pytra_json_value_obj $raw[$key])
}

function JsonObj_get_obj {
    param($obj, $key)
    if (($obj -is [System.Collections.IList] -or $obj -is [array]) -and $obj.Count -eq 1) { $obj = $obj[0] }
    $raw = $obj
    if ($obj -is [hashtable] -and $obj.ContainsKey("raw")) { $raw = $obj["raw"] }
    if ($null -eq $raw -or -not $raw.ContainsKey($key)) { return $null }
    return JsonValue_as_obj (__pytra_json_value_obj $raw[$key])
}

function JsonObj_get_arr {
    param($obj, $key)
    if (($obj -is [System.Collections.IList] -or $obj -is [array]) -and $obj.Count -eq 1) { $obj = $obj[0] }
    $raw = $obj
    if ($obj -is [hashtable] -and $obj.ContainsKey("raw")) { $raw = $obj["raw"] }
    if ($null -eq $raw -or -not $raw.ContainsKey($key)) { return $null }
    return JsonValue_as_arr (__pytra_json_value_obj $raw[$key])
}

function JsonArr_get_str {
    param($arr, $index)
    if (($arr -is [System.Collections.IList] -or $arr -is [array]) -and $arr.Count -eq 1) { $arr = $arr[0] }
    $raw = $arr
    if ($arr -is [hashtable] -and $arr.ContainsKey("raw")) { $raw = $arr["raw"] }
    if ($null -eq $raw -or $index -lt 0 -or $index -ge $raw.Count) { return $null }
    return JsonValue_as_str (__pytra_json_value_obj $raw[$index])
}

function JsonArr_get_int {
    param($arr, $index)
    if (($arr -is [System.Collections.IList] -or $arr -is [array]) -and $arr.Count -eq 1) { $arr = $arr[0] }
    $raw = $arr
    if ($arr -is [hashtable] -and $arr.ContainsKey("raw")) { $raw = $arr["raw"] }
    if ($null -eq $raw -or $index -lt 0 -or $index -ge $raw.Count) { return $null }
    return JsonValue_as_int (__pytra_json_value_obj $raw[$index])
}

function __pytra_json_loads_arr {
    param($text)
    try {
        $parsed = ConvertFrom-Json $text -AsHashTable -ErrorAction Stop
        if ($parsed -is [System.Array] -or $parsed -is [System.Collections.IList]) {
            $result = @{}
            $result["__type__"] = "JsonArr"
            $result["raw"] = $parsed
            return $result
        }
        return $null
    } catch { return $null }
}
