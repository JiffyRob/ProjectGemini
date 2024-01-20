from collections import defaultdict

import pygame
import pygame._sdl2 as sdl2

from scripts import game_state, sprite, util_draw

GRAVITY = pygame.Vector2(0, 5)  # TODO: sideways gravity?????
WALK_SPEED = 64
JUMP_SPEED = 800
LERP_SPEED = 1


class PhysicsSprite(sprite.Sprite):
    def __init__(
        self, level, image=None, rect=(0, 0, 16, 16), src_rect=None, z=0, weight=10
    ):
        super().__init__(level, image=image, rect=rect, src_rect=src_rect, z=z)
        self.weight = weight
        self.velocity = pygame.Vector2()
        self.desired_velocity = pygame.Vector2()
        self.on_ground = False

    @property
    def collision_rect(self):
        return self.rect.copy()

    def update(self, dt):
        # physics
        self.velocity += GRAVITY * self.weight
        vel = self.velocity * dt
        self.rect.x += vel.x
        # bottom of the map
        if self.collision_rect.bottom > self.level.map_rect.bottom:
            self.dead = True
            return False
        if vel.x < 0:
            for collided in sorted(
                self.level.groups["collision"], key=lambda sprite: -sprite.rect.x
            ):
                if self.collision_rect.colliderect(collided.collision_rect):
                    self.rect.x += (
                        collided.collision_rect.right - self.collision_rect.left
                    )
                    self.velocity.x = 0
                    break
        else:
            for collided in sorted(
                self.level.groups["collision"], key=lambda sprite: sprite.rect.x
            ):
                if self.collision_rect.colliderect(collided.collision_rect):
                    self.rect.x += (
                        collided.collision_rect.left - self.collision_rect.right
                    )
                    self.velocity.x = 0
                    break
        self.rect.y += vel.y
        if vel.y < 0:
            for collided in sorted(
                self.level.groups["collision"], key=lambda sprite: -sprite.rect.y
            ):
                if self.collision_rect.colliderect(collided.collision_rect):
                    self.rect.y += (
                        collided.collision_rect.bottom - self.collision_rect.top
                    )
                    self.velocity.y = 0
                    break
        else:
            for collided in sorted(
                self.level.groups["collision"], key=lambda sprite: sprite.rect.y
            ):
                if self.collision_rect.colliderect(collided.collision_rect):
                    self.rect.y += (
                        collided.collision_rect.top - self.collision_rect.bottom
                    )
                    self.velocity.y = 0
                    self.on_ground = True
                    break
        self.velocity.x = 0
        return True


class CollisionSprite(sprite.Sprite):
    def __init__(self, level, image=None, rect=(0, 0, 16, 16), src_rect=None, z=0):
        if image is None:
            image = util_draw.square_image(level.renderer, "blue")
        super().__init__(level, image=image, rect=rect, src_rect=src_rect, z=z)
        self.level.groups["collision"].add(self)

    @property
    def collision_rect(self):
        return self.rect.copy()


class Player(PhysicsSprite):
    def __init__(self, level, rect=(0, 0, 16, 16)):
        super().__init__(level, rect=rect, image=util_draw.square_image(level.renderer))

    def walk_left(self):
        self.velocity.x -= WALK_SPEED

    def walk_right(self):
        self.velocity.x += WALK_SPEED

    def jump(self):
        if self.on_ground:
            self.velocity.y = -JUMP_SPEED
            self.on_ground = False


class Level(game_state.GameState):
    def __init__(self, game):
        super().__init__(game)
        self.groups = defaultdict(set)
        self.player = Player(self)
        self.map_rect = self.screen_rect.copy()
        self.sprites = [self.player, CollisionSprite(self, rect=(0, 200, 600, 16))]
        self.camera_offset = pygame.Vector2()

    def update(self, dt):
        super().update(dt)
        keys = pygame.key.get_pressed()
        if keys[pygame.K_LEFT]:
            self.player.walk_left()
        if keys[pygame.K_RIGHT]:
            self.player.walk_right()
        if keys[pygame.K_UP]:
            self.player.jump()
        # removes dead sprites from the list
        self.sprites = [sprite for sprite in self.sprites if sprite.update(dt)]
        self.camera_offset = self.camera_offset.lerp(
            -pygame.Vector2(self.player.pos) + self.screen_rect.center, LERP_SPEED
        )

    def draw(self):
        super().draw()
        for sprite in sorted(self.sprites, key=lambda sprite: sprite.z):
            sprite.image.draw(sprite.src_rect, sprite.rect.move(self.camera_offset))
        self.renderer.present()
