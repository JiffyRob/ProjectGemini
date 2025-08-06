from typing import Iterator, Iterable, Literal
import pygame
import pygame._sdl2.controller as controller

from gamelibs import timer

controller.init()

HAT_AXIS_MOTION = pygame.event.custom_type()
CONTROLLER_AXIS_SIZE = 32768


def axis_direction(
    num: float, deadzone: float
) -> Literal["center"] | Literal["back"] | Literal["forward"]:
    if abs(num) < deadzone:
        return "center"
    elif num < 0:
        return "back"
    else:
        return "forward"


def event_magnitude(event: pygame.Event) -> int:
    if event.type == pygame.JOYAXISMOTION:
        return abs(event.value)  # type: ignore
    return 1


def event_to_strings(
    event: pygame.Event,
    joystick_deadzone: float = 0.3,
    controller_unique: bool = False,
    split_hats: bool = False,
) -> Iterator[str]:
    event = pygame.Event(event.type, event.dict)
    if event.type == HAT_AXIS_MOTION:
        identifiers = ["HatAxisMotion"]
    else:
        identifiers = [pygame.event.event_name(event.type)]

    if event.type in {pygame.MOUSEBUTTONDOWN, pygame.MOUSEBUTTONUP}:
        identifiers.append(event.button)

    # I don't know how nicely to bind mouse motion to anything
    # Do that manually I guess...?
    if event.type in {pygame.KEYDOWN, pygame.KEYUP}:
        identifiers.append(pygame.key.name(event.key))

    # controllers axes are at a different range.  Adjust to match joysticks.
    if event.type == pygame.CONTROLLERAXISMOTION:
        event.value /= CONTROLLER_AXIS_SIZE

    if (
        "Joy" in identifiers[0] or "Controller" in identifiers[0]
    ) and controller_unique:
        identifiers.insert(0, pygame.joystick.Joystick(event.instance_id).get_guid())

    if event.type in {pygame.JOYHATMOTION}:
        if split_hats:
            yield from event_to_strings(
                pygame.Event(
                    HAT_AXIS_MOTION,
                    {"hat": event.hat, "axis": 0, "value": event.value[0]},
                )
            )
            yield from event_to_strings(
                pygame.Event(
                    HAT_AXIS_MOTION,
                    {"hat": event.hat, "axis": 1, "value": event.value[1]},
                )
            )
        else:
            identifiers.append(event.hat)
            identifiers.append(event.value)

    if event.type in {HAT_AXIS_MOTION}:
        identifiers.append(event.hat)
        identifiers.append(event.axis)
        identifiers.append(event.value)

    if event.type in {
        pygame.JOYBUTTONUP,
        pygame.JOYBUTTONDOWN,
        pygame.CONTROLLERBUTTONUP,
        pygame.CONTROLLERBUTTONDOWN,
    }:
        identifiers.append(event.button)

    if event.type in {pygame.JOYAXISMOTION, pygame.CONTROLLERAXISMOTION}:
        # Just posting on/off
        # Possibly have a way of getting event "magnitude"
        identifiers.append(event.axis)
        identifiers.append(axis_direction(event.value, joystick_deadzone))

    yield "_".join([str(i) for i in identifiers])


def releaser_string(event_string: str) -> str:
    event_string = event_string.replace("KeyDown", "KeyUp")
    event_string = event_string.replace("MouseButtonDown", "MouseButtonUp")
    event_string = event_string.replace("JoyButtonDown", "JoyButtonUp")
    event_string = event_string.replace("ControllerButtonDown", "ControllerButtonUp")

    if "JoyAxisMotion" in event_string or "ControllerAxisMotion" in event_string:
        event_string = event_string.replace("forward", "center")
        event_string = event_string.replace("back", "center")
    if "HatAxisMotion" in event_string:
        event_string = event_string.replace("-", "")
        event_string = event_string[:-1] + "0"

    return event_string


def init_joysticks() -> Iterator[tuple[int, pygame.joystick.JoystickType]]:
    pygame.joystick.init()
    for i in range(pygame.joystick.get_count()):
        joy = pygame.joystick.Joystick(i)
        yield i, joy


def init_controllers() -> Iterator[tuple[int, controller.Controller]]:
    controller.init()
    for i in range(controller.get_count()):
        if controller.is_controller(i):
            gamepad = controller.Controller(i)
            gamepad.init()
            yield i, gamepad


def interactive_id_printer() -> None:
    pygame.init()
    controller.init()
    pygame.font.init()
    joys = dict(init_joysticks())
    controllers = dict(init_controllers())
    clock = pygame.time.Clock()
    font = pygame.font.SysFont(None, 40)
    surface = font.render(
        "Events will be printed to console as strings", True, "black", "white"
    )
    screen = pygame.display.set_mode(surface.get_size())
    screen.blit(surface, (0, 0))
    running = True

    while running:
        for event in pygame.event.get():
            for string in event_to_strings(event, split_hats=True):
                print(string)
            if event.type == pygame.JOYDEVICEADDED:
                joy = pygame.joystick.Joystick(event.device_index)
                joys[event.device_index] = joy
            if event.type == pygame.JOYDEVICEREMOVED:
                joys[event.instance_id].quit()
                del joys[event.instance_id]
            if event.type == pygame.CONTROLLERDEVICEADDED:
                gamepad = controller.Controller(event.device_index)
                gamepad.init()
                controllers[event.device_index] = gamepad
            if event.type == pygame.CONTROLLERDEVICEREMOVED:
                controllers[event.device_index].quit()
                del controllers[event.device_index]

            if event.type == pygame.QUIT:
                running = False
        clock.tick(60)
        pygame.display.update()
    pygame.quit()


class InputQueue:
    JOYSTICK_DEADZONE = 0.3
    CONTROLLER_UNIQUE = False
    SPLIT_HATS = True

    def __init__(self) -> None:
        self.joysticks = dict(init_joysticks())
        self.controllers = dict(init_controllers())
        self.press_bindings: dict[str, set[str]] = {}
        self.release_bindings: dict[str, set[str]] = {}
        self.magnitudes = {}
        self.held: set[str] = set()
        self.just_pressed: set[str] = set()
        self.no_hold: set[str] = set()
        self.rumble_timer = timer.Timer()

    def rumble(self, left: float = 1, right: float = 1, time: int = 500) -> None:
        for gamepad in self.controllers.values():
            gamepad.rumble(left, right, 0)
        self.rumble_timer = timer.Timer(time, self.stop_rumble)

    def stop_rumble(self) -> None:
        for gamepad in self.controllers.values():
            gamepad.stop_rumble()
        self.rumble_timer = timer.Timer()

    def update(self, events: Iterable[pygame.Event] | None = None) -> None:
        self.just_pressed.clear()
        self.rumble_timer.update()
        if events is None:
            events = pygame.event.get()

        for raw_event in events:
            if raw_event.type == pygame.JOYDEVICEADDED:
                self.joysticks[raw_event.device_index] = pygame.Joystick(
                    raw_event.device_index
                )
            if raw_event.type == pygame.JOYDEVICEREMOVED:
                self.joysticks[raw_event.instance_id].quit()
            if raw_event.type == pygame.CONTROLLERDEVICEADDED:
                self.controllers[raw_event.device_index] = controller.Controller(
                    raw_event.device_index
                )
            if raw_event.type == pygame.CONTROLLERDEVICEREMOVED:
                self.controllers[raw_event.instance_id].quit()
            for action_id in event_to_strings(
                raw_event,
                joystick_deadzone=self.JOYSTICK_DEADZONE,
                controller_unique=self.CONTROLLER_UNIQUE,
                split_hats=self.SPLIT_HATS,
            ):
                if action_id in self.press_bindings:
                    for bound_identifier in self.press_bindings[action_id]:
                        if action_id not in self.no_hold:
                            self.held.add(bound_identifier)
                        self.just_pressed.add(bound_identifier)
                if action_id in self.release_bindings:
                    for bound_identifier in self.release_bindings[action_id]:
                        self.held.discard(bound_identifier)

    def load_bindings(
        self, bindings: dict[str, set[str | None]], delete_old: bool = True
    ) -> None:
        if delete_old:
            self.press_bindings = {
                # These input bindings are non-configurable
                "Quit": {"quit"},
                "KeyDown-f11": {"toggle_fullscreen"},
            }
            self.release_bindings.clear()
            self.held.clear()
            self.just_pressed.clear()
        for identifier, user_actions in bindings.items():
            for user_action in user_actions:
                if user_action is None:
                    continue
                self.press_bindings.setdefault(user_action, set()).add(identifier)
                release_action = releaser_string(user_action)
                if release_action != user_action:
                    self.release_bindings.setdefault(release_action, set()).add(
                        identifier
                    )
                    self.held.discard(identifier)
                else:
                    print(user_action, "Not releasable")
                    self.no_hold.add(user_action)


if __name__ == "__main__":
    interactive_id_printer()
