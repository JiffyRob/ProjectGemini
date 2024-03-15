import functools

import pygame


@functools.cache
def flip_surface(surface, flip_x, flip_y):
    if flip_x:
        surface = pygame.transform.flip(surface, True, False)
    if flip_y:
        surface = pygame.transform.flip(surface, False, True)
    return surface


class Animation:
    def __init__(self, frames, speed=.2, flip_x=False, flip_y=False):
        self.frames = list(frames)
        self.time = 0
        self.speed = speed
        self.flip_x = flip_x
        self.flip_y = flip_y

    def update(self, dt):
        self.time += dt

    def restart(self):
        self.time = 0

    @property
    def image(self):
        image = self.frames[round(self.time / self.speed) % len(self.frames)]
        return flip_surface(image, self.flip_x, self.flip_y)


class SingleAnimation:
    def __init__(self, surface, flip_x=False, flip_y=False):
        self.surface = surface
        self.flip_x = flip_x
        self.flip_y = flip_y

    def update(self, dt):
        pass

    @property
    def image(self):
        return flip_surface(self.surface, self.flip_x, self.flip_y)