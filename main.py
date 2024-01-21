from collections import deque

import pygame
import pygame._sdl2 as sdl2

from scripts import space, platformer, util_draw


class Game:
    def __init__(self, title="Project Gemini", fps=0):
        self.title = title
        self.window = None
        self.renderer = None
        self.clock = pygame.time.Clock()
        self.screen_rect = pygame.Rect((0, 0), util_draw.RESOLUTION)
        self.fps = fps
        self.stack = deque()
        self.dt_mult = 1
        self.running = False
        self.renderer = None

    def run(self):
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
        self.stack.appendleft(space.Space(self))
        self.stack.appendleft(platformer.Level(self))
        dt = 0

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
            dt = self.clock.tick(self.fps) / 1000

        self.window.destroy()
        self.renderer = None

    def quit(self):
        self.running = False


Game().run()
