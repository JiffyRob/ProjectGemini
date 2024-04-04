import csv
import functools
import json
import pathlib

import numpy
import pygame
import pygame._sdl2 as sdl2
import pygame._sdl2.video as sdl2  # needed for WASM compat

COLORKEY = (255, 0, 255)
# each surface gets 5 colors
# No 2 palettes have the same colors.
# PALETTE_SURFACE = pygame.image.load("assets/palettes.png").convert(8)
# PALETTES = [
#     numpy.array([PALETTE_SURFACE.get_at((i, j)) for i in range(PALETTE_SURFACE.get_width())], numpy.uint8)
#     for j in range(PALETTE_SURFACE.get_height())
# ]


class Loader:
    def __init__(self):
        self.base_path = pathlib.Path("assets/")

    @functools.cache
    def get_text(self, path):
        with pathlib.Path(self.base_path, path).open() as file:
            return file.read()

    @functools.cache
    def get_json(self, path):
        return json.load((self.base_path / path).open())

    @functools.cache
    def get_csv(self, path, item_delimiter=",", line_delimiter="\n"):
        text = self.get_text(path)
        lines = []
        for line in text.split(line_delimiter):
            if not line:
                continue
            lines.append(line.rstrip(item_delimiter).split(item_delimiter))
        return lines

    @staticmethod
    def convert(surface):
        # for palette swapping
        new_surface = pygame.Surface(surface.get_size()).convert()
        new_surface.fill(COLORKEY)
        new_surface.blit(surface, (0, 0))
        new_surface.set_colorkey(COLORKEY)
        return new_surface

    @classmethod
    def palette_swap(cls, surface, palette_index):
        surface = cls.convert(surface)  # just to be sure
        surface.set_palette(PALETTES[palette_index % len(PALETTES)])
        return surface

    @functools.cache
    def get_surface(self, path):
        return self.convert(
            pygame.image.load(
                pathlib.Path(self.base_path, pathlib.Path(path).with_suffix(".png"))
            )
        )

    @functools.cache
    def get_surface_scaled_by(self, path, factor=(2, 2)):
        path = pathlib.Path(path)
        return self.convert(pygame.transform.scale_by(self.get_surface(path), factor))

    @functools.cache
    def get_surface_scaled_to(self, path, size=(16, 16)):
        path = pathlib.Path(path)
        return self.convert(pygame.transform.scale(self.get_surface(path), size))

    @functools.cache
    def get_spritesheet(self, path, size=(16, 16)):
        surface = self.get_surface(path)
        rect = pygame.Rect(0, 0, size[0], size[1])
        size_rect = surface.get_rect()
        images = []
        while True:
            images.append(surface.subsurface(rect).copy())
            rect.left += size[0]
            if not size_rect.contains(rect):
                rect.left = 0
                rect.top += size[1]
            if not size_rect.contains(rect):
                break
        return images

    @functools.cache
    def get_image(self, path, area=None):
        path = pathlib.Path(path)
        surface = self.get_surface(path)
        if isinstance(area, str):
            area = self.get_json(path.with_suffix(".json"))[area]
        return self.convert(surface.subsurface(area))
