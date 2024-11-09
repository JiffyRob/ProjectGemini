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
        window_size = self.window.get_size() # self.window.get_surface()
        window_rect = self.window.get_rect()
        if self.settings["scale"] == util_draw.SCALEMODE_INTEGER:
            factor = min(
                window_size[0] // util_draw.RESOLUTION[0],
                window_size[1] // util_draw.RESOLUTION[1],
            )
            rect = pygame.Rect(
                0, 0, util_draw.RESOLUTION[0] * factor, util_draw.RESOLUTION[1] * factor
            )
            rect.center = window_rect.center
            return (pygame.Vector2(pygame.mouse.get_pos()) - rect.topleft) / factor
        if self.settings["scale"] == util_draw.SCALEMODE_STRETCH:
            return pygame.Vector2(pygame.mouse.get_pos()).elementwise() * (
                util_draw.RESOLUTION[0] / window_size[0],
                util_draw.RESOLUTION[1] / window_size[1],
            )
        if self.settings["scale"] == util_draw.SCALEMODE_ASPECT:
            width_scale = window_size[0] / util_draw.RESOLUTION[0]
            height_scale = window_size[1] / util_draw.RESOLUTION[1]
            scale = min(width_scale, height_scale)
            rect = pygame.Rect(
                0,
                0,
                round(scale * window_size[0]),
                round(scale * window_size[1]))
            rect.center = window_rect.center
            return (pygame.Vector2(pygame.mouse.get_pos()) - rect.topleft) / scale

    def toggle_fullscreen(self):
        self.settings["fullscreen"] = not self.settings["fullscreen"]
        if self.settings["fullscreen"]:
            self.settings["last-resolution"] = self.window.get_size()
            self.window = pygame.display.set_mode(util_draw.RESOLUTION_FULLSCREEN, pygame.FULLSCREEN, vsync=self.settings["vsync"])
        else:
            self.window = pygame.display.set_mode(self.settings["last-resolution"], pygame.RESIZABLE, vsync=self.settings["vsync"])

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
        window_surface = self.window  # self.window.get_surface()
        self.stack[0].draw()
        if self.settings["scale"] == util_draw.SCALEMODE_INTEGER:
            factor = min(
                window_surface.get_width() // util_draw.RESOLUTION[0],
                window_surface.get_height() // util_draw.RESOLUTION[1],
            )
            rect = pygame.Rect(
                0,
                0,
                util_draw.RESOLUTION[0] * factor,
                util_draw.RESOLUTION[1] * factor,
            )
            rect.center = window_surface.get_rect().center
            window_surface.blit(
                pygame.transform.scale_by(self.display_surface, (factor, factor)),
                rect.topleft,
            )
        if self.settings["scale"] == util_draw.SCALEMODE_STRETCH:
            window_surface.blit(
                pygame.transform.scale(self.display_surface, self.window.size),
                (0, 0),
            )
        if self.settings["scale"] == util_draw.SCALEMODE_ASPECT:
            width_scale = window_surface.get_width() / util_draw.RESOLUTION[0]
            height_scale = window_surface.get_height() / util_draw.RESOLUTION[1]
            scale = min(width_scale, height_scale)
            rect = pygame.Rect(
                0,
                0,
                round(scale * util_draw.RESOLUTION[0]),
                round(scale * util_draw.RESOLUTION[1])
            )
            rect.center = window_surface.get_rect().center
            window_surface.blit(
                pygame.transform.scale(self.display_surface, rect.size), rect,
            )


        pygame.display.flip()
        # self.window.flip()

    async def run(self):
        self.running = True
        self.loader = loader.Loader()
        self.settings = self.loader.get_settings()
        """
        # commented out for lack of vsync
        self.window = pygame.window.Window(
            self.title,
            util_draw.RESOLUTION,
            sdl2.WINDOWPOS_CENTERED,
            resizable=True,
            maximized=True,
        )
        self.window.get_surface()  # allows convert() calls
        """
        if self.settings["last-resolution"] is None:
            info = pygame.display.Info()
            self.settings["last-resolution"] = (info.current_w, info.current_h - 32)
        self.window = pygame.display.set_mode(self.settings["last-resolution"], pygame.RESIZABLE, vsync=self.settings["vsync"])
        pygame.display.set_caption(self.title)
        if self.settings["fullscreen"]:
            self.toggle_fullscreen()
            self.settings["fullscreen"] = True
        self.loader.postwindow_init()
        self.display_surface = pygame.Surface(util_draw.RESOLUTION).convert()
        self.load_input_binding("arrow")
        self.add_input_binding("controller")
        self.sound_manager = sound.SoundManager(self.loader)
        self.stack.appendleft(menu.MainMenu(self))
        dt = 0
        pygame.key.set_repeat(0, 0)
        while self.running and len(self.stack):
            self.input_queue.update()
            if pygame.key.get_just_released()[pygame.K_F11]:
                print("TOGGLE")
                self.toggle_fullscreen()
            self.draw()
            dt = self.update(dt)
            await asyncio.sleep(0)

        # self.window.destroy()
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
