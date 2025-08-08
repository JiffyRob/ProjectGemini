from __future__ import annotations

import math
import numpy

import pygame
from pygame.typing import SequenceLike

from gamelibs import interfaces


class Quaternion(interfaces.Quaternion):
    def __init__(
        self, theta: float = 0.0, axis: SequenceLike[float] = (0, 0, 1)
    ) -> None:
        self._real = math.cos(theta / 2)
        self._vector = pygame.Vector3(axis).normalize() * math.sin(theta / 2)

    @property
    def real(self) -> float:
        return self._real
    
    @real.setter
    def real(self, value: float) -> None:
        self._real = value

    @property
    def vector(self) -> pygame.Vector3:
        return self._vector
    
    @vector.setter
    def vector(self, value: pygame.Vector3):
        self._vector = value

    def magnitude(self) -> float:
        return math.sqrt(
            self.real**2 + self.vector.x**2 + self.vector.y**2 + self.vector.z**2
        )

    @classmethod
    def from_standard(
        cls, r: float, i: float, j: float, k: float
    ) -> interfaces.Quaternion:
        result = cls()
        result.real = r
        result.vector.xyz = i, j, k  # type: ignore
        return result

    @classmethod
    def from_degrees(
        cls, real: float = 0.0, axis: SequenceLike[float] = (0, 0, 1)
    ) -> interfaces.Quaternion:
        return cls(real * math.pi / 180, axis)

    def __neg__(self) -> interfaces.Quaternion:
        return self.invert()

    def copy(self) -> interfaces.Quaternion:
        return Quaternion.from_standard(self.real, *self.vector)

    def invert(self) -> interfaces.Quaternion:
        return Quaternion.from_standard(self.real, *-self.vector)

    def dot(self, other: interfaces.Quaternion) -> float:
        return self.real * other.real + sum(
            self.vector.elementwise() * other.vector.elementwise()  # type: ignore
        )

    def nlerp(self, other: interfaces.Quaternion, t: float) -> interfaces.Quaternion:
        a = self
        if self.dot(other) < 0:
            a = self.invert()
        b = other
        return Quaternion.from_standard(
            a.real + t * (b.real - a.real),
            *a.vector + t * (b.vector - a.vector),
        ).normalize()

    def normalize(self) -> interfaces.Quaternion:
        length = math.sqrt(self.real**2 + sum(self.vector.elementwise() ** 2))
        return Quaternion.from_standard(
            self.real / length,
            *self.vector / length,
        )

    def __bool__(self) -> bool:
        return bool(self.vector)

    def __mul__(
        self, other: interfaces.Quaternion | pygame.Vector3 | float
    ) -> interfaces.Quaternion | pygame.Vector3:
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


def translate_points(points: numpy.ndarray, offset: numpy.ndarray) -> None:
    numpy.add(points, offset, points)


def rotate_points(points: numpy.ndarray, quaternion: interfaces.Quaternion) -> None:
    # Equation:
    # sprite_pos + 2 * rot_real * (rot_vec X sprite_pos) + 2 * (rot_vec X (rot_vec X sprite_pos))
    # rot_vec X sprite_pos is used twice, so let's grab that and call it "cross"
    crosses = numpy.cross(quaternion.vector, points)  # type: ignore

    # add 2 * rot_real * cross
    term = numpy.multiply(crosses, 2)  # type: ignore
    numpy.multiply(term, quaternion.real, term)
    numpy.add(points, term, points)

    # add 2 * (camera_vector x (camera_vector x position))
    term = numpy.cross(quaternion.vector, crosses)  # dirty double crosser ;)  # type: ignore
    term = numpy.multiply(term, 2, term)  # type: ignore
    numpy.add(points, term, points)


def project_points_sizes(points: numpy.ndarray, sizes: numpy.ndarray, near_z: float) -> None:
    # Note that this is a linear projection using integer multiplication
    # NOT the curved shape you get with homogenous coordinates and a matmul
    scale_factors = numpy.divide(near_z, points[:, 2]).reshape(len(points), 1)
    numpy.multiply(sizes, scale_factors, sizes)
    numpy.multiply(points[:, :2], scale_factors, points[:, :2])


def inverse_camera_transform_points_sizes(points: numpy.ndarray, sizes: numpy.ndarray, camera: interfaces.Camera3d) -> None:
    # translate
    numpy.add(points, -camera.pos, points)  # type: ignore
    # rotate
    quaternion = camera.rotation.invert()
    crosses = numpy.cross(quaternion.vector, points)  # type: ignore
    term = numpy.multiply(crosses, 2)  # type: ignore
    numpy.multiply(term, quaternion.real, term)
    numpy.add(points, term, points)
    term = numpy.cross(quaternion.vector, crosses)  # dirty double crosser ;)  # type: ignore
    term = numpy.multiply(term, 2, term)  # type: ignore
    numpy.add(points, term, points)
    # scale
    scale_factors = numpy.divide(camera.near_z, points[:, 2]).reshape(len(points), 1)
    numpy.multiply(sizes, scale_factors, sizes)
    numpy.multiply(points[:, :2], scale_factors, points[:, :2])
    # project
    scale_factors = numpy.divide(camera.near_z, points[:, 2]).reshape(len(points), 1)
    numpy.multiply(sizes, scale_factors, sizes)
    numpy.multiply(points[:, :2], scale_factors, points[:, :2])
