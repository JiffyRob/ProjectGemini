import pathlib

import numpy
import pygame._sdl2 as sdl2

from gamelibs.space import math3d


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
            self.rotation = math3d.Quaternion()
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
