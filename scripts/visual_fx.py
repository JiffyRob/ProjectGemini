from math import sqrt

import pygame

from scripts import loader


class GrowingCircle:
    def __init__(self, size, position, speed=64):
        self.size = pygame.Vector2(size)
        self.surface = loader.Loader.create_surface(size)
        self.surface.fill("black")
        self.radius = 0
        if callable(position):
            self.position_getter = position
        else:
            position = pygame.Vector2(position)
            self.position_getter = lambda: position
        self.speed = speed
        self.age = 0
        self.max_radius = sqrt(
            max(
                [
                    self.position.distance_squared_to(corner)
                    for corner in (
                        (0, 0),
                        self.size,
                        (self.size.x, 0),
                        (0, self.size.y),
                    )
                ]
            )
        )
        self.done = False

    @property
    def position(self):
        return self.position_getter()

    def update(self, dt):
        self.age += dt
        self.radius = self.age * self.speed
        pygame.draw.circle(self.surface, "white", self.position, self.radius)
        return not self.done

    def draw(self, surface, dest_surface=None, dest_rect=None):
        if dest_rect is None:
            rect = pygame.Rect(0, 0, 0, 0)
        if dest_surface is None:
            dest_surface = surface
        dest_surface.blit(
            self.surface, (rect.topleft, rect.topleft), None, pygame.BLEND_RGB_MULT
        )
        self.done = self.radius >= self.max_radius


class ShrinkingCircle:
    def __init__(self, size, position, speed=64):
        self.size = pygame.Vector2(size)
        self.surface = loader.Loader.create_surface(self.size)
        self.surface.fill("white")
        if callable(position):
            self.position_getter = position
        else:
            position = pygame.Vector2(position)
            self.position_getter = lambda: position
        self.speed = speed
        self.age = 0
        self.radius = self.max_radius = sqrt(
            max(
                [
                    self.position.distance_squared_to(corner)
                    for corner in (
                        (0, 0),
                        self.size,
                        (self.size.x, 0),
                        (0, self.size.y),
                    )
                ]
            )
        )
        self.done = False

    @property
    def position(self):
        return self.position_getter()

    def update(self, dt):
        self.age += dt
        self.radius = self.max_radius - self.age * self.speed
        self.surface.fill("black")
        pygame.draw.circle(self.surface, "white", self.position, self.radius)
        return not self.done

    def draw(self, surface, dest_surface=None, dest_rect=None):
        if dest_rect is None:
            dest_rect = pygame.Rect(0, 0, 0, 0)
        if dest_surface is None:
            dest_surface = surface
        dest_surface.blit(self.surface, dest_rect, None, pygame.BLEND_RGB_MULT)
        self.done = self.radius <= 0


class FadeOut:
    def __init__(self, color='black', duration=1):
        self.age = 0
        self.duration = duration
        self.color = pygame.Color(color)
        self.done = False
        print('new')

    def update(self, dt):
        self.age += dt
        self.done = self.age >= self.duration
        return not self.done

    def draw(self, surface, dest_surface=None, dest_rect=None):
        if dest_surface is None:
            dest_surface = surface
        if dest_rect is None:
            dest_rect = dest_surface.get_rect()
        surface = pygame.Surface(dest_rect.size, pygame.SRCALPHA)
        self.color.a = pygame.math.clamp(round(self.age * 255 / self.duration), 0, 255)
        surface.fill(self.color)
        dest_surface.blit(surface, dest_rect)
        return not self.done


class EternalSolid:
    def __init__(self, color):
        self.color = color
        self.done = False

    def update(self, dt):
        return True

    def draw(self, surface, dest_surface=None, dest_rect=None):
        if dest_surface is None:
            dest_surface = surface
        if dest_rect is None:
            dest_rect = dest_surface.get_rect()
        pygame.draw.rect(dest_surface, self.color, dest_rect)


class FadeIn(FadeOut):
    def draw(self, surface, dest_surface=None, dest_rect=None):
        if dest_surface is None:
            dest_surface = surface
        if dest_rect is None:
            dest_rect = dest_surface.get_rect()
        surface = pygame.Surface(dest_rect.size, pygame.SRCALPHA)
        self.color.a = pygame.math.clamp((self.duration - self.age) * 255 / self.duration, 0, 255)
        surface.fill(self.color)
        dest_surface.blit(surface, dest_rect)
        return not self.done


class Blink:
    def __init__(self, color="white", speed=0.2, count=3):
        self.color = pygame.Color(color)
        self.speed = speed
        self.age = 0
        self.done = False
        self.count = count

    def update(self, dt):
        self.age += dt
        return not self.done

    def draw(self, surface, dest_surface=None, dest_rect=None):
        if dest_rect is None:
            dest_rect = pygame.Rect(0, 0, 0, 0)
        if dest_surface is None:
            dest_surface = surface
        index = self.age // self.speed
        if index % 2:
            print("blinky")
            # TODO: pygame.transform.solid_overlay???
            new_surface = pygame.Surface(surface.get_size()).convert(dest_surface)
            new_surface.fill(surface.get_colorkey())
            new_surface.set_colorkey(surface.get_colorkey())
            pygame.transform.threshold(
                new_surface, surface, surface.get_colorkey(), set_color=self.color
            )
            dest_surface.blit(new_surface, dest_rect)
        if index >= self.count * 2:
            self.done = True
        return not self.done