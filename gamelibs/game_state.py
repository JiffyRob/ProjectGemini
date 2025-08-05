import pygame
from pygame.typing import ColorLike

from gamelibs import util_draw, interfaces

class GameState(interfaces.GameState):
    def __init__(self, game: interfaces.Game, color: ColorLike="gray", opengl: bool=False) -> None:
        self.game = game
        self.bgcolor = color
        self.screen_rect = pygame.Rect((0, 0), util_draw.RESOLUTION)
        self.live = True
        self.opengl = opengl

    def pop(self) -> None:
        self.live = False

    def update(self, dt: float) -> bool:
        return self.live

    def draw(self) -> None:
        pass