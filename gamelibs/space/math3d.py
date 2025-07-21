import math
from dataclasses import dataclass
from copy import copy

import numpy
import pygame


class Quaternion:
    def __init__(self, theta=0.0, axis=(0, 0, 1)):
        self.real = math.cos(theta / 2)
        self.vector = pygame.Vector3(axis).normalize() * math.sin(theta / 2)

    def magnitude(self):
        return math.sqrt(
            self.real**2 + self.vector.x**2 + self.vector.y**2 + self.vector.z**2
        )

    @classmethod
    def from_standard(cls, r, i, j, k):
        result = cls()
        result.real = r
        result.vector.xyz = i, j, k
        return result

    @classmethod
    def from_degrees(cls, real=0.0, axis=(0, 0, 1)):
        return cls(real * math.pi / 180, axis)

    def __neg__(self):
        return self.invert()

    def copy(self):
        return Quaternion.from_standard(self.real, *self.vector)

    def invert(self):
        return Quaternion.from_standard(self.real, *-self.vector)

    def dot(self, other):
        return self.real * other.real + sum(
            self.vector.elementwise() * other.vector.elementwise()
        )

    def nlerp(self, other, t):
        a = self
        if self.dot(other) < 0:
            a = self.invert()
        b = other
        return Quaternion.from_standard(
            a.real + t * (b.real - a.real),
            *a.vector + t * (b.vector - a.vector),
        ).normalize()

    def normalize(self):
        length = math.sqrt(self.real**2 + sum(self.vector.elementwise() ** 2))
        return Quaternion.from_standard(
            self.real / length,
            *self.vector / length,
        )

    def __bool__(self):
        return bool(self.vector)

    def __mul__(self, other):
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

    def __repr__(self):
        return f"<{self.real:.3f}, {self.vector.x:.3f}, {self.vector.y:.3f}, {self.vector.z:.3f}>"


@dataclass
class Camera:
    pos: pygame.Vector3
    rotation: Quaternion
    center: pygame.Vector2
    fov: pygame.Vector2
    near_z: int
    far_z: int

    def copy(self):
        return copy(self)


@dataclass
class Material:
    # TODO: Use these for lighting?
    ambient_color: pygame.Color = None
    diffuse_color: pygame.Color = None
    specular_color: pygame.Color = None
    # TODO: Use this for transparency?
    transparency: float = None


def translate_points(points, offset):
    numpy.add(points, offset, points)


def rotate_points(points, quaternion):
    # Equation:
    # sprite_pos + 2 * rot_real * (rot_vec X sprite_pos) + 2 * (rot_vec X (rot_vec X sprite_pos))
    # rot_vec X sprite_pos is used twice, so let's grab that and call it "cross"
    crosses = numpy.cross(quaternion.vector, points)

    # add 2 * rot_real * cross
    term = numpy.multiply(crosses, 2)
    numpy.multiply(term, quaternion.real, term)
    numpy.add(points, term, points)

    # add 2 * (camera_vector x (camera_vector x position))
    term = numpy.cross(quaternion.vector, crosses)  # dirty double crosser ;)
    term = numpy.multiply(term, 2, term)
    numpy.add(points, term, points)


def project_points_sizes(points, sizes, near_z):
    # Note that this is a linear projection using integer multiplication
    # NOT the curved shape you get with homogenous coordinates and a matmul
    scale_factors = numpy.divide(near_z, points[:, 2]).reshape(len(points), 1)
    numpy.multiply(sizes, scale_factors, sizes)
    numpy.multiply(points[:, :2], scale_factors, points[:, :2])


def inverse_camera_transform_points_sizes(points, sizes, camera):
    # translate
    numpy.add(points, -camera.pos, points)
    # rotate
    quaternion = camera.rotation.invert()
    crosses = numpy.cross(quaternion.vector, points)
    term = numpy.multiply(crosses, 2)
    numpy.multiply(term, quaternion.real, term)
    numpy.add(points, term, points)
    term = numpy.cross(quaternion.vector, crosses)  # dirty double crosser ;)
    term = numpy.multiply(term, 2, term)
    numpy.add(points, term, points)
    # scale
    scale_factors = numpy.divide(camera.near_z, points[:, 2]).reshape(len(points), 1)
    numpy.multiply(sizes, scale_factors, sizes)
    numpy.multiply(points[:, :2], scale_factors, points[:, :2])
    # project
    scale_factors = numpy.divide(camera.near_z, points[:, 2]).reshape(len(points), 1)
    numpy.multiply(sizes, scale_factors, sizes)
    numpy.multiply(points[:, :2], scale_factors, points[:, :2])


def denormalize_color(r, g, b):
    return pygame.Color(r * 255, g * 255, b * 255)
