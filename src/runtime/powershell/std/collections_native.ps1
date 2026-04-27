# Collections native implementations for PowerShell target

function deque {
    $d = @{
        "__type__" = "deque"
        "__data__" = [System.Collections.Generic.LinkedList[object]]::new()
    }
    $d | Add-Member -MemberType ScriptMethod -Name "Add" -Value {
        param([object]$item)
        $this.__data__.AddLast($item)
    } -Force
    $d | Add-Member -MemberType ScriptProperty -Name "Count" -Value { return $this.__data__.Count } -Force
    return $d
}

function deque_popleft {
    param($self)
    if ($self.__data__.Count -eq 0) { throw "popleft from empty deque" }
    $val = $self.__data__.First.Value
    $self.__data__.RemoveFirst()
    return ,$val
}

function deque_append {
    param($self, [object]$item)
    $self.__data__.AddLast($item)
}

function deque_appendleft {
    param($self, [object]$item)
    $self.__data__.AddFirst($item)
}

function deque_clear {
    param($self)
    $self.__data__.Clear()
}
