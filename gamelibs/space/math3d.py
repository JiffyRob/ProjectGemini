from __future__ import annotations

import math
from dataclasses import dataclass, field
from copy import copy

import numpy
import pygame
from pygame.typing import SequenceLike


class Quaternion:
    def __init__(self, theta: float=0.0, axis: SequenceLike[float]=(0, 0, 1)):
        self.real = math.cos(theta / 2)
        self.vector = pygame.Vector3(axis).normalize() * math.sin(theta / 2)

    def magnitude(self) -> float:
        return math.sqrt(
            self.real**2 + self.vector.x**2 + self.vector.y**2 + self.vector.z**2
        )

    @classmethod
    def from_standard(cls, r: float, i: float, j: float, k: float) -> Quaternion:
        result = cls()
        result.real = r
        result.vector.xyz = i, j, k  #type: ignore
        return result

    @classmethod
    def from_degrees(cls, real: float=0.0, axis: SequenceLike[float]=(0, 0, 1)) -> Quaternion:
        return cls(real * math.pi / 180, axis)

    def __neg__(self) -> Quaternion:
        return self.invert()

    def copy(self) -> Quaternion:
        return Quaternion.from_standard(self.real, *self.vector)

    def invert(self) -> Quaternion:
        return Quaternion.from_standard(self.real, *-self.vector)

    def dot(self, other: Quaternion) -> float:
        return self.real * other.real + sum(
            self.vector.elementwise() * other.vector.elementwise()
        )

    def nlerp(self, other: Quaternion, t: float) -> Quaternion:
        a = self
        if self.dot(other) < 0:
            a = self.invert()
        b = other
        return Quaternion.from_standard(
            a.real + t * (b.real - a.real),
            *a.vector + t * (b.vector - a.vector),
        ).normalize()

    def normalize(self) -> Quaternion:
        length = math.sqrt(self.real**2 + sum(self.vector.elementwise() ** 2))
        return Quaternion.from_standard(
            self.real / length,
            *self.vector / length,
        )

    def __bool__(self) -> bool:
        return bool(self.vector)

    def __mul__(self, other: Quaternion | pygame.Vector3 | float) -> Quaternion | pygame.Vector3 | float:
        if isinstance(other, Quaternion):
            r1, i1, j1, k1 = self.real, *self.vector
            r2, i2, j2, k2 = other.real, *other.vector
            return Quaternion.from_standard(
                r1 * r2 - i1 * i2 - j1 * j2 - k1 * k2,
                r1 * i2 + i1 * r2 + j1 * k2 - k1 * j2,
                r1 * j2 - i1 * k2 + j1 * r2 + k1 * i2,
                r1 * k2 + i1 * j2 - j1 * i2 + k1 * r2,
            )
        if isinstance(other, pygame.Vector3):
            cross_product = self.vector.cross(other)
            return (
                other
                + (cross_product * 2 * self.real)
                + 2 * self.vector.cross(cross_product)
            )
        if isinstance(other, float):
            return Quaternion.from_standard(self.real * other, *self.vector)
        raise TypeError(
            f"No multiplication between Quaternions and '{type(other)}' allowed"
        )

    def __repr__(self) -> str:
        return f"<{self.real:.3f}, {self.vector.x:.3f}, {self.vector.y:.3f}, {self.vector.z:.3f}>"


@dataclass
class Camera:
    pos: pygame.Vector3
    rotation: Quaternion
    center: pygame.Vector2
    fov: pygame.Vector2
    near_z: int
    far_z: int

    def copy(self) -> Camera:
        return copy(self)


@dataclass
class Material:
    # TODO: Use these for lighting?
    ambient_color: pygame.Color = field(default_factory=lambda: pygame.Color("white"))
    diffuse_color: pygame.Color = field(default_factory=lambda: pygame.Color("white"))
    specular_color: pygame.Color = field(default_factory=lambda: pygame.Color("white"))
    # TODO: Use this for transparency?
    transparency: float = 0