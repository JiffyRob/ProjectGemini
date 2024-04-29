from queue import Queue

import pygame

HAT_AXIS_MOTION = pygame.event.custom_type()


def axis_direction(num, deadzone):
    if abs(num) < deadzone:
        return "center"
    if num < 0:
        return "back"
    if num > 0:
        return "forward"


def event_magnitude(event):
    if event.type == pygame.JOYAXISMOTION:
        return abs(event.value)
    return 1


def event_to_strings(
    event, joystick_deadzone=0.3, controller_unique=False, split_hats=False
):
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

    if "JOY" in identifiers[0] and controller_unique:
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

    if event.type in {pygame.JOYBUTTONUP, pygame.JOYBUTTONDOWN}:
        identifiers.append(event.button)

    if event.type == pygame.JOYAXISMOTION:
        # Just posting on/off
        # Possibly have a way of getting event "magnitude"
        identifiers.append(event.axis)
        identifiers.append(axis_direction(event.value, joystick_deadzone))

    yield "_".join([str(i) for i in identifiers])


def releaser_string(event_string):
    event_string = event_string.replace("KeyDown", "KeyUp")
    event_string = event_string.replace("MouseButtonDown", "MouseButtonUp")
    event_string = event_string.replace("JoyButtonDown", "JoyButtonUp")

    if "JoyAxisMotion" in event_string:
        event_string = event_string.replace("forward", "center")
        event_string = event_string.replace("back", "center")
    if "HatAxisMotion" in event_string:
        event_string = event_string.replace("-", "")
        event_string = event_string[:-1] + "0"

    return event_string


def init_joysticks():
    pygame.joystick.init()
    for i in range(pygame.joystick.get_count()):
        joy = pygame.joystick.Joystick(i)
        joy.init()
        yield joy


def interactive_id_printer():
    pygame.init()
    pygame.font.init()
    print(pygame.joystick.get_init())
    joys = list(init_joysticks())
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
            if event.type == pygame.QUIT:
                running = False
        clock.tick(60)
        pygame.display.update()
    pygame.quit()


class InputQueue:
    JOYSTICK_DEADZONE = 0.3
    CONTROLLER_UNIQUE = False
    SPLIT_HATS = True

    def __init__(self):
        self.joysticks = {}
        self.press_bindings = {}
        self.release_bindings = {}
        self.held = {}
        self.magnitudes = {}
        self.just_pressed = set()
        self.no_hold = set()

    def update(self, events=None):
        self.just_pressed.clear()
        if events is None:
            events = pygame.event.get()

        for raw_event in events:
            if raw_event.type == pygame.JOYDEVICEADDED:
                print("New JOYSTICK!")
                self.joysticks[raw_event.device_index] = pygame.Joystick(
                    raw_event.device_index
                )
            if raw_event.type == pygame.JOYDEVICEREMOVED:
                self.joysticks[raw_event.device_index].quit()
            for action_id in event_to_strings(
                raw_event,
                joystick_deadzone=self.JOYSTICK_DEADZONE,
                controller_unique=self.CONTROLLER_UNIQUE,
                split_hats=self.SPLIT_HATS,
            ):
                if action_id in self.press_bindings:
                    print(action_id, "down")
                    for bound_identifier in self.press_bindings[action_id]:
                        if action_id not in self.no_hold:
                            self.held[bound_identifier] = True
                        self.just_pressed.add(bound_identifier)
                if action_id in self.release_bindings:
                    for bound_identifier in self.release_bindings[action_id]:
                        self.held[bound_identifier] = False

    def load_bindings(self, bindings, delete_old=True):
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
                    self.held[identifier] = False
                else:
                    print(user_action, "Not releasable")
                    self.no_hold.add(user_action)