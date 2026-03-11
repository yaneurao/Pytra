# representative self_hosted parser signature test: typed `*args` is still rejected.


class ControllerState:
    pressed: bool


def merge_controller_states(target: ControllerState, *states: ControllerState) -> None:
    target.pressed = False

