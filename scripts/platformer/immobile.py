import random
from math import sin

import pygame

from scripts import sprite
from scripts.animation import Animation


class Emerald(sprite.Sprite):
    def __init__(self, level, rect=(0, 0, 16, 16), z=0, **custom_fields):
        super().__init__(level, image=None, rect=rect, z=z)
        self.anim = Animation(
            self.level.game.loader.get_spritesheet("platformer-sprites.png")[0:5], 0.08
        )
        self.age = random.randint(0, 10)
        self.y = self.rect.top
        self.collision_rect = self.rect.inflate(-8, -4)

    def update(self, dt):
        if not super().update(dt):
            return False
        if self.collision_rect.colliderect(self.level.player.collision_rect):
            self.level.player.pay(5)
            return False
        self.anim.update(dt)
        self.image = self.anim.image
        self.rect.top = self.y + 1.5 * sin(self.age * 2)
        self.age += dt
        return True


class Prop(sprite.Sprite):
    FIRST = 13
    LAST = 15
    SPEED = 0.6

    def __init__(self, level, rect=(0, 0, 16, 16), z=0, **custom_fields):
        super().__init__(level, image=None, rect=rect, z=z)
        self.anim = Animation(
            level.game.loader.get_spritesheet("platformer-sprites.png")[
                self.FIRST : self.LAST
            ],
            self.SPEED,
        )
        # util_draw.debug_show(self.anim.image)

    def update(self, dt):
        super().update(dt)
        self.anim.update(dt)
        self.image = self.anim.image
        return True


class BrownShroom(Prop):
    FIRST = 21
    LAST = 23


class BustedParts(sprite.Sprite):
    def __init__(self, level, rect=(0, 0, 16, 16), z=0, **custom_fields):
        super().__init__(level, image=None, rect=rect, z=z)
        self.anim = Animation(
            self.level.game.loader.get_spritesheet("platformer-sprites.png")[16:20]
        )
        self.hit_image = self.level.game.loader.get_spritesheet(
            "platformer-sprites.png"
        )[20]
        self.hit_time = 0
        self.hit_wait = 0.2
        self.collision_rect = self.rect.inflate(-2, -12)
        self.collision_rect.bottom = self.rect.bottom

    def update(self, dt):
        if not super().update(dt):
            return False
        self.anim.update(dt)
        if self.collision_rect.colliderect(self.level.player.collision_rect):
            self.image = self.hit_image
            self.hit_time = 0.2
            self.level.player.jump(True, 0.7)
            self.level.player.hurt(2)
        if self.hit_time > 0:
            self.hit_time -= dt
        else:
            self.image = self.anim.image
        return True


class CollisionSprite(sprite.Sprite):
    def __init__(self, level, image=None, rect=(0, 0, 16, 16), z=0, **custom_fields):
        if image is None:
            image = pygame.Surface(rect[2:]).convert_alpha()
        super().__init__(level, image=image, rect=rect, z=z)
        # self.level.groups["collision"].add(self)
        self.level.collision_rects.add(self.collision_rect)

    def update(self, dt):
        pass  # No physics on a static sprite

    @property
    def collision_rect(self):
        return self.rect.copy()
