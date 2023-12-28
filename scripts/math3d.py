import math
import pygame
import numpy




def to_simple(homogenous):
    return pygame.Vector3(homogenous[0], homogenous[1], homogenous[2]) / homogenous[3]


class Quaternion:
    def __init__(self, theta=0.0, axis=(0, 0, 1)):
        self.real = math.cos(theta / 2)
        self.vector = pygame.Vector3(axis).normalize() * math.sin(theta / 2)

    def magnitude(self):
        return math.sqrt(self.real ** 2 + self.vector.x ** 2 + self.vector.y ** 2 + self.vector.z ** 2)

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

    def invert(self):
        return Quaternion.from_standard(self.real, *-self.vector)

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
                r1 * k2 + i1 * j2 - j1 * i2 + k1 * r2
            )
        if isinstance(other, pygame.Vector3):
            cross_product = self.vector.cross(other)
            return other + (cross_product * 2 * self.real) + 2 * self.vector.cross(cross_product)
        raise TypeError(f"No multiplication between Quaternions and '{type(other)}' allowed")

    def __repr__(self):
        return f"<{self.real:.3f}, {self.vector.x:.3f}, {self.vector.y:.3f}, {self.vector.z:.3f}>"


