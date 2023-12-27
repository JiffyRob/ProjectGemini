import pathlib
import json
import pygame
import pygame._sdl2 as sdl2


class TextureLoader:
    def __init__(self, renderer):
        self.renderer = renderer
        self.cache = {}
        self.base_path = pathlib.Path("assets/")

    def get(self, path, name):
        # TODO: implement file cache
        path = pathlib.Path(path)
        texture = sdl2.Texture.from_surface(self.renderer, pygame.image.load(self.base_path / path.with_suffix(".png")))
        with (self.base_path / path.with_suffix(".json")).open() as file:
            data = json.loads(file.read())
        return sdl2.Image(texture, data[name])