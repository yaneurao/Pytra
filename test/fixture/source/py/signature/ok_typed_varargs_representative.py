class ControllerState:
    pressed: bool


def merge_controller_states(target: ControllerState, *states: ControllerState) -> None:
    for state in states:
        target.pressed = target.pressed or state.pressed


def apply_controller_states(
    target: ControllerState,
    lhs: ControllerState,
    rhs: ControllerState,
) -> bool:
    merge_controller_states(target, lhs, rhs)
    return target.pressed


if __name__ == "__main__":
    t: ControllerState = ControllerState()
    t.pressed = False
    a: ControllerState = ControllerState()
    a.pressed = True
    b: ControllerState = ControllerState()
    b.pressed = False
    print(apply_controller_states(t, a, b))
