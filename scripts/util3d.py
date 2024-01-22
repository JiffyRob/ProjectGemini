import math
import pathlib
from dataclasses import dataclass

import pygame
import pygame._sdl2 as sdl2
import numpy

class Quaternion:
    def __init__(self, theta=0.0, axis=(0, 0, 1)):
        self.real = math.cos(theta / 2)
        self.vector = pygame.Vector3(axis).normalize() * math.sin(theta / 2)

    def magnitude(self):
        return math.sqrt(
            self.real**2
            + self.vector.x**2
            + self.vector.y**2
            + self.vector.z**2
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
                r1 * k2 + i1 * j2 - j1 * i2 + k1 * r2,
            )
        if isinstance(other, pygame.Vector3):
            cross_product = self.vector.cross(other)
            return (
                other
                + (cross_product * 2 * self.real)
                + 2 * self.vector.cross(cross_product)
            )
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


class Model:
    obj_cache = {}

    def __init__(self, faces, pos=None, rotation=None):
        # face format: [[polygon-vertexes, face-normals, uv-texture-coordinates, material (An SDL2 Texture)
        self.face_count = len(faces)
        self.vertexes = numpy.zeros((self.face_count, 4, 3), numpy.float64)
        self.is_quad = numpy.zeros((self.face_count,), numpy.bool_)
        # TODO: Normal implementation
        self.uvs = numpy.zeros((self.face_count, 2), numpy.float64)
        self.materials = numpy.zeros((self.face_count,), sdl2.Image)
        spare = [[numpy.nan, numpy.nan, numpy.nan]]

        for i, (vertexes, normals, uvs, material) in enumerate(faces):
            if len(vertexes == 3):
                self.vertexes[i] = vertexes + spare
                self.uvs[i] = uvs + spare
            elif len(vertexes == 4):
                self.vertexes[i] = vertexes
                self.uvs[i] = uvs
                self.is_quad[i] = True
            # TODO: Normal implementation
            self.materials[i] = material

        if pos is None:
            self.pos = pygame.Vector3()
        else:
            self.pos = pygame.Vector3(pos)
        if rotation is None:
            self.rotation = Quaternion()
        else:
            self.rotation = rotation

    @classmethod
    def load_material_library(cls, path):
        materials = {}
        current_key = None
        with path.open("r") as file:
            for line in file.readlines():
                if line[0] == "#":
                    continue

                values = line.split()
                if not values:
                    continue

                match values:
                    case ["newmtl", name]:
                        materials[name] = Material()
                    case ["Ka", r, g, b] if current_key is not None:
                        materials[current_key].ambient_color = denormalize_color(
                            r, g, b
                        )
                    case ["Kd", r, g, b] if current_key is not None:
                        materials[current_key].diffuse_color = denormalize_color(
                            r, g, b
                        )
                    case ["Ks", r, g, b] if current_key is not None:
                        materials[current_key].specular_color = denormalize_color(
                            r, g, b
                        )
                    case ["d", n] if current_key is not None:
                        materials[current_key].transparency = 1 - n
                    case ["Tr", n] if current_key is not None:
                        materials[current_key].transparency = n
                    case _:
                        print(
                            f"File {path}: line {line} contains incorrect syntax or is not supported"
                        )

    @classmethod
    def from_files(cls, path, texture_path=None, pos=None, rotation=None, cache=True):
        vertices = []
        normals = []
        texcoords = []
        faces = []
        material = None
        path = pathlib.Path(path)
        if texture_path:
            texture_path = pathlib.Path(texture_path)
        with path.open("r") as file:
            for line in file.readlines():
                if line[0] == "#":
                    continue

                values = line.split()
                if not values:
                    continue

                match values:
                    case ["v", x, y, z, *_]:
                        vertices.append([float(x), float(y), float(z)])
                    case ["vn", x, y, z, *_]:
                        normals.append([float(x), float(y), float(z)])
                    case ["vt", x, y, *_]:
                        texcoords.append([float(x), float(y)])
                    case ["mtllib", name]:
                        cls.load_material_library(path / name)
                    case ["usemtl", mat] | ["usemat", mat]:
                        material = mat
                    case ["f", *verts]:
                        face = []
                        face_texcoords = []
                        face_normals = []
                        for vert in verts:
                            vert += "/" * (
                                3 - vert.count("/")
                            )  # add implicit slashes for easier parsing
                            vertex_index, texture_index, normal_index, *_ = vert.split(
                                "/"
                            )
                            face.append(vertex_index)
                            if texture_index:
                                face_texcoords.append(int(texture_index))
                            if normal_index:
                                face_normals.append(int(normal_index))
                        faces.append([face, normals, texcoords, material])
                    case _:
                        print(
                            f"File {path}: line {line} contains incorrect syntax or is not supported"
                        )
