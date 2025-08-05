from math import sin
from typing import Any

import pygame
from pygame.typing import RectLike

from gamelibs import easings, sprite, timer, interfaces, hardware
from gamelibs.animation import Animation, flip_surface

GRAVITY = pygame.Vector2(0, 50)  # TODO: sideways gravity?????
ACCEL_SPEED = 6
DECCEL_SPEED = 6
WALK_SPEED = 84
MAX_X_SPEED = 256
MAX_Y_SPEED = 256
JUMP_SPEED = 240


class PhysicsSprite(sprite.Sprite, interfaces.PlatformerSprite, interfaces.Collider):
    def __init__(
        self,
        level: interfaces.PlatformerLevel,
        image: pygame.Surface | None = None,
        rect: RectLike = (0, 0, 16, 16),
        z: int = 0,
        weight: float = 10,
        **_: Any
    ) -> None:
        super().__init__(level, image=image, rect=rect, z=z)
        self.weight: float = weight
        self.velocity: pygame.Vector2 = pygame.Vector2()
        self.desired_velocity = pygame.Vector2()
        self.on_ground: bool = False
        self.on_downer: bool = False
        self.ducking: bool = False
        self.ground_rect_relative: pygame.Vector2 | None = None
        self.ground_rect: interfaces.MiscRect | None = None

    @property
    def collision_rect(self) -> interfaces.MiscRect:
        return self.rect.copy()

    def get_player(self) -> interfaces.PlatformerPlayer:
        return super().get_player()  # type: ignore

    def get_level(self) -> interfaces.PlatformerLevel:
        return self._level  # type: ignore

    def on_xy_collision(self, direction: interfaces.Direction) -> None:
        pass

    def on_fallout(self) -> None:
        pass

    def update(self, dt: float, *, physics: bool = True) -> bool:
        # physics
        # moving platforms
        if physics:
            if self.ground_rect:
                self.rect.center = self.ground_rect.center + self.ground_rect_relative  # type: ignore
            self.ground_rect = None
            self.ground_rect_relative = None
            # lock velocity
            self.velocity.x = pygame.math.clamp(
                self.velocity.x, -MAX_X_SPEED, MAX_X_SPEED
            )
            self.velocity.y = pygame.math.clamp(
                self.velocity.y, -MAX_Y_SPEED, MAX_Y_SPEED
            )
            # locked sprites do not move
            if self.locked:
                self.velocity.x *= 0
            old_rect = self.collision_rect.copy()
            vel = self.velocity * dt + 0.5 * GRAVITY * self.weight * dt**2
            self.velocity += GRAVITY * self.weight * dt
            self.rect.x += vel.x
            self.on_ground = False
            # bottom of the map
            if self.collision_rect.top > self.get_level().map_rect.bottom:
                self.on_fallout()
                return False
            if vel.x < 0:
                for collided in sorted(
                    self.get_level().get_rects("collision"), key=lambda rect: -(rect.x)
                ):
                    if self.collision_rect.colliderect(collided):
                        self.on_xy_collision(interfaces.Direction.LEFT)
                        self.rect.x += collided.right - self.collision_rect.left
                        self.velocity.x = 0
                        break
            else:
                for collided in sorted(
                    self.get_level().get_rects("collision"), key=lambda rect: rect.x
                ):
                    if self.collision_rect.colliderect(collided):
                        self.on_xy_collision(interfaces.Direction.RIGHT)
                        self.rect.x += collided.left - self.collision_rect.right
                        self.velocity.x = 0
                        break
            self.rect.y += vel.y
            if vel.y < 0:
                for collided in sorted(
                    self.get_level().get_rects("collision"), key=lambda rect: -rect.y
                ):
                    if self.collision_rect.colliderect(collided):
                        self.on_xy_collision(interfaces.Direction.UP)
                        self.rect.y += collided.bottom - self.collision_rect.top
                        self.velocity.y = 0
                        break
            else:
                if not self.ducking:
                    for collided in sorted(
                        self.get_level().get_rects("platform"), key=lambda rect: rect.y
                    ):
                        if (
                            old_rect.bottom <= collided.top
                            and self.collision_rect.colliderect(collided)
                        ):
                            self.on_xy_collision(interfaces.Direction.DOWN)
                            self.rect.y += collided.top - self.collision_rect.bottom
                            self.velocity.y = 0
                            self.on_ground = True
                            self.on_downer = True
                            self.ground_rect = collided
                            self.ground_rect_relative = (
                                self.pos - self.ground_rect.center
                            )
                            break
                for collided in sorted(
                    self.get_level().get_rects("collision"), key=lambda rect: rect.y
                ):
                    if self.collision_rect.colliderect(collided):
                        self.on_xy_collision(interfaces.Direction.DOWN)
                        self.rect.y += collided.top - self.collision_rect.bottom
                        self.velocity.y = 0
                        self.on_ground = True
                        self.ground_rect = collided
                        self.ground_rect_relative = self.pos - self.ground_rect.center
                        break
            self.ducking = False
        return super().update(dt)


class Ship(sprite.Sprite):
    SHIPS = {
        "ford": (0, 80, 48, 32),
    }

    def __init__(
        self,
        level: interfaces.PlatformerLevel,
        rect: RectLike = (0, 0, 48, 32),
        z: int = 0,
        **custom_fields: Any
    ) -> None:
        ship_image = hardware.loader.get_surface(
            "platformer-sprites.png", self.SHIPS[custom_fields["ship_type"]]  # type: ignore
        )
        super().__init__(level, ship_image, rect, z)
        self.start = pygame.Vector2(custom_fields["start"])  # type: ignore
        self.dest = pygame.Vector2(custom_fields["dest"])  # type: ignore
        self.duration: float = custom_fields.get("duration", 4)  # type: ignore
        self.age = 0.0

    def update(self, dt: float) -> bool:
        self.age += dt
        if self.age <= self.duration:
            self.rect.center = self.start.lerp(
                self.dest,
                pygame.math.clamp(easings.in_out_cubic(self.age / self.duration), 0, 1),
            )
        else:
            self.rect.center = self.dest + (0, 1.5 * sin(self.age * 3))
        return super().update(dt)


class BoingerBeetle(PhysicsSprite):
    def __init__(
        self,
        level: interfaces.PlatformerLevel,
        rect: RectLike = (0, 0, 16, 16),
        z: int = 0,
        **custom_fields: Any
    ) -> None:
        super().__init__(level, rect=rect, weight=3, z=z)
        self.anim = Animation(
            hardware.loader.get_spritesheet("platformer-sprites.png")[8:12],
            0.15,
        )
        self.hit_image = hardware.loader.get_spritesheet("platformer-sprites.png")[12]
        self.moving = custom_fields["moving"]
        self.hit_wait = 0.2
        self.hit_timer = 0
        self.facing_left = True
        self.image = self.anim.image
        self.hop_timer = timer.Timer(1000, self.hop, True)

    def on_xy_collision(self, direction: interfaces.Direction) -> None:
        if direction in {interfaces.Direction.RIGHT, interfaces.Direction.LEFT}:
            self.facing_left = not self.facing_left

    @property
    def collision_rect(self) -> interfaces.MiscRect:
        rect = self.rect.inflate(-4, -10).move(0, 5)
        rect.center = self.rect.center
        rect.top = self.rect.top + 5
        return rect

    def hop(self) -> None:
        if not self.moving:
            self.velocity.y = -JUMP_SPEED * 0.1

    def update(self, dt: float) -> bool:  # type: ignore
        self.hop_timer.update()
        if self.moving:
            self.velocity.x = WALK_SPEED * 0.3 * (-1 + self.facing_left * 2)
        self.anim.flip_x = self.facing_left
        if (
            self.collision_rect.colliderect(self.get_player().collision_rect)
            and self.get_player().facing == interfaces.Direction.RIGHT
        ):
            self.image = flip_surface(self.hit_image, self.anim.flip_x, False)
            self.hit_timer = self.hit_wait
            self.get_player().jump(interfaces.JumpCause.BOOSTED)
        if self.hit_timer > 0:
            self.hit_timer -= dt
        else:
            self.image = self.anim.image
        return super().update(dt)
