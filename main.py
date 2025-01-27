import asyncio
from collections import deque

import pygame
import zengl
import numpy

from scripts import (
    game_save,
    input_binding,
    level,
    loader,
    menu,
    sound,
    space,
    util_draw,
    env,
    window,
)

pygame.init()
pygame.joystick.init()


class Game:
    def __init__(self, title="Project Gemini", fps=60):
        self.title = title
        self.window = None
        self.clock = pygame.time.Clock()
        self.screen_rect = pygame.Rect((0, 0), util_draw.RESOLUTION)
        self.fps = fps
        self.stack = deque()
        self.dt_mult = 1
        self.running = False
        self.loader = None
        self.sound_manager = None
        self.save = game_save.GameSave(self)
        self.input_queue = input_binding.InputQueue()
        self.timers = []
        self.context = None

    @property
    def mouse_pos(self):
        return self.window.mouse_pos

    @property
    def window_surface(self):
        return self.window.get_soft_surface()

    @property
    def gl_window_surface(self):
        return self.window.get_gl_surface()

    def pop_state(self):
        self.stack.popleft()

    def load_map(self, map_name, direction=None, position=None, entrance=None):
        print("loading level:", map_name)
        new_map = level.Level.load(self, map_name, direction, position, entrance)
        if (
            isinstance(self.stack[0], level.Level)
            and new_map.map_type != new_map.MAP_HOUSE
        ):
            self.pop_state()
        self.stack.appendleft(new_map)
        if "_" not in map_name:
            self.save.planet = map_name

    def load_save(self, save_name):
        print("opening save:", save_name)
        self.stack.clear()
        self.save.load(save_name)
        self.stack.appendleft(space.Space(self))
        self.stack.appendleft(level.Level.load(self, self.save.planet))

    def delayed_callback(self, dt, callback):
        self.timers.append((dt, callback))

    def load_input_binding(self, name):
        self.input_queue.load_bindings(
            self.loader.get_json(f"keybindings/{name}"), delete_old=True
        )

    def add_input_binding(self, name):
        self.input_queue.load_bindings(
            self.loader.get_json(f"keybindings/{name}"), delete_old=False
        )

    def time_phase(self, mult):
        self.dt_mult = mult

    def play_soundtrack(self, track_name):
        if track_name is None:
            self.sound_manager.stop_track()
        else:
            self.sound_manager.switch_track(f"music/{track_name}.ogg")

    def update(self, dt):
        kill_state = False
        if not self.stack[0].update(dt * self.dt_mult):
            kill_state = True
        # if fps drops below 10 the game will start to lag
        dt = pygame.math.clamp(
            self.clock.tick(self.settings["frame-cap"] * (not env.PYGBAG))
            * self.dt_mult
            / 1000,
            -0.1,
            0.1,
        )
        # update delayed callbacks
        still_waiting = []
        for index in range(len(self.timers)):
            self.timers[index][0] -= dt
            if self.timers[index][0] <= 0:
                self.timers[index][1]()
            else:
                still_waiting.append(self.timers[index])
        self.timers = still_waiting
        if kill_state:
            self.stack.popleft()
        self.dt_mult = 1
        return dt

    def draw(self):
        self.context.new_frame()
        self.stack[0].draw()
        self.window.render(not self.stack[0].opengl)
        self.context.end_frame()
        self.window.flip()

    async def run(self):
        self.running = True
        self.loader = loader.Loader()
        self.settings = self.loader.get_settings()

        if self.settings["last-resolution"] is None:
            info = pygame.display.Info()
            self.settings["last-resolution"] = (info.current_w, info.current_h - 32)

        self.window = window.WindowOld(
            self,
            "Project Gemini",
            self.settings["last-resolution"],
            self.settings["scale"],
            self.settings["vsync"],
            self.settings["fullscreen"],
        )
        self.context = zengl.context()

        self.loader.postwindow_init()

        self.load_input_binding("arrow")
        self.add_input_binding("controller")
        self.sound_manager = sound.SoundManager(self.loader)

        self.stack.appendleft(menu.MainMenu(self))
        # self.stack.appendleft(space.Space(self))
        dt = 0
        pygame.key.set_repeat(0, 0)
        while self.running and len(self.stack):
            events = tuple(pygame.event.get())
            self.input_queue.update(events)
            for event in events:
                if event.type == pygame.VIDEORESIZE:
                    self.window.resize(event.size)
            self.draw()
            dt = self.update(dt)
            await asyncio.sleep(0)

        pygame.quit()

    def save_to_disk(self):
        self.save.save()

    def quit(self):
        self.loader.save_settings(self.settings)
        self.loader.flush()
        while len(self.stack) > 1:
            self.stack.clear()
        self.stack.appendleft(menu.MainMenu(self))

    def exit(self):
        self.running = env.PYGBAG


asyncio.run(Game().run())
