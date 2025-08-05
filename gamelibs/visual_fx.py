from math import sqrt

import pygame

from gamelibs import loader


class VisualEffect:
    def __init__(self, on_done=lambda: None):
        self.done = False
        self.on_done = on_done
        self.called_done = False

    def update(self, dt):
        if not self.called_done and self.done:
            self.on_done()
            self.called_done = True
            return False
        return True

    def draw(self, surface):
        return None

    def draw_over(self, dest_surface, dest_rect):
        return None


class CircleTransitionIn(VisualEffect):
    def __init__(self, size, position, speed=64, on_done=lambda: None):
        super().__init__(on_done)
        self.size = pygame.Vector2(size)
        self.surface = loader.Loader.create_surface(size)
        self.surface.fill("black")
        self.radius = 0
        if callable(position):
            self.position_getter = position
        else:
            position = pygame.Vector2(position)
            self.position_getter = lambda: position
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
    def position(self):
        return self.position_getter()

    def update(self, dt):
        self.age += dt
        self.radius = self.age * self.speed
        pygame.draw.circle(self.surface, "white", self.position, self.radius)
        self.done = self.radius >= self.max_radius
        return super().update(dt)

    def draw(self, surface):
        surface.blit(self.surface, (0, 0), None, pygame.BLEND_RGB_MULT)

    def draw_over(self, dest_surface, dest_rect):
        dest_surface.blit(self.surface, dest_rect, None, pygame.BLEND_RGB_MULT)


class CircleTransitionOut(VisualEffect):
    def __init__(self, size, position, speed=64, on_done=lambda: None):
        super().__init__(on_done)
        self.size = pygame.Vector2(size)
        self.surface = loader.Loader.create_surface(self.size)
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
    def position(self):
        return self.position_getter()

    def update(self, dt):
        self.age += dt
        self.radius = self.max_radius - self.age * self.speed
        self.surface.fill("black")
        self.done = self.radius <= 0
        pygame.draw.circle(self.surface, "white", self.position, self.radius)
        return super().update(dt)

    def draw(self, surface):
        surface.blit(self.surface, (0, 0), None, pygame.BLEND_RGB_MULT)


class ColorTransitionOut(VisualEffect):
    def __init__(self, color="black", duration=1, on_done=lambda: None):
        super().__init__(on_done)
        self.age = 0
        self.duration = duration
        self.color = pygame.Color(color)

    def update(self, dt):
        self.age += dt
        self.done = self.age >= self.duration
        self.color.a = pygame.math.clamp(round(self.age * 255 / self.duration), 0, 255)
        return super().update(dt)

    def draw(self, surface):
        color_surface = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
        color_surface.fill(self.color)
        surface.blit(color_surface, (0, 0))

    def draw_over(self, dest_surface, dest_rect):
        surface = pygame.Surface(dest_rect.size, pygame.SRCALPHA)
        surface.fill(self.color)
        surface.blit(surface, dest_rect)


class ColorTransitionIn(ColorTransitionOut):
    def update(self, dt):
        self.age += dt
        self.done = self.age >= self.duration
        self.color.a = pygame.math.clamp(
            255 - round(self.age * 255 / self.duration), 0, 255
        )
        return VisualEffect.update(self, dt)


class Fill(VisualEffect):
    def __init__(self, color, duration=0, on_done=lambda: None):
        super().__init__(on_done)
        self.color = color
        self.duration = duration
        self.age = 0
        if not self.duration:
            self.on_done()
            self.called_done = True

    def update(self, dt):
        self.age += dt
        self.done = (self.age >= self.duration) and self.duration
        return super().update(dt)

    def draw(self, surface):
        surface.fill(self.color)

    def draw_over(self, dest_surface, dest_rect):
        dest_surface.fill(self.color, dest_rect)


class Blink(VisualEffect):
    def __init__(self, color="white", speed=0.2, count=3, on_done=lambda: None):
        super().__init__(on_done)
        self.color = pygame.Color(color)
        self.speed = speed
        self.age = 0
        self.count = count

    def update(self, dt):
        self.age += dt
        return super().update(dt)

    def draw(self, surface):
        index = self.age // self.speed
        if index % 2:
            new_surface = pygame.Surface(surface.get_size())
            new_surface.fill(surface.get_colorkey())
            new_surface.set_colorkey(surface.get_colorkey())
            pygame.transform.threshold(
                new_surface, surface, surface.get_colorkey(), set_color=self.color
            )
            surface.blit(new_surface, (0, 0))
        if index >= self.count * 2:
            self.done = True

    def draw_over(self, dest_surface, dest_rect):
        raise TypeError(
            f"{self.__class__} cannot be drawn over other surfaces due to no transparency info"
        )


class Hide(VisualEffect):
    def draw(self, surface):
        surface.fill(surface.get_colorkey())

    def draw_over(self, dest_surface, dest_rect):
        pass
