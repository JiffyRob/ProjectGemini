import pygame
import pygame._sdl2 as sdl2

from scripts import util_draw


class GameState:
    def __init__(self, game, color="gray", vsync=True):
        self.game = game
        self.renderer = sdl2.Renderer(game.window, -1, -1, vsync)
        self.renderer.logical_size = util_draw.RESOLUTION
        self.renderer.draw_color = self.bg_color = color
        self.screen_rect = pygame.Rect((0, 0), util_draw.RESOLUTION)

    def update(self, dt):
        for event in pygame.event.get():
            match event:
                case pygame.Event(type=pygame.QUIT):
                    self.game.quit()

    def draw(self):
        # want black borders to keep game separate from the screen
        self.renderer.draw_color = "black"
        self.renderer.clear()
        self.renderer.draw_color = self.bg_color
        self.renderer.fill_rect(self.screen_rect)