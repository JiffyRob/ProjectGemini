from scripts import sprite, timer


class Laser(sprite.Sprite):
    groups = {}

    def __init__(self, level, rect, z, direction):
        surface = level.game.loader.create_surface((4, 1))
        surface.fill((52, 197, 163))
        self.death_timer = timer.Timer(5000)
        super().__init__(level, surface, rect, z + 1)
        self.velocity = direction

    def update(self, dt):
        if not self.locked:
            self.rect.center += self.velocity * dt
            if self.rect.colliderect(self.level.player.collision_rect):
                self.level.player.hurt(2)
                return False
            if self.rect.collidelist(self.level.collision_rects) != -1:
                return False
        return (self.rect.colliderect(self.level.map_rect) or not self.death_timer.done()) and super().update(dt)
