import random
import math
import numpy
from dataclasses import dataclass

import pygame

from scripts import game_state
from scripts import loader


@dataclass
class Camera:
    pos: pygame.Vector3
    rotation: pygame.Vector3
    center: pygame.Vector2
    fov: pygame.Vector2
    near_z: int
    far_z: int


class SpaceParticle:
    def __init__(self, pos, image, size):
        self.pos = pos
        self.image = image
        self.rect = pygame.Rect((-1, -1), size)
        self.width, self.height = size

class Space(game_state.GameState):
    def __init__(self, game):
        super().__init__(game, color='navy')
        self.loader = loader.TextureLoader(self.renderer)
        self.renderer.logical_size = (800, 600)
        # in world space y is vertical, and x and z are horizontal
        # on screen with no rotation x is left-right, y is up-down, and z is depth
        self.camera = Camera(
            pygame.Vector3(),
            pygame.Vector3(),
            pygame.Vector2(self.renderer.logical_size) / 2,
            pygame.Vector2(60, 60),
            200,
            500
        )
        self.sprites = []

        for i in range(3000):
            self.sprites.append(
                SpaceParticle(
                    pygame.Vector3(random.uniform(-self.renderer.logical_size[0], self.renderer.logical_size[0]),
                                   random.uniform(-self.renderer.logical_size[1], self.renderer.logical_size[1]),
                                   random.uniform(-500, 500)),
                    self.loader.get("stars", "blue4a"),
                    (16, 16)
                )
            )

    def update(self, dt):
        buttons = pygame.mouse.get_pressed()
        keys = pygame.key.get_pressed()
        for event in pygame.event.get():
            match event:
                case pygame.Event(type=pygame.QUIT):
                    self.game.quit()
                case pygame.Event(type=pygame.MOUSEMOTION, rel=motion):
                    self.camera.rotation.y += motion[0]
                    self.camera.rotation.x -= motion[1]
                    print(self.camera.rotation)
                case pygame.Event(type=pygame.MOUSEWHEEL, y=motion):
                    self.camera.rotation.z += motion * 10
        if keys[pygame.K_UP]:
            self.camera.pos.z += 100 * dt
        if keys[pygame.K_DOWN]:
            self.camera.pos.z -= 100 * dt
        if keys[pygame.K_LEFT]:
            self.camera.pos.x -= 100 * dt
        if keys[pygame.K_RIGHT]:
            self.camera.pos.x += 100 * dt
        if keys[pygame.K_SPACE]:
            self.camera.pos.y -= 100 * dt
        if keys[pygame.K_LSHIFT]:
            self.camera.pos.y += 100 * dt
        if keys[pygame.K_LCTRL]:
            self.camera.rotation *= 0
        if keys[pygame.K_ESCAPE]:
            self.game.quit()

    def draw(self):
        self.renderer.clear()
        rotation = -self.camera.rotation * math.pi / 180
        rotate_x = numpy.array((
            (1, 0, 0, 0),
            (0, math.cos(rotation.x), -math.sin(rotation.x), 0),
            (0, math.sin(rotation.x), math.cos(rotation.x), 0),
            (0, 0, 0, 1)),
            numpy.float64
        )
        rotate_y = numpy.array((
            (math.cos(rotation.y), 0, math.sin(rotation.y), 0),
            (0, 1, 0, 0),
            (-math.sin(rotation.y), 0, math.cos(rotation.y), 0),
            (0, 0, 0, 1)),
            numpy.float64
        )
        rotate_z = numpy.array((
            (math.cos(rotation.z), -math.sin(rotation.z), 0, 0),
            (math.sin(rotation.z), math.cos(rotation.z), 0, 0),
            (0, 0, 1, 0),
            (0, 0, 0, 1)),
            numpy.float64
        )
        translate = numpy.array((
            (1, 0, 0, -self.camera.pos.x),
            (0, 1, 0, -self.camera.pos.y),
            (0, 0, 1, -self.camera.pos.z),
            (0, 0, 0, 1)),
            numpy.float64
        )
        project = numpy.array((
            (self.camera.near_z, 0, 0, 0),
            (0, self.camera.near_z, 0, 0),
            (0, 0, self.camera.far_z + self.camera.near_z, -self.camera.far_z * self.camera.near_z),
            (0, 0, 1, 0)),
            numpy.float64
        )
        transformation = project @ rotate_z @ rotate_y @ rotate_x @ translate
        for sprite in self.sprites:
            new_point = tuple(transformation @ numpy.array((*sprite.pos, 1), numpy.float64))
            new_point = pygame.Vector3(new_point[0], new_point[1], new_point[2]) / new_point[3]
            scale_factor = self.camera.near_z / new_point.z
            sprite.rect.width = sprite.width * scale_factor
            sprite.rect.height = sprite.height * scale_factor
            sprite.rect.center = new_point.xy + self.camera.center
            if self.camera.near_z <= new_point[2] <= self.camera.far_z:
                self.renderer.blit(sprite.image, sprite.rect)
        self.renderer.present()