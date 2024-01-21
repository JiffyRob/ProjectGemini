import json
import csv
import pathlib

import pygame
import pygame._sdl2 as sdl2
import functools


class Loader:
    def __init__(self, renderer):
        self.renderer = renderer
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

    @functools.cache
    def get_surface(self, path):
        return pygame.image.load(pathlib.Path(self.base_path, path))

    @functools.cache
    def get_texture(self, path):
        path = pathlib.Path(path)
        texture = sdl2.Texture.from_surface(
            self.renderer,
            self.get_surface(path.with_suffix(".png")),
        )
        return texture

    @functools.cache
    def get_image(self, path, area=None):
        path = pathlib.Path(path)
        texture = self.get_texture(path)
        if isinstance(area, str):
            area = self.get_json(path.with_suffix(".json"))[area]
        return sdl2.Image(texture, area)
