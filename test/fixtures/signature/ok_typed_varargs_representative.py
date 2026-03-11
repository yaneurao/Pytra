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
