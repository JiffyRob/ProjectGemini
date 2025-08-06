from math import sqrt
from typing import Any, Callable

import pygame
from pygame.typing import ColorLike, Point, RectLike

from gamelibs import interfaces, hardware


class VisualEffect:
    def __init__(self, on_done: Callable[[], Any] = lambda: None) -> None:
        self.done = False
        self.on_done = on_done
        self.called_done = False

    def update(self, dt: float) -> bool:
        if not self.called_done and self.done:
            self.on_done()
            self.called_done = True
            return False
        return True


class CircleTransitionIn(VisualEffect, interfaces.GlobalEffect):
    def __init__(
        self,
        size: tuple[int, int],
        position: Point | Callable[[], pygame.Vector2],
        speed: float = 64,
        on_done: Callable[[], Any] = lambda: None,
    ) -> None:
        super().__init__(on_done)
        self.size = pygame.Vector2(size)
        self.surface = hardware.loader.create_surface(size)
        self.surface.fill("black")
        self.radius = 0
        self.position_getter: Callable[[], pygame.Vector2]
        if callable(position):
            self.position_getter = position
        else:
            self.position_getter = lambda: pygame.Vector2(position)
        self.speed = speed
        self.age = 0
        self.max_radius = sqrt(
            max(
                [
                    self.position.distance_squared_to(corner)
                    for corner in (
                        (0, 0),
                        self.size,
                        (self.size.x, 0),
                        (0, self.size.y),
                    )
                ]
            )
        )

    @property
    def position(self) -> pygame.Vector2:
        return self.position_getter()

    def update(self, dt: float) -> bool:
        self.age += dt
        self.radius = self.age * self.speed
        pygame.draw.circle(self.surface, "white", self.position, self.radius)
        self.done = self.radius >= self.max_radius
        return super().update(dt)

    def draw(self, surface: pygame.Surface) -> None:
        surface.blit(self.surface, (0, 0), None, pygame.BLEND_RGB_MULT)

    def draw_over(self, dest_surface: pygame.Surface, dest_rect: RectLike) -> None:
        dest_surface.blit(self.surface, dest_rect, None, pygame.BLEND_RGB_MULT)


class CircleTransitionOut(VisualEffect, interfaces.GlobalEffect):
    def __init__(
        self,
        size: tuple[int, int],
        position: Point | Callable[[], pygame.Vector2],
        speed: float = 64,
        on_done: Callable[[], Any] = lambda: None,
    ) -> None:
        super().__init__(on_done)
        self.size = pygame.Vector2(size)
        self.surface = hardware.loader.create_surface(self.size)
        self.surface.fill("white")
        if callable(position):
            self.position_getter = position
        else:
            position = pygame.Vector2(position)
            self.position_getter = lambda: position
        self.speed = speed
        self.age = 0
        self.radius = self.max_radius = sqrt(
            max(
                [
                    self.position.distance_squared_to(corner)
                    for corner in (
                        (0, 0),
                        self.size,
                        (self.size.x, 0),
                        (0, self.size.y),
                    )
                ]
            )
        )

    @property
    def position(self) -> pygame.Vector2:
        return self.position_getter()

    def update(self, dt: float) -> bool:
        self.age += dt
        self.radius = self.max_radius - self.age * self.speed
        self.surface.fill("black")
        self.done = self.radius <= 0
        pygame.draw.circle(self.surface, "white", self.position, self.radius)
        return super().update(dt)

    def draw(self, surface: pygame.Surface) -> None:
        surface.blit(self.surface, (0, 0), None, pygame.BLEND_RGB_MULT)


class ColorTransitionOut(VisualEffect, interfaces.GlobalEffect):
    def __init__(self, color: ColorLike="black", duration: float=1, on_done: Callable[[], Any]=lambda: None) -> None:
        super().__init__(on_done)
        self.age = 0
        self.duration = duration
        self.color = pygame.Color(color)

    def update(self, dt: float) -> bool:
        self.age += dt
        self.done = self.age >= self.duration
        self.color.a = int(pygame.math.clamp(round(self.age * 255 / self.duration), 0, 255))
        return super().update(dt)

    def draw(self, surface: pygame.Surface) -> None:
        color_surface = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
        color_surface.fill(self.color)
        surface.blit(color_surface, (0, 0))

    def draw_over(self, dest_surface: pygame.Surface, dest_rect: RectLike) -> None:
        dest_rect = pygame.Rect(dest_rect)
        surface = pygame.Surface(dest_rect.size, pygame.SRCALPHA)
        surface.fill(self.color)
        surface.blit(surface, dest_rect)


class ColorTransitionIn(ColorTransitionOut, interfaces.GlobalEffect):
    def update(self, dt: float) -> bool:
        self.age += dt
        self.done = self.age >= self.duration
        self.color.a = int(pygame.math.clamp(
            255 - round(self.age * 255 / self.duration), 0, 255
        ))
        return VisualEffect.update(self, dt)


class Fill(VisualEffect):
    def __init__(self, color: ColorLike, duration: float=0, on_done: Callable[[], Any]=lambda: None):
        super().__init__(on_done)
        self.color = color
        self.duration = duration
        self.age = 0
        if not self.duration:
            self.on_done()
            self.called_done = True

    def update(self, dt: float) -> bool:
        self.age += dt
        self.done = (self.age >= self.duration) and self.duration
        return super().update(dt)

    def draw(self, surface: pygame.Surface) -> None:
        surface.fill(self.color)

    def draw_over(self, dest_surface: pygame.Surface, dest_rect: RectLike) -> None:
        dest_surface.fill(self.color, dest_rect)


class Blink(VisualEffect, interfaces.SpriteEffect):
    def __init__(self, color: ColorLike="white", speed: float=0.2, count: int=3, on_done: Callable[[], Any]=lambda: None) -> None:
        super().__init__(on_done)
        self.color = pygame.Color(color)
        self.speed = speed
        self.age = 0
        self.count = count

    def update(self, dt: float) -> bool:
        self.age += dt
        return super().update(dt)

    def draw(self, surface: pygame.Surface) -> None:
        index = self.age // self.speed
        if index % 2:
            new_surface = pygame.Surface(surface.get_size())
            colorkey = surface.get_colorkey()
            if colorkey is None:
                colorkey = (0, 0, 0, 0)
            new_surface.fill(colorkey)
            new_surface.set_colorkey(colorkey)
            pygame.transform.threshold(
                new_surface, surface, colorkey, set_color=self.color
            )
            surface.blit(new_surface, (0, 0))
        if index >= self.count * 2:
            self.done = True


class Hide(VisualEffect, interfaces.SpriteEffect):
    def draw(self, surface: pygame.Surface) -> None:
        surface.fill(surface.get_colorkey() or (0, 0, 0, 0))
