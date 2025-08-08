import pygame

from pygame.typing import Point

from gamelibs import sprite, timer, interfaces, hardware


class Laser(sprite.Sprite):
    groups: set[str] = set()
    SPEED = 100

    def __init__(
        self,
        level: interfaces.Level,
        pos: Point,
        z: int,
        direction: interfaces.Direction,
    ) -> None:
        if direction.get_axis() == interfaces.Axis.X:
            surface = hardware.loader.create_surface((4, 1))
            rect = pygame.FRect(0, 0, 4, 1)
        else:
            surface = hardware.loader.create_surface((1, 4))
            rect = pygame.FRect(0, 0, 1, 4)
        rect.center = pos
        surface.fill((205, 36, 36))
        self.death_timer = timer.Timer(15000)
        super().__init__(level, surface, rect, z + 1)
        self.velocity = direction.to_vector()

    def update(self, dt: float) -> bool:
        if not self.locked:
            self.rect.center += self.velocity * dt * self.SPEED
            if self.rect.colliderect(self.get_player().collision_rect):
                self.get_player().hurt(1)
                return False
            if (
                self.get_level().map_type != interfaces.MapType.HOVERBOARD
                and self.rect.collidelist(self.get_level().get_rects("collision")) != -1
            ):
                return False
        return not self.death_timer.done() and super().update(dt)


class MiniLaser(sprite.Sprite):
    groups: set[str] = set()
    SPEED = 250

    def __init__(
        self,
        level: interfaces.Level,
        pos: Point,
        z: int,
        direction: interfaces.Direction,
    ) -> None:
        if direction.get_axis() == interfaces.Axis.X:
            surface = hardware.loader.create_surface((2, 1))
            rect = pygame.FRect(0, 0, 2, 1)
        else:
            surface = hardware.loader.create_surface((1, 2))
            rect = pygame.FRect(0, 0, 1, 2)
        rect.center = pos
        surface.fill((199, 86, 190))
        self.death_timer = timer.Timer(15000)
        super().__init__(level, surface, rect, z + 1)
        self.velocity = direction.to_vector()

    def update(self, dt: float) -> bool:
        if not self.locked:
            self.rect.center += self.velocity * dt * self.SPEED
            for sprite in self.get_level().get_group("hurtable"):
                if sprite.collision_rect.colliderect(self.rect):  # type: ignore
                    sprite.hurt(1)  # type: ignore
                    return False
            if (
                self.get_level().map_type != interfaces.MapType.HOVERBOARD
                and self.rect.collidelist(self.get_level().get_rects("collision")) != -1
            ):
                return False
        return not self.death_timer.done() and super().update(dt)
