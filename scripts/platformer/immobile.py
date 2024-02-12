import random
from itertools import cycle
from math import sin

from scripts import sprite, util_draw


class Emerald(sprite.Sprite):
    def __init__(self, level, rect=(0, 0, 16, 16)):
        super().__init__(level, image=None, rect=rect, src_rect=None, z=0)
        self.anim_speed = 0.08
        self.anim_time = 0
        self.anim = cycle(
            self.level.game.loader.get_spritesheet("platformer-sprites.png")[0:5]
        )
        self.age = random.randint(0, 10)
        self.y = self.rect.top
        self.collision_rect = self.rect.inflate(-8, -4)

    def update(self, dt):
        if not super().update(dt):
            return False
        if self.collision_rect.colliderect(self.level.player.collision_rect):
            return False
        self.anim_time += dt
        if self.anim_time >= self.anim_speed:
            self.anim_time = 0
            self.image = next(self.anim)
        self.rect.top = self.y + 1.5 * sin(self.age * 2)
        self.age += dt
        return True


class BustedParts(sprite.Sprite):
    def __init__(self, level, rect=(0, 0, 16, 16)):
        super().__init__(level, image=None, rect=rect, src_rect=None, z=0)
        self.anim_speed = 0.2
        self.anim_time = 0
        self.anim = cycle(
            self.level.game.loader.get_spritesheet("platformer-sprites.png")[16:20]
        )
        self.hit_image = self.level.game.loader.get_spritesheet("platformer-sprites.png")[20]
        self.collision_rect = self.rect.inflate(-2, -12)
        self.collision_rect.bottom = self.rect.bottom

    def update(self, dt):
        if not super().update(dt):
            return False
        if self.collision_rect.colliderect(self.level.player.collision_rect):
            self.image = self.hit_image
            self.anim_time = 0
            self.level.player.jump(True, .7)
        self.anim_time += dt
        if self.anim_time >= self.anim_speed:
            self.anim_time = 0
            self.image = next(self.anim)
        return True


class CollisionSprite(sprite.Sprite):
    def __init__(self, level, image=None, rect=(0, 0, 16, 16), src_rect=None, z=0):
        if image is None:
            image = util_draw.square_image(level.game.renderer, "blue")
        super().__init__(level, image=image, rect=rect, src_rect=src_rect, z=z)
        # self.level.groups["collision"].add(self)
        self.level.collision_rects.add(self.collision_rect)

    def update(self, dt):
        pass  # No physics on a static sprite

    @property
    def collision_rect(self):
        return self.rect.copy()

