import pygame

from scripts import sprite
from scripts.platformer import immobile, mobile


class Battery(sprite.Sprite):
    groups = {"time-reversable", "vertical-collision"}
    STATE_BROKEN = 1
    STATE_FIXED = 2

    def __init__(self, level, rect, z, **custom_fields):
        frames = level.game.loader.get_spritesheet("platformer-sprites.png", (16, 16))
        self.anim_dict = {
            self.STATE_BROKEN: frames[32],
            self.STATE_FIXED: frames[33],
        }
        self.state = self.STATE_BROKEN
        if custom_fields.get("trigger_id"):
            self.groups = self.__class__.groups | {custom_fields["trigger_id"]}
        rect = pygame.FRect(rect)
        self.collision_rect = pygame.Rect(
            rect.left, rect.centery, rect.width, rect.height / 2
        )
        self.time_reverse_collision_rect = rect
        super().__init__(level, self.anim_dict[self.state], rect, z - 1)

    def update(self, dt):
        super().update(dt)
        self.image = self.anim_dict[self.state]
        return True

    def triggered(self):
        return self.state == self.STATE_FIXED

    def reverse_time(self):
        self.state = self.STATE_FIXED


class GunPlatform(sprite.Sprite):
    groups = {
        "static-collision",
    }
    STATE_OFF = 1
    STATE_ON = 2
    STATE_SHOOTING = 3

    def __init__(self, level, rect, z, **custom_fields):
        on_frame, *shoot_frames, off_frame = level.game.loader.get_spritesheet(
            "platformer-sprites.png", (32, 8)
        )[24:29]
        self.state = None
