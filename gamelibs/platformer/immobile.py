import random
from math import sin
from typing import Any

import pygame
from pygame.typing import RectLike

from gamelibs import sprite, interfaces, hardware
from gamelibs.animation import Animation


class Emerald(sprite.Sprite, interfaces.PlatformerSprite, interfaces.Pickup):
    def __init__(
        self,
        level: interfaces.PlatformerLevel,
        rect: RectLike = (0, 0, 16, 16),
        z: int = 0,
        **_: dict[str, Any]
    ) -> None:
        super().__init__(level, image=None, rect=rect, z=z)
        self.anim = Animation(
            hardware.loader.get_spritesheet("platformer-sprites.png")[0:5], 0.08
        )
        self.age = random.randint(0, 10)
        self.y = self.rect.top

    @property
    def collision_rect(self) -> interfaces.MiscRect:
        return self.rect.inflate(-8, -4)

    def get_player(self) -> interfaces.PlatformerPlayer:
        return super().get_player()  # type: ignore

    def get_level(self) -> interfaces.PlatformerLevel:
        return self._level  # type: ignore

    def update(self, dt: float) -> bool:
        if self.collision_rect.colliderect(self.get_player().collision_rect):
            self.get_player().pay(5)
            return False
        self.anim.update(dt)
        self.image = self.anim.image
        self.rect.top = self.y + 1.5 * sin(self.age * 2)
        self.age += dt
        return super().update(dt)


class CrazyMushroom(sprite.Sprite, interfaces.PlatformerSprite):
    groups = {"interactable", "static-collision"}

    def __init__(
        self, level: interfaces.Level, rect: RectLike = (0, 0, 16, 16), z: int = 0, **_
    ) -> None:
        super().__init__(level, None, rect, z)
        self.collision_rect = self.rect
        frames = hardware.loader.get_spritesheet("platformer-sprites.png")[35:38]
        self.anim = Animation(frames, speed=0.2)

    def get_player(self) -> interfaces.PlatformerPlayer:
        return super().get_player()  # type: ignore

    def get_level(self) -> interfaces.PlatformerLevel:
        return self._level  # type: ignore

    def update(self, dt: float) -> bool:
        self.anim.update(dt)
        self.image = self.anim.image
        return super().update(dt)

    def interact(self) -> None:
        self.get_game().run_cutscene("psychedelic")


class Prop(sprite.Sprite, interfaces.PlatformerSprite):
    FIRST = 13
    LAST = 15
    SPEED = 0.6

    def __init__(
        self, level: interfaces.Level, rect: RectLike = (0, 0, 16, 16), z: int = 0, **_
    ):
        super().__init__(level, image=None, rect=rect, z=z)
        self.anim = Animation(
            hardware.loader.get_spritesheet("platformer-sprites.png")[
                self.FIRST : self.LAST
            ],
            self.SPEED,
        )
        # util_draw.debug_show(self.anim.image)

    def get_player(self) -> interfaces.PlatformerPlayer:
        return super().get_player()  # type: ignore

    def get_level(self) -> interfaces.PlatformerLevel:
        return self._level  # type: ignore

    def update(self, dt: float) -> bool:
        self.anim.update(dt)
        self.image = self.anim.image
        return super().update(dt)


class BrownShroom(Prop, interfaces.PlatformerSprite):
    FIRST = 21
    LAST = 23


class BustedParts(sprite.Sprite, interfaces.PlatformerSprite):
    def __init__(
        self,
        level: interfaces.PlatformerLevel,
        rect: RectLike = (0, 0, 16, 16),
        z: int = 0,
        **_
    ) -> None:
        super().__init__(level, image=None, rect=rect, z=z)
        self.anim = Animation(
            hardware.loader.get_spritesheet("platformer-sprites.png")[16:20]
        )
        self.hit_image = hardware.loader.get_spritesheet("platformer-sprites.png")[20]
        self.hit_time = 0
        self.hit_wait = 0.2
        self.collision_rect = self.rect.inflate(-2, -12)
        self.collision_rect.bottom = self.rect.bottom

    def get_player(self) -> interfaces.PlatformerPlayer:
        return super().get_player()  # type: ignore

    def get_level(self) -> interfaces.PlatformerLevel:
        return self._level  # type: ignore

    def update(self, dt: float) -> bool:
        self.anim.update(dt)
        if self.collision_rect.colliderect(self.get_player().collision_rect):
            self.image = self.hit_image
            self.hit_time = 0.2
            self.get_player().jump(interfaces.JumpCause.PAIN)
            self.get_player().hurt(2)
        if self.hit_time > 0:
            self.hit_time -= dt
        else:
            self.image = self.anim.image
        return super().update(dt)


class CollisionSprite(sprite.Sprite, interfaces.PlatformerSprite):
    groups = {"static-collision"}

    def __init__(
        self,
        level: interfaces.PlatformerLevel,
        image: pygame.Surface | None = None,
        rect: RectLike = (0, 0, 16, 16),
        z: int = 0,
        **_
    ) -> None:
        if image is None:
            image = pygame.Surface(pygame.Rect(rect).size).convert_alpha()
        super().__init__(level, image=image, rect=rect, z=z)

    def get_player(self) -> interfaces.PlatformerPlayer:
        return super().get_player()  # type: ignore

    def get_level(self) -> interfaces.PlatformerLevel:
        return self._level  # type: ignore

    @property
    def collision_rect(self) -> interfaces.MiscRect:
        return self.rect.copy()
