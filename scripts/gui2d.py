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
        heart_count = math.ceil(self.level.player.health_capacity / (len(self.heart_frames) - 1))
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
