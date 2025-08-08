import asyncio
import random
from typing import Any

import pygame
from pygame.typing import RectLike

from gamelibs import sprite, interfaces, hardware
from gamelibs.animation import Animation

from SNEK2 import AsyncSNEKCallable  # type: ignore


class Interactable(sprite.Sprite, interfaces.Interactor):
    groups = {"interactable"}

    def __init__(
        self,
        level: interfaces.Level,
        image: pygame.Surface | None = None,
        rect: RectLike = (0, 0, 16, 16),
        z: int = 0,
        script: interfaces.FileID = "oops",
        api: interfaces.SnekAPI | None = None,
    ) -> None:
        super().__init__(level, image, rect, z)
        self.script = script

        self.api: interfaces.SnekAPI
        if api is None:
            self.api = {}
        else:
            self.api = api

    def interact(self) -> interfaces.InteractionResult:
        self.get_game().run_cutscene(self.script, api=self.api)
        return interfaces.InteractionResult.NO_MORE


class Ship(Interactable, interfaces.Collider):
    groups = {"interactable", "static-collision"}

    def __init__(
        self,
        level: interfaces.Level,
        rect: RectLike = (0, 0, 48, 24),
        z: int = 0,
        **_: Any,
    ) -> None:
        rect = pygame.FRect(rect)
        rect = (rect[0], rect[1], 48, 32)  # ldtk always has single tile rects :/
        self._collision_rect = pygame.FRect(rect[0] + 10, rect[1] + 10, 32, 12)
        super().__init__(
            level,
            hardware.loader.get_surface("tileset.png", rect=(208, 0, 48, 32)),
            rect=rect,
            z=z,
            script="ship",
        )

    @property
    def collision_rect(self) -> interfaces.MiscRect:
        return self._collision_rect


class BrokenShip(Interactable, interfaces.Collider):
    groups = {"interactable", "static-collision"}

    def __init__(
        self,
        level: interfaces.Level,
        rect: RectLike = (0, 0, 48, 24),
        z: int = 0,
        **_: Any,
    ) -> None:
        rect = pygame.FRect(rect)
        rect = (rect[0], rect[1], 48, 32)  # ldtk always has single tile rects :/
        self._collision_rect = pygame.FRect(rect[0] + 10, rect[1] + 10, 32, 12)
        super().__init__(
            level,
            hardware.loader.get_surface("tileset.png", rect=(160, 0, 48, 32)),
            rect=rect,
            z=z,
            script="broken_ship",
        )

    @property
    def collision_rect(self) -> interfaces.MiscRect:
        return self._collision_rect


class House(Interactable, interfaces.Collider):
    groups = {"static-collision", "interactable"}

    def __init__(
        self,
        level: interfaces.Level,
        rect: RectLike = (0, 0, 64, 48),
        z: int = 0,
        **custom_fields: Any,
    ) -> None:
        # three rects to represent the house without the doorway
        rect = pygame.FRect(rect)
        roof_rect = pygame.FRect(rect[0], rect[1] + 10, 64, 22)
        self.extra_collision_rects = (
            pygame.FRect(roof_rect.left, roof_rect.bottom, 32, 16),
            roof_rect,
        )
        # use right side of door as collision rect as that's what interaction uses
        # this way you interact with the rect that has the sign on it
        self._collision_rect = pygame.FRect(
            roof_rect.left + 48,
            roof_rect.bottom,
            16,
            16,
        )
        # the doorway
        self.teleport_rect = pygame.FRect(
            roof_rect.left + 32,
            roof_rect.bottom,
            16,
            10,
        )
        self.dest_map = custom_fields["map"]
        super().__init__(
            level,
            image=hardware.loader.get_surface("tileset.png", rect=(0, 208, 64, 48)),
            rect=rect,
            z=z,
            script="furniture",
            api={"TEXT": custom_fields["Sign"]},
        )

    @property
    def collision_rect(self) -> interfaces.MiscRect:
        return self._collision_rect

    def update(self, dt: float) -> bool:
        if self.get_player().collision_rect.colliderect(self.teleport_rect):
            self.get_player().rect.top += (
                self.teleport_rect.bottom - self.get_player().collision_rect.top
            )
            self.get_game().switch_level(self.dest_map)
        return super().update(dt)


class Smith(Interactable, interfaces.Collider):
    groups = {"static-collision", "interactable"}

    def __init__(
        self,
        level: interfaces.Level,
        rect: RectLike = (0, 0, 64, 48),
        z: int = 0,
        **custom_fields: Any,
    ) -> None:
        # three rects to represent the house without the doorway
        rect = pygame.FRect(rect)
        roof_rect = pygame.FRect(rect[0], rect[1] + 15, 64, 22)
        self.extra_collision_rects = (
            pygame.FRect(roof_rect.left, roof_rect.bottom, 32, 16),
            roof_rect,
        )
        # use right side of door as collision rect as that's what interaction uses
        # this way you interact with the rect that has the sign on it
        self._collision_rect = pygame.FRect(
            roof_rect.left + 48,
            roof_rect.bottom,
            16,
            16,
        )
        # the doorway
        self.teleport_rect = pygame.FRect(
            roof_rect.left + 32,
            roof_rect.bottom,
            16,
            10,
        )
        self.dest_map = custom_fields["map"]
        super().__init__(
            level,
            image=hardware.loader.get_surface("tileset.png", rect=(0, 96, 64, 64)),
            rect=rect,
            z=z,
            script="furniture",
            api={"TEXT": custom_fields["Sign"]},
        )

    @property
    def collision_rect(self) -> interfaces.MiscRect:
        return self._collision_rect

    def update(self, dt: float) -> bool:
        if self.get_player().collision_rect.colliderect(self.teleport_rect):
            self.get_player().rect.top += (
                self.teleport_rect.bottom - self.get_player().collision_rect.top
            )
            self.get_game().switch_level(self.dest_map)
        return super().update(dt)


class Furniture(Interactable, interfaces.Collider):
    groups = {"static-collision", "interactable"}

    TABLE_LEFT = "Table_Left"
    TABLE_CENTER = "Table_Center"
    TABLE_RIGHT = "Table_Right"
    TABLE_PAPER = "Table_Paper"
    STOOL = "Stool"

    IMAGES = {
        TABLE_LEFT: 178,
        TABLE_CENTER: 179,
        TABLE_RIGHT: 180,
        TABLE_PAPER: 164,
        STOOL: 181,
    }

    def __init__(
        self,
        level: interfaces.Level,
        rect: RectLike = (0, 0, 16, 16),
        z: int = 0,
        **custom_fields: Any,
    ) -> None:
        self.type = custom_fields["Type"]
        self.info = custom_fields["Info"]
        super().__init__(
            level,
            rect=rect,
            image=hardware.loader.get_spritesheet("tileset.png", (16, 16))[
                self.IMAGES[self.type]
            ],
            z=z,
            script="furniture",
            api={"TEXT": self.info},
        )
        self._collision_rect = self.rect.copy()
        self._collision_rect.height *= 0.7
        self._collision_rect.centery = self.rect.centery

    @property
    def collision_rect(self) -> interfaces.MiscRect:
        return self._collision_rect


class Bush(sprite.Sprite):
    groups = {"static-collision"}

    def __init__(
        self,
        level: interfaces.Level,
        rect: RectLike = (0, 0, 16, 16),
        z: int = 0,
        **_: Any,
    ) -> None:
        super().__init__(
            level,
            hardware.loader.get_surface("tileset.png", rect=(160, 64, 16, 16)),
            rect,
            z,
        )
        self.collision_rect = self.rect.copy()


class Spikefruit(sprite.Sprite, interfaces.Interactor):
    groups = {"interactable"}

    def __init__(
        self,
        level: interfaces.Level,
        rect: RectLike = (0, 0, 16, 16),
        z: int = 0,
        **_: Any,
    ) -> None:
        self.frames = hardware.loader.get_spritesheet("spikeberry.png", (8, 8))
        self.fruit = 2
        self.collision_rect = pygame.FRect(rect)
        super().__init__(
            level,
            self.frames[2],
            rect,
            z - 1,
        )

    def interact(self) -> interfaces.InteractionResult:
        if self.fruit > 0:
            self.fruit -= 1
            self.image = self.frames[self.fruit]
            self.get_player().acquire("spikefruit", 1)
            return interfaces.InteractionResult.NO_MORE
        else:
            return interfaces.InteractionResult.FAILED


class WaspberryBush(sprite.Sprite, interfaces.Collider):
    groups = {"static-collision"}

    def __init__(
        self,
        level: interfaces.Level,
        rect: RectLike = (0, 0, 16, 16),
        z: int = 0,
        **_: Any,
    ) -> None:
        super().__init__(
            level,
            hardware.loader.get_surface("waspberry-bush.png"),
            rect,
            z,
        )
        self._collision_rect = self.rect
        for __ in range(5):
            rect = pygame.FRect(
                self.rect.centerx + random.uniform(-6, 5),
                self.rect.centery + random.uniform(-5, 6),
                2,
                2,
            )
            self.get_level().spawn("Waspberry", rect, z)

    @property
    def collision_rect(self) -> interfaces.MiscRect:
        return self._collision_rect


class Waspberry(sprite.Sprite, interfaces.Interactor):
    groups = {"interactable"}

    def __init__(
        self,
        level: interfaces.Level,
        rect: RectLike = (0, 0, 2, 2),
        z: int = 0,
        **_: Any,
    ) -> None:
        self.frames = hardware.loader.get_spritesheet("waspberry.png", (2, 2))
        super().__init__(
            level,
            random.choice(self.frames),
            rect,
            z + 1,
        )
        self.collision_rect = self.rect.copy()

    def interact(self) -> interfaces.InteractionResult:
        self.dead = True
        self.get_player().acquire("waspberry", 1)
        return interfaces.InteractionResult.NO_MORE


class Spapple(sprite.Sprite, interfaces.Interactor):
    groups = {"interactable"}

    def __init__(
        self,
        level: interfaces.Level,
        rect: RectLike = (0, 0, 16, 16),
        z: int = 0,
        **_: Any,
    ) -> None:
        self.frames = hardware.loader.get_spritesheet("spapple.png", (16, 16))
        self.fruit = 1
        self.collision_rect = pygame.FRect(rect)
        super().__init__(
            level,
            self.frames[1],
            rect,
            z,
        )

    def interact(self) -> interfaces.InteractionResult:
        if self.fruit > 0:
            self.fruit -= 1
            self.image = self.frames[self.fruit]
            self.get_player().acquire("spapple", 1)
            return interfaces.InteractionResult.NO_MORE
        return interfaces.InteractionResult.MORE


class Hoverboard(sprite.Sprite, interfaces.Interactor):
    groups = {"interactable"}

    def __init__(
        self,
        level: interfaces.Level,
        rect: RectLike = (0, 0, 32, 32),
        z: int = 0,
        **_: Any,
    ) -> None:
        self.anim = Animation(
            hardware.loader.get_spritesheet("hoverboard.png", (32, 32))[:4]
        )
        self.exit_anim = Animation(
            hardware.loader.get_spritesheet("hoverboard.png", (32, 32))[4:8]
        )
        self.exiting = False
        self.exited = asyncio.Event()
        super().__init__(level, self.anim.image, rect, z - 1)

    @property
    def collision_rect(self) -> interfaces.MiscRect:
        return self.rect.inflate(-16, -8)

    async def ride_off_into_sunset(self) -> None:
        self.get_player().lock()
        self.get_player().hide()
        self.get_player().attach(self)
        self.anim = self.exit_anim
        self.exiting = True
        await self.exited.wait()

    def interact(self) -> interfaces.InteractionResult:
        self.get_game().run_cutscene(
            "hoverboard",
            api={
                "ride_off_into_sunset": AsyncSNEKCallable(self.ride_off_into_sunset, 0)
            },
        )
        return interfaces.InteractionResult.NO_MORE

    def update(self, dt: float) -> bool:
        self.anim.update(dt)
        self.image = self.anim.image
        if self.exiting:
            self.rect.x += 64 * dt
            if self.rect.left > self.get_level().map_rect.right:
                self.get_player().rect.center = self.pos
                long_name = f"{self.get_level().name}_right"
                x = long_name.count("right") - long_name.count("left")
                y = long_name.count("down") - long_name.count("up")
                short_name = self.get_level().name.split("_")[0]
                if x < 0:
                    short_name += "_left" * abs(x)
                if x > 0:
                    short_name += "_right" * x
                if y < 0:
                    short_name += "_up" * abs(y)
                if y > 0:
                    short_name += "_down" * y
                self.get_game().switch_level(
                    short_name, direction=interfaces.Direction.RIGHT, position=self.pos
                )
                self.exited.set()
        return super().update(dt)
