import math
from typing import Callable

type Easing = Callable[[float], float]

def create_exp_easings(exp: float) -> tuple[Easing, Easing, Easing]:
    def ease_in(time: float) -> float:
        return time**exp  #type: ignore

    def ease_out(time: float) -> float:
        return 1 - (1 - time) ** exp  #type: ignore

    def ease_in_out(time: float) -> float:
        return (  #type: ignore
            2 ** (exp - 1) * time**exp if time < 0.5 else 1 - (-2 * time + 2) ** exp / 2
        )

    return ease_in, ease_out, ease_in_out


def reverse(easer: Easing) -> Easing:
    def reverser(time: float) -> float:
        return 1 - easer(time)

    return reverser


def combo(*easers: Easing) -> Easing:
    count = len(easers)

    def callback(time: float) -> float:
        index, time = divmod(time * count, 1)
        if index == count:
            index -= 1
            time += 1
        return easers[int(index)](time)

    return callback


# implementations translated from easings.net
def scale(start: float, end: float, time: float) -> float:
    return start + (end - start) * time


def linear(time: float) -> float:
    return time


def in_sine(time: float) -> float:
    return 1 - math.cos((time * math.pi) / 2)


def out_sine(time: float) -> float:
    return math.sin(time * math.pi / 2)


def in_out_sine(time: float) -> float:
    return -(math.cos(math.pi * time) - 1) / 2


def in_quad(time: float) -> float:
    return time**2


def out_quad(time: float) -> float:
    return 1 - (1 - time) ** 2


def in_out_quad(time: float) -> float:
    return 2 * time * time if time < 0.5 else 1 - (-2 * time + 2) ** 2 / 2


def in_cubic(time: float) -> float:
    return time**3


def out_cubic(time: float) -> float:
    return 1 - ((1 - time) ** 3)


def in_out_cubic(time: float) -> float:
    return 4 * (time**3) if time < 0.5 else 1 - ((-2 * time + 2) ** 3) / 2


def in_quart(time: float) -> float:
    return time**4


def out_quart(time: float) -> float:
    return 1 - (1 - time) ** 4


def in_out_quart(time: float) -> float:
    return 8 * time**4 if time < 0.5 else 1 - (-2 * time + 2) ** 4 / 2


def in_quint(time: float) -> float:
    return time**5


def out_quint(time: float) -> float:
    return 1 - (1 - time) ** 5


def in_out_quint(time: float) -> float:
    return 16 * time**5 if time < 0.5 else 1 - (-2 * time + 2) ** 5 / 2


def in_expo(time: float) -> float:
    return 0 if time == 0 else 2 ** (10 * time - 10)


def out_expo(time: float) -> float:
    return 1 if time == 1 else 1 - 2 ** (-10 * time)


def in_out_expo(time: float) -> float:
    if time not in {0, 1}:
        if time < 0.5:
            return 2 ** (20 * time - 10) / 2
        else:
            return (2 - 2 ** (-20 * time + 10)) / 2
    return time


def in_circ(time: float) -> float:
    return 1 - math.sqrt(1 - time**2)


def out_circ(time: float) -> float:
    return math.sqrt(1 - (time - 1) ** 2)


def in_out_circ(time: float) -> float:
    return (
        (1 - math.sqrt(1 - (2 * time) ** 2)) / 2
        if time < 0.5
        else (math.sqrt(1 - (-2 * time + 2) ** 2) + 1) / 2
    )


def in_back(time: float) -> float:
    return 2.70158 * time**3 - 1.70158 * time**2


def out_back(time: float) -> float:
    return 1 + 2.70158 * (time - 1) ** 3 + 1.70158 * (time - 1) ** 2


def in_out_back(time: float) -> float:
    c1 = 1.70158
    c2 = c1 * 1.525
    return (
        ((2 * time) ** 2 * ((c2 + 1) * 2 * time - c2)) / 2
        if time < 0.5
        else ((2 * time - 2) ** 2 * ((c2 + 1) * (time * 2 - 2) + c2) + 2) / 2
    )


def in_elastic(time: float) -> float:
    if time not in {0, 1}:
        return -(2 ** (10 * time - 10)) * math.sin(
            (time * 10 - 10.75) * (2 * math.pi / 3)
        )
    return time


def out_elastic(time: float) -> float:
    if time not in {0, 1}:
        return -(2 ** (-10 * time)) * math.sin(time * 10 - 0.75) * (math.pi * 2 / 3) + 1
    return time


def in_out_elastic(time: float) -> float:
    c3 = 2 * math.pi / 4.5
    if time not in {0, 1}:
        if time < 0.5:
            return -(2 ** (20 * time - 10) * math.sin((20 * time - 11.125) * c3)) / 2
        else:
            return (
                2 ** (-20 * time + 10) * math.sin((20 * time - 11.125) * c3)
            ) / 2 + 1
    return time


def out_bounce(time: float) -> float:
    n1 = 7.5625
    d1 = 2.75

    if time < 1 / d1:
        return time**2 * n1
    elif time < 2 / d1:
        time -= 1.5 / d1
        return n1 * time**2 + 0.75
    elif time < 2.5 / d1:
        time -= 2.25 / d1
        return n1 * time**2 + 0.9375
    else:
        time -= 2.625 / d1
        return n1 * time**2 + 0.984375


def in_bounce(time: float) -> float:
    return 1 - out_bounce(1 - time)


def in_out_bounce(time: float) -> float:
    return (
        (1 - out_bounce(1 - 2 * time)) / 2
        if time < 0.5
        else (1 + out_bounce(2 * time - 1)) / 2
    )
