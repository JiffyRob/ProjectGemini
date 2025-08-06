import pygame
from pygame.typing import ColorLike

from gamelibs import util_draw, interfaces


class GameState(interfaces.GameState):
    def __init__(
        self, game: interfaces.Game, color: ColorLike = "gray", opengl: bool = False
    ) -> None:
        self.game = game
        self._bgcolor = color
        self.screen_rect = pygame.Rect((0, 0), util_draw.RESOLUTION)
        self.live = True
        self._opengl = opengl

    @property
    def opengl(self) -> bool:
        return self._opengl
    
    @opengl.setter
    def opengl(self, value: bool) -> None:
        self._opengl = value

    @property
    def bgcolor(self) -> ColorLike:
        return self._bgcolor
    
    @bgcolor.setter
    def bgcolor(self, value: ColorLike) -> None:
        self._bgcolor = value

    def pop(self) -> None:
        self.live = False

    def update(self, dt: float) -> bool:
        return self.live

    def draw(self) -> None:
        pass

    def get_game(self) -> interfaces.Game:
        return self.game
