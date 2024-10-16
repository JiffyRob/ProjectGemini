import asyncio
from collections import deque

import pygame
import pygame._sdl2 as sdl2
import pygame._sdl2.video as sdl2  # needed for WASM compat

from scripts import (
    game_save,
    input_binding,
    level,
    loader,
    menu,
    sound,
    space,
    util_draw,
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
        self.display_surface = None
        self.sound_manager = None
        self.save = game_save.GameSave(self)
        self.input_queue = input_binding.InputQueue()
        self.timers = []

    @property
    def window_surface(self):
        return self.display_surface

    @property
    def mouse_pos(self):
        if self.stack[0].scale_mode == util_draw.SCALEMODE_INTEGER:
            factor = min(
                self.window.get_surface().get_width() // util_draw.RESOLUTION[0],
                self.window.get_surface().get_height() // util_draw.RESOLUTION[1],
            )
            rect = pygame.Rect(
                0, 0, util_draw.RESOLUTION[0] * factor, util_draw.RESOLUTION[1] * factor
            )
            rect.center = self.window.get_surface().get_rect().center
            return (pygame.Vector2(pygame.mouse.get_pos()) - rect.topleft) / factor
        if self.stack[0].scale_mode == util_draw.SCALEMODE_STRETCH:
            return pygame.Vector2(pygame.mouse.get_pos()).elementwise() * (
                util_draw.RESOLUTION[0] / self.window.size[0],
                util_draw.RESOLUTION[1] / self.window.size[1],
            )

    def pop_state(self):
        self.stack.popleft()

    def load_map(self, map_name, direction=None, position=None, entrance=None):
        print("loading level:", map_name)
        new_map = level.Level.load(self, map_name, direction, position, entrance)
        if isinstance(self.stack[0], level.Level) and new_map.map_type != new_map.MAP_HOUSE:
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
            self.sound_manager.switch_track(f"music/{track_name}.wav")

    def update(self, dt):
        kill_state = False
        if not self.stack[0].update(dt * self.dt_mult):
            kill_state = True
        # if fps drops below 10 the game will start to lag
        dt = pygame.math.clamp(
            self.clock.tick(self.fps) * self.dt_mult / 1000, -0.1, 0.1
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
        self.window_surface.fill(self.stack[0].bgcolor)
        self.window.get_surface().fill("black")
        self.stack[0].draw()
        if self.stack[0].scale_mode == util_draw.SCALEMODE_INTEGER:
            factor = min(
                self.window.get_surface().get_width() // util_draw.RESOLUTION[0],
                self.window.get_surface().get_height() // util_draw.RESOLUTION[1],
            )
            rect = pygame.Rect(
                0,
                0,
                util_draw.RESOLUTION[0] * factor,
                util_draw.RESOLUTION[1] * factor,
            )
            rect.center = self.window.get_surface().get_rect().center
            self.window.get_surface().blit(
                pygame.transform.scale_by(self.display_surface, (factor, factor)),
                rect.topleft,
            )
        if self.stack[0].scale_mode == util_draw.SCALEMODE_STRETCH:
            self.window.get_surface().blit(
                pygame.transform.scale(self.display_surface, self.window.size),
                (0, 0),
            )
        self.window.flip()

    async def run(self):
        self.running = True
        self.window = sdl2.Window(
            self.title,
            util_draw.RESOLUTION,
            sdl2.WINDOWPOS_CENTERED,
            resizable=True,
            maximized=True,
        )
        self.window.get_surface()  # allows convert() calls to happen
        self.display_surface = pygame.Surface(util_draw.RESOLUTION).convert()
        self.loader = loader.Loader()
        self.load_input_binding("arrow")
        self.add_input_binding("controller")
        self.sound_manager = sound.SoundManager(self.loader)
        self.stack.appendleft(menu.MainMenu(self))
        dt = 0
        pygame.key.set_repeat(0, 0)

        while self.running and len(self.stack):
            self.input_queue.update()
            self.draw()
            dt = self.update(dt)
            self.window.title = str(int(self.clock.get_fps())).zfill(
                3
            )  # TODO: Remove this
            await asyncio.sleep(0)

        self.window.destroy()
        pygame.quit()

    def save_to_disk(self):
        self.save.save()

    def quit(self):
        while len(self.stack) > 1:
            self.stack.clear()
            self.stack.appendleft(menu.MainMenu(self))

    def exit(self):
        self.running = False


asyncio.run(Game().run())
