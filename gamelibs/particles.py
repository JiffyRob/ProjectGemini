import pygame
from pygame.typing import Point, RectLike


class ParticleManager:
    def __init__(self) -> None:
        self.surfaces: list[pygame.Surface] = []
        self.rects: list[pygame.FRect] = []
        self.velocities: list[pygame.Vector2] = []
        self.death_times: list[float] = []

        self.used_ids: set[int] = set()

        self.now = 0.0

    def _get_free_id(self) -> int:
        result = 0
        while result in self.used_ids:
            result += 1
        return result

    def _free_id(self, id: int) -> None:
        self.surfaces[id] = pygame.Surface((0, 0))  # now nothing will be drawn
        self.used_ids.discard(id)

    def _lengthen_to(self, id: int) -> None:
        while len(self.surfaces) < id + 1:
            self.surfaces.append(pygame.Surface((0, 0)))
            self.rects.append(pygame.FRect(0, 0, 0, 0))
            self.velocities.append(pygame.Vector2(0, 0))
            self.death_times.append(0)

    def add_particle(
        self, surface: pygame.Surface, rect: RectLike, velocity: Point, duration: float
    ) -> int:
        id = self._get_free_id()
        self._lengthen_to(id)
        self.surfaces[id] = surface
        self.rects[id] = pygame.FRect(rect)
        self.velocities[id] = pygame.Vector2(velocity)
        self.death_times[id] = self.now + duration
        self.used_ids.add(id)
        return id

    def update(self, dt: float) -> None:
        # hehe, everything is vectorized!
        self.now += dt
        self.rects = list(
            map(
                lambda tup: tup[1].move(self.velocities[tup[0]] * dt),
                enumerate(self.rects),
            )
        )
        list(map(
            self._free_id,
            map(
                lambda x: x[0],
                filter(lambda tup: tup[1] < self.now, enumerate(self.death_times)),
            ),
        ))

    def draw(self, surface: pygame.Surface, offset: Point) -> None:
        surface.fblits(
            zip(self.surfaces, map(lambda rect: rect.move(offset), self.rects))
        )
