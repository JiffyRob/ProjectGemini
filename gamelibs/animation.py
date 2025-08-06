import functools
from typing import Sequence

import pygame

from gamelibs import interfaces


@functools.cache
def flip_surface(surface: pygame.Surface, flip_x: bool, flip_y: bool) -> pygame.Surface:
    if flip_x:
        surface = pygame.transform.flip(surface, True, False)
    if flip_y:
        surface = pygame.transform.flip(surface, False, True)
    return surface


class Animation(interfaces.Animation):
    def __init__(
        self,
        frames: Sequence[pygame.Surface],
        speed: float = 0.2,
        flip_x: bool = False,
        flip_y: bool = False,
    ) -> None:
        self.frames = list(frames)
        self.time = 0.0
        self.speed = speed
        self._flip_x = flip_x
        self._flip_y = flip_y

    @property
    def flip_x(self) -> bool:
        return self._flip_x
    
    @flip_x.setter
    def flip_x(self, value: bool) -> None:
        self._flip_x = value
    
    @property
    def flip_y(self) -> bool:
        return self._flip_y
    
    @flip_y.setter
    def flip_y(self, value: bool) -> None:
        self._flip_y = value

    def update(self, dt: float) -> None:
        self.time += dt

    def restart(self) -> None:
        self.time = 0

    def done(self) -> bool:
        return False

    @property
    def image(self) -> pygame.Surface:
        image = self.frames[round(self.time / self.speed) % len(self.frames)]
        return flip_surface(image, self.flip_x, self.flip_y)


class NoLoopAnimation(interfaces.Animation):
    def __init__(
        self,
        frames: Sequence[pygame.Surface],
        speed: float = 0.2,
        flip_x: bool = False,
        flip_y: bool = False,
    ) -> None:
        self.frames = list(frames)
        self.time = 0.0
        self.speed = speed
        self.flip_x = flip_x
        self.flip_y = flip_y

    @property
    def flip_x(self) -> bool:
        return self._flip_x
    
    @flip_x.setter
    def flip_x(self, value: bool) -> None:
        self._flip_x = value
    
    @property
    def flip_y(self) -> bool:
        return self._flip_y
    
    @flip_y.setter
    def flip_y(self, value: bool) -> None:
        self._flip_y = value

    def update(self, dt: float) -> None:
        self.time += dt

    def restart(self) -> None:
        self.time = 0

    def done(self) -> bool:
        return (
            min(round(self.time / self.speed), len(self.frames) - 1)
            == len(self.frames) - 1
        )

    @property
    def image(self) -> pygame.Surface:
        frame_index = min(round(self.time / self.speed), len(self.frames) - 1)
        return flip_surface(self.frames[frame_index], self.flip_x, self.flip_y)


class SingleAnimation(interfaces.Animation):
    def __init__(
        self, surface: pygame.Surface, flip_x: bool = False, flip_y: bool = False
    ) -> None:
        self.surface = surface
        self.flip_x = flip_x
        self.flip_y = flip_y

    @property
    def flip_x(self) -> bool:
        return self._flip_x
    
    @flip_x.setter
    def flip_x(self, value: bool) -> None:
        self._flip_x = value
    
    @property
    def flip_y(self) -> bool:
        return self._flip_y
    
    @flip_y.setter
    def flip_y(self, value: bool) -> None:
        self._flip_y = value

    def update(self, dt: float) -> None:
        pass

    def restart(self) -> None:
        pass

    def done(self) -> bool:
        return True

    @property
    def image(self) -> pygame.Surface:
        return flip_surface(self.surface, self.flip_x, self.flip_y)


class AnimatedSurface(pygame.Surface, interfaces.Animation):
    def __init__(
        self,
        frames: Sequence[pygame.Surface],
        speed: float = 0.2,
        flip_x: bool = False,
        flip_y: bool = False,
    ) -> None:
        self.frames = list(frames)
        self.time = 0.0
        self.speed = speed
        self.flip_x = flip_x
        self.flip_y = flip_y
        self.index = 0
        super().__init__(self.frames[0].get_size(), pygame.SRCALPHA)

    @property
    def flip_x(self) -> bool:
        return self._flip_x
    
    @flip_x.setter
    def flip_x(self, value: bool) -> None:
        self._flip_x = value
    
    @property
    def flip_y(self) -> bool:
        return self._flip_y
    
    @flip_y.setter
    def flip_y(self, value: bool) -> None:
        self._flip_y = value

    def restart(self) -> None:
        self.time = 0.0

    def update(self, dt: float) -> None:
        self.time += dt
        new_index = round(self.time / self.speed) % len(self.frames)
        if new_index != self.index:
            self.index = new_index
            self.fill((0, 0, 0, 0))
            self.blit(
                flip_surface(self.frames[self.index], self.flip_x, self.flip_y), (0, 0)
            )
