import math
from typing import Any
from enum import Enum, auto

import pygame
from pygame.typing import RectLike

from gamelibs import easings, sprite, timer, projectile, interfaces, hardware
from gamelibs.animation import NoLoopAnimation, SingleAnimation


class Battery(sprite.Sprite, interfaces.PuzzleTrigger):
    groups = {"time-reversable", "vertical-collision"}
    STATE_BROKEN = 1
    STATE_FIXED = 2

    def __init__(
        self,
        level: interfaces.PlatformerLevel,
        rect: RectLike,
        z: int,
        **custom_fields: Any
    ) -> None:
        frames = hardware.loader.get_spritesheet("platformer-sprites.png", (16, 16))
        self.anim_dict = {
            self.STATE_BROKEN: frames[32],
            self.STATE_FIXED: frames[33],
        }
        self.state = self.STATE_BROKEN
        if custom_fields.get("trigger_id"):
            self.groups = self.__class__.groups | {custom_fields["trigger_id"]}
        rect = pygame.FRect(rect)
        self.time_reverse_collision_rect = rect
        self._collision_rect = pygame.Rect(
            rect.left, rect.centery, rect.width, rect.height / 2
        )
        super().__init__(level, self.anim_dict[self.state], rect, z - 1)

    @property
    def collision_rect(self) -> interfaces.MiscRect:
        return self._collision_rect

    def update(self, dt: float) -> bool:
        super().update(dt)
        self.image = self.anim_dict[self.state]
        return True

    def triggered(self) -> bool:
        return self.state == self.STATE_FIXED

    def reverse_time(self) -> None:
        self.state = self.STATE_FIXED


class GunPlatform(sprite.Sprite):
    groups = {
        "vertical-collision",
    }

    class State(Enum):
        OFF = auto()
        MOVING = auto()
        ARRIVED = auto()
        SHOOTING = auto()

    def __init__(
        self,
        level: interfaces.PlatformerLevel,
        rect: RectLike,
        z: int,
        **custom_fields: Any
    ) -> None:
        super().__init__(level, None, rect, z - 1)
        self.collision_rect = self.rect
        on_frame, *shoot_frames, off_frame = hardware.loader.get_spritesheet(
            "platformer-sprites.png", (32, 8)
        )[24:29]
        self.facing_left = custom_fields["facing_left"]
        self.anim_dict: dict[GunPlatform.State, interfaces.Animation] = {
            self.State.OFF: SingleAnimation(off_frame, self.facing_left),
            self.State.MOVING: SingleAnimation(on_frame, self.facing_left),
            self.State.ARRIVED: SingleAnimation(on_frame, self.facing_left),
            self.State.SHOOTING: NoLoopAnimation(shoot_frames, 0.1, self.facing_left),
        }
        self.state: GunPlatform.State = self.State.OFF
        self.triggers = custom_fields["triggers"]
        self.start = pygame.Vector2(self.pos)
        self.rotation_speed = 100
        self.angle = custom_fields["angle"]
        self.radius = 48
        self.dest = pygame.Vector2(
            custom_fields["dest"]["cx"] * 16 + 8, custom_fields["dest"]["cy"] * 16 + 8
        )
        self.dest_dt = 0
        self.shoot_timer = timer.DTimer(2000)
        if self.facing_left:
            self.shoot_direction = interfaces.Direction.LEFT
            self.shoot_start = pygame.Vector2(-2, 4)
        else:
            self.shoot_direction = interfaces.Direction.RIGHT
            self.shoot_start = pygame.Vector2(self.rect.width + 2, 4)

    def shoot(self) -> None:
        if self.state == self.State.ARRIVED:
            self.state = self.State.SHOOTING
            self.anim_dict[self.state].restart()

    def update(self, dt: float) -> bool:
        if not self.locked:
            self.shoot_timer.update(dt)
            for trigger in self.triggers:
                triggered = False
                for sprite in self.get_level().get_group(trigger):
                    if sprite.triggered():  # type: ignore
                        triggered = True
                    else:
                        triggered = False
                        break
                if triggered and self.state == self.State.OFF:
                    self.state = self.State.MOVING
            circle_offset = (
                math.cos(self.angle * math.pi / 180) * self.radius,
                math.sin(self.angle * math.pi / 180) * self.radius,
            )
            if self.state == self.State.MOVING:
                self.dest_dt += dt
                self.rect.center = self.start.lerp(
                    self.dest + circle_offset, easings.out_quint(min(self.dest_dt, 1))
                )
                if self.dest_dt > 1:
                    self.state = self.State.ARRIVED
            if self.state in {self.State.ARRIVED, self.State.SHOOTING}:
                self.angle += dt * self.rotation_speed
                self.angle %= 360
                self.rect.center = self.dest + circle_offset
            if (
                self.state == self.State.ARRIVED
                and ((self.rect.topleft + self.shoot_start).y - self.get_player().pos.y)
                < 8
                and self.shoot_timer.done()
            ):
                self.shoot()
                self.shoot_timer.reset()
            if self.state == self.State.SHOOTING and self.anim_dict[self.state].done():
                self.get_level().add_sprite(
                    projectile.Laser(
                        self.get_level(),
                        self.shoot_start,
                        self.z,
                        self.shoot_direction,
                    )
                )
                self.state = self.State.ARRIVED
            self.anim_dict[self.state].update(dt)
            self.image = self.anim_dict[self.state].image
        return super().update(dt)
