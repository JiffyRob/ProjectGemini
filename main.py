from collections import deque

import pygame
import pygame._sdl2 as sdl2

from scripts import space


class Game:
    def __init__(self, title="Project Gemini", size=(640, 480), fps=0):
        self.title = title
        self.size = size
        self.window = None
        self.clock = pygame.time.Clock()
        self.fps = fps
        self.stack = deque()
        self.dt_mult = 1
        self.running = False

    def run(self):
        self.running = True
        self.window = sdl2.Window(
            self.title,
            self.size,
            sdl2.WINDOWPOS_CENTERED,
            resizable=True,
            maximized=True,
        )
        self.stack.appendleft(space.Space(self))
        dt = 0

        while self.running:
            self.stack[0].update(dt * self.dt_mult)
            self.stack[0].draw()
            dt = self.clock.tick(self.fps) / 1000

    def quit(self):
        self.running = False


Game().run()
