import pygame
import pygame._sdl2 as sdl2
from collections import deque


class GameState:
    def __init__(self, game, color='gray', vsync=True):
        self.game = game
        self.renderer = sdl2.Renderer(game.window, -1, -1, vsync)
        self.renderer.draw_color = color

    def update(self, dt):
        for event in pygame.event.get():
            match event:
                case pygame.Event(type=pygame.QUIT):
                    self.game.quit()

    def draw(self):
        self.renderer.clear()
        self.renderer.present()


class Game:
    def __init__(self, title='Project Gemini', size=(640, 480), fps=60):
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
        self.window = sdl2.Window(self.title, self.size, sdl2.WINDOWPOS_CENTERED)
        self.stack.appendleft(GameState(self))
        dt = 0

        while self.running:
            self.stack[0].update(dt * self.dt_mult)
            self.stack[0].draw()
            dt = self.clock.tick(self.fps) / 1000

    def quit(self):
        self.running = False


Game().run()
