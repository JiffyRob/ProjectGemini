import pygame
import pygame._sdl2 as sdl2

from scripts import util_draw


class GameState:
    def __init__(self, game, color="gray", scale_mode=util_draw.SCALEMODE_INTEGER):
        self.game = game
        self.bgcolor = color
        self.screen_rect = pygame.Rect((0, 0), util_draw.RESOLUTION)
        self.scale_mode = scale_mode
        self.live = True

    def pop(self):
        self.live = False

    def update(self, dt):
        if "quit" in self.game.input_queue.just_pressed:
            self.game.quit()
        return self.live

    def draw(self):
        pass
