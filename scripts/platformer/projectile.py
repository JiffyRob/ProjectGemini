from scripts import sprite


class Laser(sprite.Sprite):
    groups = {}

    def __init__(self, level, rect, z, direction):
        surface = level.game.loader.create_surface((4, 1))
        surface.fill((52, 197, 163))
        super().__init__(level, surface, rect, z + 1)
        self.velocity = direction

    def update(self, dt):
        super().update(dt)
        self.rect.center += self.velocity * dt
        if self.rect.colliderect(self.level.player.collision_rect):
            self.level.player.hurt(2)
            return False
        if self.rect.collidelist(self.level.collision_rects) != -1:
            return False
        return self.rect.colliderect(self.level.map_rect)
