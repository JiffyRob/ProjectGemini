import pygame
from pygame.typing import RectLike

from gamelibs import interfaces


class Sprite(interfaces.Sprite):
    groups: set[str] = set()

    def __init__(
        self,
        level: interfaces.Level,
        image: pygame.Surface | None = None,
        rect: RectLike = (0, 0, 16, 16),
        z: int = 0,
    ) -> None:
        if image is None:
            image = pygame.Surface((0, 0))
        self._level: interfaces.Level = level
        self.image: pygame.Surface = image
        self._rect: interfaces.MiscRect = pygame.FRect(rect)
        self._z = z
        self.velocity = pygame.Vector2()
        self.dead = False
        self.locked = False
        self.effects: list[interfaces.SpriteEffect] = []
        self.hidden = False
        self.hidden_image = pygame.Surface((0, 0))
        self.attached_to: interfaces.Sprite | None = None

    def attach(self, other: interfaces.Sprite) -> None:
        self.attached_to = other

    def detach(self) -> None:
        self.attached_to = None
        self._rect = self.rect

    @property
    def to_draw(self) -> pygame.Surface:
        return self._to_draw

    @to_draw.setter
    def to_draw(self, value: pygame.Surface) -> None:
        self._to_draw = value

    @property
    def z(self) -> int:
        return self._z

    @z.setter
    def z(self, value: int) -> None:
        self._z = value

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

    def add_effect(self, effect: interfaces.SpriteEffect) -> None:
        self.effects.append(effect)

    def get_level(self) -> interfaces.Level:
        return self._level

    def get_player(self) -> interfaces.Player:
        return self.get_level().get_player()

    def get_game(self) -> interfaces.Game:
        return self.get_level().get_game()

    @property
    def pos(self) -> pygame.Vector2:
        return pygame.Vector2(self.rect.center)

    @property
    def rect(self) -> interfaces.MiscRect:
        return self._rect

    @rect.setter
    def rect(self, value: RectLike) -> None:
        self._rect = pygame.FRect(value)

    def update(self, dt: float) -> bool:
        if self.hidden:
            self.image = pygame.Surface((0, 0))
        if self.attached_to is not None:
            self.rect.center = self.attached_to.rect.center
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
