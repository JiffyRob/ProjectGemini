import math
import random
from dataclasses import dataclass

import numpy
import pygame

from scripts import game_state, loader, math3d


@dataclass
class Camera:
    pos: pygame.Vector3
    rotation: math3d.Quaternion
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
        super().__init__(game, color="navy")
        self.loader = loader.TextureLoader(self.renderer)
        self.renderer.logical_size = (800, 600)
        # in world space y is vertical, and x and z are horizontal
        # on screen with no rotation x is left-right, y is up-down, and z is depth
        self.camera = Camera(
            pygame.Vector3(),
            math3d.Quaternion(),
            pygame.Vector2(self.renderer.logical_size) / 2,
            pygame.Vector2(60, 60),
            200,
            500,
        )
        self.sprites = []

        for i in range(3000):
            self.sprites.append(
                SpaceParticle(
                    pygame.Vector3(
                        random.uniform(
                            -self.renderer.logical_size[0],
                            self.renderer.logical_size[0],
                        ),
                        random.uniform(
                            -self.renderer.logical_size[1],
                            self.renderer.logical_size[1],
                        ),
                        random.uniform(-500, 500),
                    ),
                    self.loader.get("stars", "blue4a"),
                    (16, 16),
                )
            )

    def update(self, dt):
        buttons = pygame.mouse.get_pressed()
        keys = pygame.key.get_pressed()
        for event in pygame.event.get():
            match event:
                case pygame.Event(type=pygame.QUIT):
                    self.game.quit()
                case pygame.Event(type=pygame.MOUSEMOTION, rel=motion) if buttons[0]:
                    self.camera.rotation *= math3d.Quaternion(-motion[0] * dt / 30, (0, 1, 0)) * math3d.Quaternion(motion[1] * dt / 30, (1, 0, 0))
                case pygame.Event(type=pygame.MOUSEWHEEL, y=motion):
                    rotation = math3d.Quaternion(motion * dt, (0, 0, 1))
                    print(rotation)
                    self.camera.rotation *= rotation
                    pass
        motion = pygame.Vector3()
        if keys[pygame.K_UP]:
            motion.z += 100 * dt
        if keys[pygame.K_DOWN]:
            motion.z -= 100 * dt
        if keys[pygame.K_LEFT]:
            motion.x -= 100 * dt
        if keys[pygame.K_RIGHT]:
            motion.x += 100 * dt
        if keys[pygame.K_SPACE]:
            motion.y -= 100 * dt
        if keys[pygame.K_LSHIFT]:
            motion.y += 100 * dt
        if keys[pygame.K_LCTRL]:
            self.camera.rotation = math3d.Quaternion()
        self.camera.pos += self.camera.rotation * motion
        if keys[pygame.K_ESCAPE]:
            self.game.quit()
        self.game.window.title = f"FPS: {round(self.game.clock.get_fps())} ROTATION: {self.camera.rotation}"

    def draw(self):
        self.renderer.clear()
        projection_matrix = numpy.array(
            (
                (self.camera.near_z, 0, 0, 0),
                (0, self.camera.near_z, 0, 0),
                (
                    0,
                    0,
                    self.camera.far_z + self.camera.near_z,
                    -self.camera.far_z * self.camera.near_z,
                ),
                (0, 0, 1, 0),
            ),
            numpy.float64,
        )
        for sprite in self.sprites:
            # TODO: Proper FOV??
            # translate and rotate (relative position * relative rotation)
            relative_pos = -self.camera.rotation * (sprite.pos - self.camera.pos)
            # scale (cheating)
            scale_factor = self.camera.near_z / relative_pos.z
            sprite.rect.width = sprite.width * scale_factor
            sprite.rect.height = sprite.height * scale_factor
            # project
            screen_pos = math3d.to_simple(projection_matrix @ math3d.to_homogenous(relative_pos))
            # draw
            if self.camera.near_z <= screen_pos[2] <= self.camera.far_z:
                sprite.rect.center = screen_pos.xy + self.camera.center
                self.renderer.blit(sprite.image, sprite.rect)
        self.renderer.present()
