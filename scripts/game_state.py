import pygame
import pygame._sdl2 as sdl2

from scripts import util_draw


class GameState:
    def __init__(self, game, color="gray", vsync=True):
        self.game = game
        self.game.renderer.draw_color = self.bg_color = color
        self.screen_rect = pygame.Rect((0, 0), util_draw.RESOLUTION)

    def handle_event(self, event):
        pass

    def update(self, dt):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.game.quit()
            self.handle_event(event)


    def draw(self):
        pass
