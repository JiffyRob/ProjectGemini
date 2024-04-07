from math import sqrt
import pygame

from scripts import loader


class GrowingCircle:
    def __init__(self, size, position, speed=64):
        self.size = pygame.Vector2(size)
        self.surface = loader.Loader.create_surface(size)
        self.radius = 0
        self.position = pygame.Vector2(position)
        self.speed = speed
        self.age = 0
        self.max_radius = sqrt(max(
            [
                self.position.distance_squared_to(corner)
                for corner in ((0, 0), self.size, (self.size.x, 0), (0, self.size.y))
            ]
        ))
        self.done = False

    def update(self, dt):
        self.age += dt
        self.radius = self.age * self.speed
        pygame.draw.circle(self.surface, "white", self.position, self.radius)

    def draw(self, surface):
        surface.blit(self.surface, (0, 0), None, pygame.BLEND_RGB_MULT)
        self.done = self.radius >= self.max_radius


class ShrinkingCircle:
    def __init__(self, size, position, speed=64):
        self.size = pygame.Vector2(size)
        self.surface = loader.Loader.create_surface(self.size)
        self.surface.fill('white')
        self.position = pygame.Vector2(position)
        self.speed = speed
        self.age = 0
        self.radius = self.max_radius = sqrt(max(
            [
                self.position.distance_squared_to(corner)
                for corner in ((0, 0), self.size, (self.size.x, 0), (0, self.size.y))
            ]
        ))
        self.done = False

    def update(self, dt):
        self.age += dt
        self.radius = self.max_radius - self.age * self.speed
        self.surface.fill('black')
        pygame.draw.circle(self.surface, "white", self.position, self.radius)

    def draw(self, surface):
        surface.blit(self.surface, (0, 0), None, pygame.BLEND_RGB_MULT)
        self.done = self.radius <= 0
