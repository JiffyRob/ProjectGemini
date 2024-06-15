from itertools import cycle

import pygame

from scripts import sprite, timer
from scripts.animation import Animation, flip_surface

GRAVITY = pygame.Vector2(0, 50)  # TODO: sideways gravity?????
ACCEL_SPEED = 6
DECCEL_SPEED = 6
WALK_SPEED = 84
MAX_X_SPEED = 256
MAX_Y_SPEED = 256
JUMP_SPEED = 240


class PhysicsSprite(sprite.Sprite):
    DIRECTION_UP = 1
    DIRECTION_DOWN = 2
    DIRECTION_LEFT = 3
    DIRECTION_RIGHT = 4

    def __init__(
        self, level, image=None, rect=(0, 0, 16, 16), z=0, weight=10, **custom_fields
    ):
        super().__init__(level, image=image, rect=rect, z=z)
        self.collision_rect = self.rect
        self.weight = weight
        self.velocity = pygame.Vector2()
        self.desired_velocity = pygame.Vector2()
        self.on_ground = False
        self.on_downer = False
        self.ducking = False
        self.ground_rect_relative = pygame.Vector2()
        self.ground_rect = None

    def on_xy_collision(self, direction):
        pass

    def on_fallout(self):
        pass

    def update_rects(self):
        self.collision_rect = self.rect

    def update(self, dt):
        if not super().update(dt):
            return False
        # physics
        # moving platforms
        if self.ground_rect:
            self.rect.center = self.ground_rect.center + self.ground_rect_relative
            self.update_rects()
        self.ground_rect = None
        self.ground_rect_relative = None
        # lock velocity
        self.velocity.x = pygame.math.clamp(self.velocity.x, -MAX_X_SPEED, MAX_X_SPEED)
        self.velocity.y = pygame.math.clamp(self.velocity.y, -MAX_Y_SPEED, MAX_Y_SPEED)
        # locked sprites do not move
        if self.locked:
            self.velocity.x *= 0
        old_rect = self.collision_rect.copy()
        vel = self.velocity * dt + 0.5 * GRAVITY * self.weight * dt**2
        self.velocity += GRAVITY * self.weight * dt
        self.rect.x += vel.x
        self.update_rects()
        # bottom of the map
        if self.collision_rect.top > self.level.map_rect.bottom:
            self.on_fallout()
            return False
        if vel.x < 0:
            for collided in sorted(
                self.level.collision_rects, key=lambda rect: -rect.x
            ):
                if self.collision_rect.colliderect(collided):
                    self.on_xy_collision(self.DIRECTION_LEFT)
                    self.rect.x += collided.right - self.collision_rect.left
                    self.velocity.x = 0
                    self.update_rects()
                    break
        else:
            for collided in sorted(self.level.collision_rects, key=lambda rect: rect.x):
                if self.collision_rect.colliderect(collided):
                    self.on_xy_collision(self.DIRECTION_RIGHT)
                    self.rect.x += collided.left - self.collision_rect.right
                    self.velocity.x = 0
                    self.update_rects()
                    break
        self.rect.y += vel.y
        self.update_rects()
        if vel.y < 0:
            for collided in sorted(
                self.level.collision_rects, key=lambda rect: -rect.y
            ):
                if self.collision_rect.colliderect(collided):
                    self.on_xy_collision(self.DIRECTION_UP)
                    self.rect.y += collided.bottom - self.collision_rect.top
                    self.velocity.y = 0
                    self.update_rects()
                    break
        else:
            for collided in sorted(self.level.collision_rects, key=lambda rect: rect.y):
                if self.collision_rect.colliderect(collided):
                    self.on_xy_collision(self.DIRECTION_DOWN)
                    self.rect.y += collided.top - self.collision_rect.bottom
                    self.velocity.y = 0
                    self.on_ground = True
                    self.ground_rect = collided
                    self.ground_rect_relative = self.pos - self.ground_rect.center
                    self.update_rects()
                    break
            if not self.ducking:
                for collided in sorted(self.level.down_rects, key=lambda rect: rect.y):
                    if (
                        old_rect.bottom <= collided.top
                        and self.collision_rect.colliderect(collided)
                    ):
                        self.on_xy_collision(self.DIRECTION_DOWN)
                        self.rect.y += collided.top - self.collision_rect.bottom
                        self.velocity.y = 0
                        self.on_ground = True
                        self.on_downer = True
                        self.ground_rect = collided
                        self.ground_rect_relative = self.pos - self.ground_rect.center
                        self.update_rects()
                        break
        self.ducking = False
        return True


class BoingerBeetle(PhysicsSprite):
    def __init__(self, level, rect=(0, 0, 16, 16), z=0, **custom_fields):
        super().__init__(level, rect=rect, weight=3, z=z)
        self.collision_rect = self.rect.inflate(-4, -10).move(0, 5)
        self.anim = Animation(
            self.level.game.loader.get_spritesheet("platformer-sprites.png")[8:12],
            0.15,
        )
        self.hit_image = self.level.game.loader.get_spritesheet(
            "platformer-sprites.png"
        )[12]
        self.moving = custom_fields["moving"]
        self.hit_wait = 0.2
        self.hit_timer = 0
        self.facing_left = True
        self.image = self.anim.image
        self.hop_timer = timer.Timer(1000, self.hop, True)

    def on_xy_collision(self, direction):
        if direction in {self.DIRECTION_RIGHT, self.DIRECTION_LEFT}:
            self.facing_left = not self.facing_left

    def update_rects(self):
        self.collision_rect.center = self.rect.center
        self.collision_rect.top += 5

    def hop(self):
        if not self.moving:
            self.velocity.y = -JUMP_SPEED * 0.1

    def update(self, dt):
        self.hop_timer.update()
        if self.moving:
            self.velocity.x = WALK_SPEED * 0.3 * (-1 + self.facing_left * 2)
        self.anim.flip_x = self.facing_left
        if not super().update(dt):
            return False
        if (
            self.collision_rect.colliderect(self.level.player.collision_rect)
            and self.level.player.velocity.y > 0
        ):
            self.image = flip_surface(self.hit_image, self.anim.flip_x, False)
            self.hit_timer = self.hit_wait
            self.level.player.jump(self.level.player.JUMP_BOOSTED)
        if self.hit_timer > 0:
            self.hit_timer -= dt
        else:
            self.image = self.anim.image
        return True
