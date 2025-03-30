import math

import pygame

from gamelibs import easings, sprite, timer, projectile
from gamelibs.animation import NoLoopAnimation, SingleAnimation


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
        "vertical-collision",
    }
    STATE_OFF = 1
    STATE_MOVING = 2
    STATE_ARRIVED = 3
    STATE_SHOOTING = 4

    def __init__(self, level, rect, z, **custom_fields):
        super().__init__(level, None, rect, z - 1)
        self.collision_rect = self.rect
        on_frame, *shoot_frames, off_frame = level.game.loader.get_spritesheet(
            "platformer-sprites.png", (32, 8)
        )[24:29]
        self.facing_left = custom_fields["facing_left"]
        self.anim_dict = {
            self.STATE_OFF: SingleAnimation(off_frame, self.facing_left),
            self.STATE_MOVING: SingleAnimation(on_frame, self.facing_left),
            self.STATE_ARRIVED: SingleAnimation(on_frame, self.facing_left),
            self.STATE_SHOOTING: NoLoopAnimation(shoot_frames, 0.1, self.facing_left),
        }
        self.state = self.STATE_OFF
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
            self.shoot_direction = pygame.Vector2(-128, 0)
            self.shoot_start = pygame.Vector2(-2, 4)
        else:
            self.shoot_direction = pygame.Vector2(128, 0)
            self.shoot_start = pygame.Vector2(self.rect.width + 2, 4)

    def shoot(self):
        if self.state == self.STATE_ARRIVED:
            self.state = self.STATE_SHOOTING
            self.anim_dict[self.state].restart()

    def update(self, dt):
        if not self.locked:
            self.shoot_timer.update(dt)
            for trigger in self.triggers:
                triggered = False
                for sprite in self.level.groups[trigger]:
                    if sprite.triggered():
                        triggered = True
                    else:
                        triggered = False
                        break
                if triggered and self.state == self.STATE_OFF:
                    self.state = self.STATE_MOVING
            circle_offset = (
                math.cos(self.angle * math.pi / 180) * self.radius,
                math.sin(self.angle * math.pi / 180) * self.radius,
            )
            if self.state == self.STATE_MOVING:
                self.dest_dt += dt
                self.rect.center = self.start.lerp(
                    self.dest + circle_offset, easings.out_quint(min(self.dest_dt, 1))
                )
                if self.dest_dt > 1:
                    self.state = self.STATE_ARRIVED
            if self.state in {self.STATE_ARRIVED, self.STATE_SHOOTING}:
                self.angle += dt * self.rotation_speed
                self.angle %= 360
                self.rect.center = self.dest + circle_offset
            if (
                self.state == self.STATE_ARRIVED
                and ((self.rect.topleft + self.shoot_start).y - self.level.player.pos.y)
                < 8
                and self.shoot_timer.done()
            ):
                self.shoot()
                self.shoot_timer.reset()
            if self.state == self.STATE_SHOOTING and self.anim_dict[self.state].done():
                self.level.add_sprite(
                    projectile.Laser(
                        self.level,
                        pygame.Rect(self.rect.topleft + self.shoot_start, (4, 1)),
                        self.z,
                        self.shoot_direction,
                    )
                )
                self.state = self.STATE_ARRIVED
            self.anim_dict[self.state].update(dt)
            self.image = self.anim_dict[self.state].image
        return super().update(dt)
