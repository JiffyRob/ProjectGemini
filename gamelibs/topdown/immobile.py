import asyncio
import random

import pygame

from gamelibs import sprite
from gamelibs.animation import Animation

from SNEK2 import AsyncSNEKCallable  # type: ignore

class Interactable(sprite.Sprite):
    groups = {"interactable"}

    def __init__(
        self,
        level,
        image=None,
        rect=(0, 0, 16, 16),
        z=0,
        script="oops",
        api=None,
    ):
        super().__init__(level, image, rect, z)
        self.script = script
        if api is None:
            self.api = {}
        else:
            self.api = api

    def interact(self):
        self.level.game.run_cutscene(self.script, api=self.api)


class Ship(Interactable):
    groups = {"interactable", "static-collision"}

    def __init__(self, level, rect=(0, 0, 48, 24), z=0, **custom_fields):
        rect = (rect[0], rect[1], 48, 32)  # ldtk always has single tile rects :/
        self.collision_rect = pygame.FRect(rect[0] + 10, rect[1] + 10, 32, 12)
        super().__init__(
            level,
            level.game.loader.get_surface("tileset.png", rect=(208, 0, 48, 32)),
            rect=rect,
            z=z,
            script="ship",
        )


class BrokenShip(Interactable):
    groups = {"interactable", "static-collision"}

    def __init__(self, level, rect=(0, 0, 48, 24), z=0, **custom_fields):
        rect = (rect[0], rect[1], 48, 32)
        self.collision_rect = pygame.FRect(rect[0] + 10, rect[1] + 10, 32, 12)
        super().__init__(
            level,
            level.game.loader.get_surface("tileset.png", rect=(160, 0, 48, 32)),
            rect=rect,
            z=z,
            script="broken_ship",
        )


class House(Interactable):
    groups = {"static-collision", "interactable"}

    def __init__(self, level, rect=(0, 0, 64, 48), z=0, **custom_fields):
        # three rects to represent the house without the doorway
        roof_rect = pygame.FRect(rect[0], rect[1] + 10, 64, 22)
        self.extra_collision_rects = (
            pygame.FRect(roof_rect.left, roof_rect.bottom, 32, 16),
            roof_rect,
        )
        # use right side of door as collision rect as that's what interaction uses
        # this way you interact with the rect that has the sign on it
        self.collision_rect = pygame.FRect(
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
            image=level.game.loader.get_surface("tileset.png", rect=(0, 208, 64, 48)),
            rect=rect,
            z=z,
            script="furniture",
            api={"TEXT": custom_fields["Sign"]},
        )

    def update(self, dt):
        if self.level.player.collision_rect.colliderect(self.teleport_rect):
            self.level.player.rect.top += (
                self.teleport_rect.bottom - self.level.player.collision_rect.top
            )
            self.level.switch_level(self.dest_map)
        return super().update(dt)


class Smith(Interactable):
    groups = {"static-collision", "interactable"}

    def __init__(self, level, rect=(0, 0, 64, 48), z=0, **custom_fields):
        # three rects to represent the house without the doorway
        roof_rect = pygame.FRect(rect[0], rect[1] + 15, 64, 22)
        self.extra_collision_rects = (
            pygame.FRect(roof_rect.left, roof_rect.bottom, 32, 16),
            roof_rect,
        )
        # use right side of door as collision rect as that's what interaction uses
        # this way you interact with the rect that has the sign on it
        self.collision_rect = pygame.FRect(
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
            image=level.game.loader.get_surface("tileset.png", rect=(0, 96, 64, 64)),
            rect=rect,
            z=z,
            script="furniture",
            api={"TEXT": custom_fields["Sign"]},
        )

    def update(self, dt):
        if self.level.player.collision_rect.colliderect(self.teleport_rect):
            self.level.player.rect.top += (
                self.teleport_rect.bottom - self.level.player.collision_rect.top
            )
            self.level.switch_level(self.dest_map)
        return super().update(dt)


class Furniture(Interactable):
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

    def __init__(self, level, rect=(0, 0, 16, 16), z=0, **custom_fields):
        self.type = custom_fields["Type"]
        self.info = custom_fields["Info"]
        print("INFO", self.info)
        super().__init__(
            level,
            rect=rect,
            image=level.game.loader.get_spritesheet("tileset.png", (16, 16))[
                self.IMAGES[self.type]
            ],
            z=z,
            script="furniture",
            api={"TEXT": self.info},
        )
        self.collision_rect = self.rect.copy()
        self.collision_rect.height *= 0.7
        self.collision_rect.centery = self.rect.centery


class Bush(sprite.Sprite):
    groups = {"static-collision"}

    def __init__(self, level, rect=(0, 0, 16, 16), z=0, **custom_fields):
        super().__init__(
            level,
            level.game.loader.get_surface("tileset.png", rect=(160, 64, 16, 16)),
            rect,
            z,
        )
        self.collision_rect = self.rect.copy()


class Spikefruit(sprite.Sprite):
    groups = {"interactable"}

    def __init__(self, level, rect=(0, 0, 16, 16), z=0, **custom_fields):
        self.frames = level.game.loader.get_spritesheet("spikeberry.png", (8, 8))
        self.fruit = 2
        self.collision_rect = pygame.FRect(rect)
        super().__init__(
            level,
            self.frames[2],
            rect,
            z - 1,
        )

    def interact(self):
        if self.fruit > 0:
            self.fruit -= 1
            self.image = self.frames[self.fruit]
            self.level.player.acquire("spikefruit")
            return 0
        else:
            return None


class WaspberryBush(sprite.Sprite):
    groups = {"static-collision"}

    def __init__(self, level, rect=(0, 0, 16, 16), z=0, **custom_fields):
        super().__init__(
            level,
            level.game.loader.get_surface("waspberry-bush.png"),
            rect,
            z,
        )
        self.collision_rect = self.rect
        for _ in range(5):
            rect = pygame.FRect(self.rect.centerx + random.uniform(-6, 5), self.rect.centery + random.uniform(-5, 6), 2, 2)
            self.level.spawn("Waspberry", rect, z)


class Waspberry(sprite.Sprite):
    groups = {"interactable"}

    def __init__(self, level, rect=(0, 0, 2, 2), z=0, **custom_fields):
        self.frames = level.game.loader.get_spritesheet("waspberry.png", (2, 2))
        super().__init__(
            level,
            random.choice(self.frames),
            rect,
            z + 0.5,
        )
        self.collision_rect = self.rect.copy()

    def interact(self):
        self.dead = True
        self.level.player.acquire("waspberry")
        return 0


class Spapple(sprite.Sprite):
    groups = {"interactable"}

    def __init__(self, level, rect=(0, 0, 16, 16), z=0, **custom_fields):
        self.frames = level.game.loader.get_spritesheet("spapple.png", (16, 16))
        self.fruit = 1
        self.collision_rect = pygame.FRect(rect)
        super().__init__(
            level,
            self.frames[1],
            rect,
            z,
        )

    def interact(self):
        if self.fruit > 0:
            self.fruit -= 1
            self.image = self.frames[self.fruit]
            self.level.player.acquire("spapple")
            return 0


class Hoverboard(sprite.Sprite):
    groups = {"interactable"}

    def __init__(self, level, rect=(0, 0, 32, 32), z=0, **custom_fields):
        self.anim = Animation(
            level.game.loader.get_spritesheet("hoverboard.png", (32, 32))[:4]
        )
        self.exit_anim = Animation(
            level.game.loader.get_spritesheet("hoverboard.png", (32, 32))[4:8]
        )
        self.exiting = False
        self.exited = asyncio.Event()
        super().__init__(level, self.anim.image, rect, z - 1)

    @property
    def collision_rect(self):
        return self.rect.inflate(-16, -8)

    async def ride_off_into_sunset(self):
        self.level.player.lock()
        self.level.player.hide()
        self.anim = self.exit_anim
        self.exiting = True
        await self.exited.wait()

    def interact(self):
        self.level.run_cutscene(
            "hoverboard",
            api={
                "ride_off_into_sunset": AsyncSNEKCallable(self.ride_off_into_sunset, 0)
            },
        )

    def update(self, dt):
        self.anim.update(dt)
        self.image = self.anim.image
        if self.exiting:
            self.rect.x += 64 * dt
            if self.rect.left > self.level.map_rect.right:
                self.level.player.rect.center = self.pos
                long_name = f"{self.level.name}_right"
                x = long_name.count("right") - long_name.count("left")
                y = long_name.count("down") - long_name.count("up")
                short_name = self.level.name.split("_")[0]
                if x < 0:
                    short_name += "_left" * abs(x)
                if x > 0:
                    short_name += "_right" * x
                if y < 0:
                    short_name += "_up" * abs(y)
                if y > 0:
                    short_name += "_down" * y
                self.level.switch_level(
                    short_name, direction="right", position=self.pos
                )
                self.exited.set()
        return super().update(dt)
