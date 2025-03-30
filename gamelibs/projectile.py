from gamelibs import sprite, timer


class Laser(sprite.Sprite):
    groups = {}

    def __init__(self, level, rect, z, direction):
        surface = level.game.loader.create_surface((4, 1))
        surface.fill((205, 36, 36))
        self.death_timer = timer.Timer(15000)
        super().__init__(level, surface, rect, z + 1)
        self.velocity = direction

    def update(self, dt):
        if not self.locked:
            self.rect.center += self.velocity * dt
            if self.rect.colliderect(self.level.player.collision_rect):
                self.level.player.hurt(1)
                return False
            if (
                self.level.map_type != self.level.MAP_HOVERBOARD
                and self.rect.collidelist(self.level.collision_rects) != -1
            ):
                return False
        return not self.death_timer.done() and super().update(dt)
