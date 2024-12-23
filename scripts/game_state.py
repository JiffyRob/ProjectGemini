import pygame

from scripts import util_draw


class GameState:
    def __init__(self, game, color="gray", opengl=False):
        self.game = game
        self.bgcolor = color
        self.screen_rect = pygame.Rect((0, 0), util_draw.RESOLUTION)
        self.live = True
        self.opengl = opengl

    def pop(self):
        self.live = False

    def update(self, dt):
        return self.live

    def draw(self):
        pass
