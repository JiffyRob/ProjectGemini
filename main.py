import asyncio
from collections import deque

import numpy
import pygame
import pygame._sdl2 as sdl2
import pygame._sdl2.video as sdl2  # needed for WASM compat

from scripts import loader, platformer, space, util_draw

pygame.init()


class Game:
    def __init__(self, title="Project Gemini", fps=0):
        self.title = title
        self.window = None
        self.clock = pygame.time.Clock()
        self.screen_rect = pygame.Rect((0, 0), util_draw.RESOLUTION)
        self.fps = fps
        self.stack = deque()
        self.dt_mult = 1
        self.running = False
        self.renderer = None
        self.loader = None

    async def run(self):
        self.running = True
        self.window = sdl2.Window(
            self.title,
            util_draw.RESOLUTION,
            sdl2.WINDOWPOS_CENTERED,
            resizable=True,
            maximized=True,
        )
        self.renderer = sdl2.Renderer(self.window, -1, -1, True)
        self.renderer.logical_size = util_draw.RESOLUTION
        self.loader = loader.Loader(self.renderer)
        # self.stack.appendleft(space.Space(self))
        self.stack.appendleft(platformer.Level.load(self, "Level_0"))
        dt = 0
        pygame.key.set_repeat(0, 0)

        while self.running and len(self.stack):
            self.stack[0].update(dt * self.dt_mult)
            # draw black borders on areas outside aspect ratio
            self.renderer.draw_color = "black"
            self.renderer.clear()
            # but still color that actual screen area with the state's background
            self.renderer.draw_color = self.stack[0].bg_color
            self.renderer.fill_rect(self.screen_rect)
            self.stack[0].draw()
            self.renderer.present()
            dt = self.clock.tick(self.fps) * self.dt_mult / 1000
            await asyncio.sleep(0)

        self.window.destroy()
        self.renderer = None
        self.loader = None

    def quit(self):
        self.running = False


asyncio.run(Game().run())
