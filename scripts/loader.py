import json
import pathlib

import pygame
import pygame._sdl2 as sdl2


class Loader:
    def __init__(self, renderer):
        self.renderer = renderer
        self.cache = {}
        self.base_path = pathlib.Path("assets/")

    def get_text(self, path):
        if path not in self.cache:
            with open("path", "r") as file:
                self.cache[path] = file.read()

    def get_texture(self, path, name):
        # TODO: implement file cache
        path = pathlib.Path(path)
        key = f"{path}$+${name}"  # if a file path follows THIS format it's the developer's problem
        if key not in self.cache:
            texture = sdl2.Texture.from_surface(
                self.renderer,
                pygame.image.load(self.base_path / path.with_suffix(".png")),
            )
            with (self.base_path / path.with_suffix(".json")).open() as file:
                data = json.loads(file.read())
            self.cache[key] = sdl2.Image(texture, data[name])
        return self.cache[key]
