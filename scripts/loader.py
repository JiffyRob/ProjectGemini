import functools
import gzip
import json
import pathlib

import pygame

from scripts import pixelfont
from scripts.util_draw import COLORKEY


class Loader:
    def __init__(self):
        self.base_path = pathlib.Path(".")
        self.asset_path = self.base_path / "assets"
        self.data_path = self.base_path / "data"
        self.save_path = self.data_path / "saves"
        self.sound_path = self.base_path / "sound"
        self.music_path = self.base_path / "music"
        self.font = pixelfont.PixelFont(self.get_spritesheet("font.png", (7, 8)))

    def join(self, path):
        return pathlib.Path(self.base_path, path)

    def join_asset(self, path):
        return self.asset_path / path

    def join_sound(self, path):
        return self.sound_path / path

    def join_music(self, path):
        return self.music_path / path

    def join_data(self, path, for_map=False):
        if for_map:
            # Map data in the asset folder bc that's where ldtk saves it
            return self.join_asset(path)
        return self.data_path / path

    def join_save(self, path):
        return self.save_path / path

    @functools.cache
    def get_text(self, path, for_map=False):
        with self.join_data(path, for_map).open() as file:
            return file.read()

    @functools.cache
    def get_json(self, path, for_map=False):
        return json.load(self.join_data(path, for_map).with_suffix(".json").open())

    @functools.cache
    def get_csv(self, path, item_delimiter=",", line_delimiter="\n", for_map=False):
        text = self.get_text(path, for_map)
        lines = []
        for line in text.split(line_delimiter):
            if not line:
                continue
            lines.append(line.rstrip(item_delimiter).split(item_delimiter))
        return lines

    @staticmethod
    def convert(surface):
        new_surface = pygame.Surface(surface.get_size()).convert()
        new_surface.fill(COLORKEY)
        new_surface.blit(surface, (0, 0))
        new_surface.set_colorkey(COLORKEY)
        return new_surface

    @classmethod
    def create_surface(cls, size):
        surface = cls.convert(pygame.Surface(size))
        surface.fill(COLORKEY)
        return surface

    @functools.cache
    def get_surface(self, path, rect=None):
        if rect:
            return self.convert(
                pygame.image.load(self.join_asset(path).with_suffix(".png")).subsurface(
                    rect
                )
            )
        else:
            return self.convert(
                pygame.image.load(self.join_asset(path).with_suffix(".png"))
            )

    @functools.cache
    def get_surface_scaled_by(self, path, factor=(2, 2)):
        return self.convert(pygame.transform.scale_by(self.get_surface(path), factor))

    @functools.cache
    def get_surface_scaled_to(self, path, size=(16, 16)):
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

    @functools.cache
    def get_sound(self, path):
        path = self.join_sound(path).with_suffix(".wav")
        return pygame.mixer.Sound(path)

    # not cached because save files change
    def get_save(self, path):
        path = self.join_save(path).with_suffix(".sav")
        return json.load(path.open())
        # compress save files later - leave for debug
        with gzip.open(path) as file:
            return json.load(file)

    def save_data(self, path, data):
        path = self.join_save(path).with_suffix(".sav")
        return json.dump(data, path.open("w"))
        # compress save files later - leave for debug
        with gzip.open(path, "wb") as file:
            json.dump(data, file)

    def get_save_names(self, amount=5):
        names = []
        i = 0
        for i, save_path in enumerate(self.save_path.glob("*")):
            names.append(save_path.stem)
        if i < amount:
            names.extend(("" for _ in range(amount - i)))
        return names[:amount]
