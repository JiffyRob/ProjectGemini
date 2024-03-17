import pygame


class Sprite:
    def __init__(self, level, image=None, rect=(0, 0, 16, 16), z=0):
        self.level = level
        self.image = image
        self.rect = pygame.FRect(rect)
        self.z = z
        self.velocity = pygame.Vector2()
        self.dead = False

    @property
    def pos(self):
        return self.rect.center

    def update(self, dt):
        return True
