import pygame
from pygame.typing import RectLike

from gamelibs import interfaces


class Sprite(interfaces.Sprite):
    groups: set[str] = set()

    def __init__(self, level: interfaces.Level, image: pygame.Surface | None=None, rect:RectLike=(0, 0, 16, 16), z: int=0) -> None:
        if image is None:
            image = pygame.Surface((0, 0))
        self.level: interfaces.Level = level
        self.image: pygame.Surface = image
        self.to_draw: pygame.Surface = image
        self.rect = pygame.FRect(rect)
        self.z = z
        self.velocity = pygame.Vector2()
        self.dead = False
        self.locked = False
        self.effects: list[interfaces.SpriteEffect] = []
        self.hidden = False
        self.hidden_image = pygame.Surface((0, 0))

    def message(self, message: str) -> None:
        print(self, "received", message)

    def hide(self) -> None:
        self.hidden = True
        self.hidden_image = self.image

    def show(self) -> None:
        self.hidden = False
        self.image = self.hidden_image

    def lock(self) -> None:
        self.locked = True

    def unlock(self) -> None:
        self.locked = False

    @property
    def pos(self) -> pygame.Vector2:
        return pygame.Vector2(self.rect.center)

    def update(self, dt: float) -> bool:
        if self.hidden:
            self.image = pygame.Surface((0, 0))
        self.effects = [effect for effect in self.effects if effect.update(dt)]
        if max(self.image.size):
            self.to_draw = self.image.copy()
            for effect in self.effects:
                effect.draw(self.to_draw)
        else:
            self.to_draw = pygame.Surface((0, 0))
        return not self.dead


class GUISprite(Sprite):
    def draw(self, surface: pygame.Surface) -> None:
        if max(self.image.size):
            surface.blit(self.image, self.rect)
