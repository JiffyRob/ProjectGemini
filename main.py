import asyncio
from collections import deque

import pygame
import pygame._sdl2 as sdl2
import pygame._sdl2.video as sdl2  # needed for WASM compat

from scripts import level, loader, sound, space, util_draw, game_save

pygame.init()


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

    def load_map(self, map_name):
        print("loading", map_name)
        self.stack.appendleft(level.Level.load(self, map_name))

    def time_phase(self, mult):
        self.dt_mult = mult

    def play_soundtrack(self, track_name):
        self.sound_manager.switch_track(f"music/{track_name}.wav")

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
        self.sound_manager = sound.SoundManager(self.loader)
        self.stack.appendleft(space.Space(self))
        self.stack.appendleft(level.Level.load(self, "GeminiII"))
        dt = 0
        pygame.key.set_repeat(0, 0)

        while self.running and len(self.stack):
            kill_state = False
            self.window_surface.fill(self.stack[0].bgcolor)
            self.window.get_surface().fill("black")
            if not self.stack[0].update(dt * self.dt_mult):
                kill_state = True
            self.stack[0].draw()
            # if fps drops below 10 the game will start to lag
            dt = pygame.math.clamp(
                self.clock.tick(self.fps) * self.dt_mult / 1000, -0.1, 0.1
            )
            self.dt_mult = 1
            # window scaling
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
            self.window.title = str(int(self.clock.get_fps())).zfill(3)
            await asyncio.sleep(0)
            if kill_state:
                self.stack.popleft()

        self.window.destroy()
        self.renderer = None
        self.loader = None

    def quit(self):
        self.running = False


asyncio.run(Game().run())
