from gamelibs import sprite, timer


class Laser(sprite.Sprite):
    groups: set[str] = set()
    SPEED = 100

    def __init__(self, level, rect, z, direction):
        surface = level.game.loader.create_surface((4, 1))
        surface.fill((205, 36, 36))
        self.death_timer = timer.Timer(15000)
        super().__init__(level, surface, rect, z + 1)
        self.velocity = direction

    def update(self, dt):
        if not self.locked:
            self.rect.center += self.velocity * dt * self.SPEED
            if self.rect.colliderect(self.level.player.collision_rect):
                self.level.player.hurt(1)
                return False
            if (
                self.level.map_type != self.level.MAP_HOVERBOARD
                and self.rect.collidelist(self.level.get_rects("collision")) != -1
            ):
                return False
        return not self.death_timer.done() and super().update(dt)


class MiniLaser(sprite.Sprite):
    groups: set[str] = set()
    SPEED = 250

    def __init__(self, level, rect, z, direction):
        surface = level.game.loader.create_surface((2, 1))
        surface.fill((199, 86, 190))
        self.death_timer = timer.Timer(15000)
        super().__init__(level, surface, rect, z + 1)
        self.velocity = direction

    def update(self, dt):
        if not self.locked:
            self.rect.center += self.velocity * dt * self.SPEED
            for sprite in self.level.get_group("hurtable"):
                if sprite.collision_rect.colliderect(self.rect):
                    sprite.hurt(1)
                    return False
            if (
                self.level.map_type != self.level.MAP_HOVERBOARD
                and self.rect.collidelist(self.level.get_rects("collision")) != -1
            ):
                return False
        return not self.death_timer.done() and super().update(dt)
