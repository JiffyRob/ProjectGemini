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


def event_to_strings(event, joystick_deadzone=0.3, controller_unique=False, split_hats=False):
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
            yield from event_to_strings(pygame.Event(
                HAT_AXIS_MOTION,
                {"hat": event.hat, "axis": 0, "value": event.value[0]},
            ))
            yield from event_to_strings(pygame.Event(
                HAT_AXIS_MOTION,
                {"hat": event.hat, "axis": 1, "value": event.value[1]}
            ))
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


class UserAction:
    JOYSTICK_DEADZONE = 0.3
    CONTROLLER_UNIQUE = False
    SPLIT_HATS = True

    def __init__(self, identifier, magnitude, original, original_name):
        self.identifier = identifier
        self.magnitude = magnitude
        self.original = original
        self.original_name = original_name


class InputQueue:
    def __init__(self):
        self.events = []
        self.originals = []
        self.bindings = {}

    def update(self, events=None):
        self.events.clear()
        self.originals.clear()
        if events is None:
            events = pygame.event.get()
        for raw_event in events:
            for action_id in event_to_strings(raw_event):
                if action_id in self.bindings:
                    for bound_identifier in self.bindings[action_id]:
                        self.events.append(UserAction(bound_identifier, event_magnitude(raw_event), raw_event, action_id))
            self.originals.append(raw_event)

    def get(self):
        yield from self.events

    def load_bindings(self, bindings):
        self.bindings.clear()
        for identifier, action in bindings.items():
            self.bindings.setdefault(identifier, set()).add(action)
