from typing import Any, Callable

import pygame

from gamelibs import interfaces


class Timer(interfaces.Timer):
    def __init__(
        self,
        amount: int = 1000,
        on_finish: Callable[[], Any] = lambda: None,
        repeat: bool = False,
    ) -> None:
        self.wait = amount
        self.start = pygame.time.get_ticks()
        self.on_finish = on_finish
        self.repeat = repeat
        self.ran_ending = False

    def __repr__(self) -> str:
        return f"<bush.Timer (start={self.start}, remaining={self.time_left()}>"

    def time_left(self) -> int:
        return max(self.wait - (pygame.time.get_ticks() - self.start), 0)

    def percent_complete(self) -> float:
        return (self.wait - self.time_left()) / self.wait

    def done(self) -> bool:
        return self.time_left() == 0

    def reset(self) -> None:
        self.start = pygame.time.get_ticks()
        self.ran_ending = False

    def finish(self) -> None:
        self.start = (pygame.time.get_ticks() - self.wait) - 1

    def update(self) -> None:
        now = pygame.time.get_ticks()
        if now - self.start >= self.wait and not self.ran_ending:
            self.on_finish()
            if self.repeat:
                self.reset()
            else:
                self.ran_ending = True


class DTimer(interfaces.DTimer):
    def __init__(
        self,
        amount: float = 1000,
        on_finish: Callable[[], Any] = lambda: None,
        repeat: bool = False,
    ):
        self.wait = amount
        self.remaining = self.wait
        self.on_finish = on_finish
        self.repeat = repeat
        self.ran_ending = False

    def __repr__(self) -> str:
        return f"<bush.DTimer (remaining={self.time_left()})>"

    def time_left(self) -> int:
        return int(self.remaining)

    def percent_complete(self) -> float:
        return (self.wait - self.time_left()) / self.wait

    def done(self) -> bool:
        return not self.remaining

    def reset(self) -> None:
        self.remaining = self.wait
        self.ran_ending = False

    def finish(self) -> None:
        self.remaining = 0

    def update(self, dt: float) -> None:
        self.remaining = max(0, self.remaining - (dt * 1000))
        if not self.remaining:
            self.on_finish()
            if self.repeat:
                self.reset()
            else:
                self.ran_ending = True
