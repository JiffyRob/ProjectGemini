import asyncio
from collections import deque

import numpy
import pygame
import pygame._sdl2 as sdl2
import pygame._sdl2.video as sdl2  # needed for WASM compat

from scripts import loader, platformer, space, util_draw

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

    @property
    def window_surface(self):
        return self.display_surface

    def time_phase(self, mult):
        self.dt_mult = mult

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
        # self.stack.appendleft(space.Space(self))
        self.stack.appendleft(platformer.Level.load(self, "Level_0"))
        dt = 0
        pygame.key.set_repeat(0, 0)

        while self.running and len(self.stack):
            self.window_surface.fill(self.stack[0].bgcolor)
            self.window.get_surface().fill("black")
            self.stack[0].update(dt * self.dt_mult)
            self.stack[0].draw()
            # if fps drops below 10 the game will start to lag
            dt = pygame.math.clamp(self.clock.tick(self.fps) * self.dt_mult / 1000, -.1, .1)
            self.dt_mult = 1
            # self.window.title = str(round(self.clock.get_fps())).zfill(5)
            # window scaling
            factor = min(self.window.get_surface().get_width() // util_draw.RESOLUTION[0],
                         self.window.get_surface().get_height() // util_draw.RESOLUTION[1])
            rect = pygame.Rect(0, 0, util_draw.RESOLUTION[0] * factor, util_draw.RESOLUTION[1] * factor)
            rect.center = self.window.get_surface().get_rect().center
            self.window.get_surface().blit(pygame.transform.scale_by(self.display_surface, (factor, factor)), rect.topleft)
            self.window.flip()

        self.window.destroy()
        self.renderer = None
        self.loader = None

    def quit(self):
        self.running = False


asyncio.run(Game().run())
