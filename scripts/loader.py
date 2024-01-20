import json
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
    def get_surface(self, path):
        return pygame.image.load(pathlib.Path(self.base_path, path))

    @functools.cache
    def get_texture(self, path, name):
        path = pathlib.Path(path)
        key = f"{path}$+${name}"  # if a file path follows THIS format it's the developer's problem
        texture = sdl2.Texture.from_surface(
            self.renderer,
            self.get_surface(path.with_suffix(".png")),
        )
        return sdl2.Image(texture, self.get_json(path.with_suffix(".json"))[name])
