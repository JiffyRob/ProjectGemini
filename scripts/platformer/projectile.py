import pygame

from scripts import sprite
from scripts.animation import Animation, SingleAnimation


class Laser(sprite.Sprite):
    groups = {}

    def __init__(self, level, rect, z, direction):
        surface = level.game.loader.create_surface((4, 1))
        surface.fill((52, 197, 163))
        super().__init__(level, surface, rect, z + 1)
        self.velocity = direction
        self.age = 0

    def update(self, dt):
        super().update(dt)
        self.age += dt
        self.rect.center += self.velocity * dt
        if self.rect.colliderect(self.level.player.collision_rect):
            self.level.player.hurt(2)
            return False
        return self.age < 8  # should be offscreen by now
