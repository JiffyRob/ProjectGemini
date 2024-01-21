import functools
import pathlib
from collections import defaultdict

import pygame
import pygame._sdl2 as sdl2

from scripts import game_state, sprite, util_draw

GRAVITY = pygame.Vector2(0, 2)  # TODO: sideways gravity?????
WALK_SPEED = 64
JUMP_SPEED = 400
LERP_SPEED = .3


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
                self.level.collision_rects, key=lambda rect: -rect.x
            ):
                if self.collision_rect.colliderect(collided):
                    self.rect.x += (
                        collided.right - self.collision_rect.left
                    )
                    self.velocity.x = 0
                    break
        else:
            for collided in sorted(
                self.level.collision_rects, key=lambda rect: rect.x
            ):
                if self.collision_rect.colliderect(collided):
                    self.rect.x += (
                        collided.left - self.collision_rect.right
                    )
                    self.velocity.x = 0
                    break
        self.rect.y += vel.y
        if vel.y < 0:
            for collided in sorted(
                self.level.collision_rects, key=lambda rect: -rect.y
            ):
                if self.collision_rect.colliderect(collided):
                    self.rect.y += (
                        collided.bottom - self.collision_rect.top
                    )
                    self.velocity.y = 0
                    break
        else:
            for collided in sorted(
                self.level.collision_rects, key=lambda rect: rect.y
            ):
                if self.collision_rect.colliderect(collided):
                    self.rect.y += (
                        collided.top - self.collision_rect.bottom
                    )
                    self.velocity.y = 0
                    self.on_ground = True
                    break
        self.velocity.x = 0
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


class Player(PhysicsSprite):
    def __init__(self, level, rect=(0, 0, 16, 16)):
        super().__init__(
            level, rect=rect, image=util_draw.square_image(level.game.renderer)
        )

    def walk_left(self):
        self.velocity.x -= WALK_SPEED

    def walk_right(self):
        self.velocity.x += WALK_SPEED

    def jump(self):
        if self.on_ground:
            self.velocity.y = -JUMP_SPEED
            self.on_ground = False


class Level(game_state.GameState):
    sprite_classes = {
        "Coin2": None,
    }

    def __init__(self, game, player_pos=(0, 0), map_size=(256, 256)):
        super().__init__(game)
        self.groups = defaultdict(set)
        self.player = Player(self)
        self.player.rect.center = player_pos
        self.sprites = [self.player]
        self.collision_rects = []
        self.map_rect = pygame.Rect((0, 0), map_size)
        self.camera_offset = pygame.Vector2()

    def add_sprite(self, sprite):
        self.sprites.append(sprite)

    @classmethod
    @functools.cache
    def load(cls, game, name):
        folder = pathlib.Path("ldtk/simplified", name)
        data = game.loader.get_json(folder / "data.json")
        size = data["width"], data["height"]
        map_rect = pygame.Rect((0, 0), size)
        entity_layer = data["customFields"]["entity_layer"]
        level = cls(game, player_pos=data["customFields"]["start"], map_size=size)
        for layer_ind, layer in enumerate(data["layers"]):
            level.add_sprite(
                sprite.Sprite(level, game.loader.get_texture(folder / layer), pygame.FRect(map_rect), z=layer_ind)
            )
        for key, value in data["entities"].items():
            sprite_cls = cls.sprite_classes[key]
            if sprite_cls is None:
                continue
            # TODO: Sprite creation
            ...

        for row, line in enumerate(game.loader.get_csv(folder / "Collision.csv")):
            for col, value in enumerate(line):
                value = int(value)
                if value == 1:
                    rect = pygame.FRect(col * 16, row * 16, 16, 16)
                    print(rect)
                    level.collision_rects.append(rect)
        level.player.z = entity_layer
        return level

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
