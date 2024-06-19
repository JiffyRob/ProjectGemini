import pygame


class Sprite:
    groups = set()

    def __init__(self, level, image=None, rect=(0, 0, 16, 16), z=0):
        self.level = level
        self.image = image
        self.to_draw = image
        self.rect = pygame.FRect(rect)
        self.z = z
        self.velocity = pygame.Vector2()
        self.dead = False
        self.locked = False
        self.effects = []

    def lock(self):
        self.locked = True

    def unlock(self):
        self.locked = False

    @property
    def pos(self):
        return pygame.Vector2(self.rect.center)

    def update(self, dt):
        self.effects = [effect for effect in self.effects if effect.update(dt)]
        if self.image is not None:
            self.to_draw = self.image.copy()
            for effect in self.effects:
                effect.draw(self.to_draw)
        else:
            self.to_draw = None
        return True


class GUISprite(Sprite):
    def draw(self, surface):
        surface.blit(self.image, self.rect)
