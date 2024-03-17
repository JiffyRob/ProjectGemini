import numpy
import pygame
from scripts.animation import AnimatedSurface
from scripts.space import math3d


class StaticSpriteGroup:
    def __init__(self, level, sprites=1000, lod=4):
        self.level = level
        self.sprite_count = sprites

        self.global_positions = numpy.zeros((self.sprite_count, 3), dtype=numpy.float64)  # x, y, z
        self.global_sizes = numpy.zeros((self.sprite_count, 2), dtype=numpy.float64)  # width, height

        self.screen_positions = numpy.zeros((self.sprite_count, 3), dtype=numpy.float64)  # x, y, z
        self.screen_sizes = numpy.zeros((self.sprite_count, 2), dtype=numpy.float64)  # width, height

        self.sprite_texture_ids = numpy.zeros((self.sprite_count,), dtype=numpy.uint8)
        self.sprite_texture_sub_ids = numpy.zeros((self.sprite_count,), dtype=numpy.uint8)
        self.texture_sizes = numpy.zeros((256, lod, 2), dtype=numpy.int32)
        self.textures = numpy.zeros((256, lod), dtype=object)
        self.texture_names = {}
        self.next_texture_id = 0

        self.draw_indices = None

        # preallocate memory for transform data
        self.cross_buffer = numpy.zeros((self.sprite_count,), dtype=numpy.float64)
        self.texture_difference_buffer = numpy.zeros((self.sprite_count, lod, 2), dtype=numpy.float64)
        self.mod_array = numpy.zeros((6,), dtype=numpy.float64)
        self.ids = numpy.arange(self.sprite_count)

        self.next_id = 0
        self.next_texture_id = 0

    def update(self, dt):
        for texture_list in self.textures[: self.next_texture_id]:
            for texture in texture_list:
                if isinstance(texture, AnimatedSurface):
                    texture.update(dt)

    def add_textures(self, name, data):
        texture_id = self.next_texture_id
        self.texture_names[name] = texture_id
        for i, value in enumerate(data.values()):
            self.textures[texture_id][i] = value
        keys = tuple(data.keys())
        self.texture_sizes[texture_id][: len(keys)] = keys
        self.next_texture_id += 1

    def add_sprite(self, position, texture, size=(16, 16)):
        texture_id = self.texture_names[texture]

        self.sprite_texture_ids[self.next_id] = texture_id
        self.global_positions[self.next_id] = pygame.Vector3(position)
        self.global_sizes[self.next_id] = size
        self.next_id += 1
        return self.next_id - 1

    def finalize(self, camera):
        # move to camera center
        numpy.add(
            self.screen_positions[: self.next_id],
            (*camera.center, 0),
            self.screen_positions[: self.next_id],
        )
        # texture matching (get best size texture for computed object size)
        numpy.subtract(
            self.screen_sizes.reshape(self.sprite_count, 1, 2)[: self.next_id],
            self.texture_sizes[self.sprite_texture_ids][: self.next_id],
            self.texture_difference_buffer,
        )
        numpy.argmin(
            numpy.linalg.norm(self.texture_difference_buffer[: self.next_id], axis=2),
            axis=1,
            out=self.sprite_texture_sub_ids[: self.next_id],
        )
        self.screen_sizes[: self.next_id] = self.texture_sizes[self.sprite_texture_ids, self.sprite_texture_sub_ids][: self.next_id]
        # top left positioning
        numpy.subtract(
            self.screen_positions[: self.next_id][:, :2],
            self.screen_sizes[: self.next_id] / 2,
            self.screen_positions[: self.next_id][:, :2],
        )
        # don't draw things outside view area
        zs = self.screen_positions[: self.next_id][:, 2]
        indices = numpy.argsort(-zs)
        zs = zs[indices]
        xs = self.screen_sizes[: self.next_id][:, 0][indices]
        ys = self.screen_sizes[: self.next_id][:, 1][indices]

        self.draw_indices = self.ids[: self.next_id][indices][
            (zs >= 0) & (zs <= camera.far_z) & (xs >= 0) & (ys >= 0) & (xs <= camera.center.x * 2) & (ys <= camera.center.y * 2)
        ]

    def get_rect(self, id):
        if id in self.draw_indices:
            return pygame.FRect(tuple(self.screen_positions[id][:2]), tuple(self.screen_sizes[id]))
        return pygame.FRect(0, 0, 0, 0)

    def distance(self, id):
        return pygame.Vector3(tuple(self.screen_positions[id])).length()

    def draw(self):
        self.level.game.window_surface.fblits(
            (
                zip(
                    self.textures[self.sprite_texture_ids, self.sprite_texture_sub_ids][self.draw_indices],
                    self.screen_positions[:, :2][self.draw_indices],
                )
            )
        )

    def dirty_draw(self, camera):
        # copy
        numpy.copyto(self.screen_positions[: self.next_id], self.global_positions[: self.next_id])
        numpy.copyto(self.screen_sizes[: self.next_id], self.global_sizes[: self.next_id])
        math3d.inverse_camera_transform_points_sizes(
            self.screen_positions[: self.next_id],
            self.screen_sizes[: self.next_id],
            camera,
        )
        # center on screen + culling
        self.finalize(camera)
        # now that positions are nice, draw properly
        self.draw()

