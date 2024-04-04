import pygame
import math

from scripts import sprite


class HeartMeter(sprite.GUISprite):
    def __init__(self, level, rect=(0, 0, 16, 16)):
        super().__init__(level, None, rect)
        self.heart_frames = self.level.game.loader.get_spritesheet("heart.png", (8, 8))

    def update(self, dt):
        # TODO: Animations and effects?
        pass

    def draw(self, surface):
        heart_count = math.ceil(
            self.level.player.health_capacity / (len(self.heart_frames) - 1)
        )
        columns = self.rect.width // 9
        position = pygame.Vector2()
        health_left = self.level.player.health
        for i in range(heart_count):
            if health_left > len(self.heart_frames) - 1:
                index = len(self.heart_frames) - 1
            else:
                index = health_left
            health_left -= index
            surface.blit(self.heart_frames[index], self.rect.move(position))
            position.x += 9
            if i == columns - 1:
                position.x = 0
                position.y += 9


class EmeraldMeter(sprite.GUISprite):
    X = 10
    EMERALD = 11

    def __init__(self, level, rect=(0, 0, 16, 16)):
        rect = pygame.Rect(rect)
        rect.size = (22, 7)
        super().__init__(level, None, rect)
        self.surface = pygame.Surface(rect.size).convert()
        self.font_frames = self.level.game.loader.get_spritesheet(
            "digifont.png", (3, 5)
        )

    def draw(self, surface):
        numbers = [self.EMERALD, self.X] + [
            int(i) for i in str(self.level.player.emeralds).zfill(3)
        ]
        position = pygame.Vector2(1, 1)
        self.surface.fill("black")
        for i, number in enumerate(numbers):
            self.surface.blit(self.font_frames[number], position + (i * 4, 0))
        surface.blit(self.surface, self.rect)
