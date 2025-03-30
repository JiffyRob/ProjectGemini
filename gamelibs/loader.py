import functools
import gzip
import json
import pathlib

import pygame

from gamelibs import pixelfont, env
from gamelibs.util_draw import COLORKEY


class Loader:
    def __init__(self):
        self.base_path = pathlib.Path(".")
        self.asset_path = self.base_path / "assets"
        self.shader_path = self.base_path / "shaders"
        self.data_path = self.base_path / "data"
        self.save_path = self.data_path / "saves"
        self.sound_path = self.base_path / "sound"
        self.music_path = self.base_path / "music"
        self.script_path = self.base_path / "scripts"
        self.cutscene_path = self.base_path / "cutscenes"
        self.font = None

    def postwindow_init(self):
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

    def join_script(self, path):
        return self.script_path / path

    def join_cutscene(self, path):
        return self.cutscene_path / path

    def join_shader(self, path):
        return self.shader_path / path

    @functools.cache
    def get_text(self, path, for_map=False):
        with self.join_data(path, for_map).open() as file:
            return file.read()

    @functools.cache
    def get_json(self, path, for_map=False):
        return json.load(self.join_data(path, for_map).with_suffix(".json").open())

    def save_json(self, path, data):
        path = self.join_data(path).with_suffix(".json")
        with path.open("w") as file:
            file.write(json.dumps(data))

    @functools.cache
    def get_settings(self):
        return {
            **self.get_json("settings-default"),
            **self.get_json("settings"),
            **env.get_settings(),
        }

    def save_settings(self, settings):
        overwritten_settings = {}
        default_settings = self.get_json("settings-default")
        for key, value in settings.items():
            if value != default_settings[key]:
                overwritten_settings[key] = value
        self.save_json("settings", overwritten_settings)
        env.update_settings(settings)
        env.write_settings()

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
        path = self.join_sound(path).with_suffix(".ogg")
        return pygame.mixer.Sound(path)

    @functools.cache
    def get_script(self, path):
        path = self.join_script(path).with_suffix(".snek")
        with path.open() as file:
            return file.read()

    @functools.cache
    def get_cutscene(self, path):
        path = self.join_cutscene(path).with_suffix(".snek")
        with path.open() as file:
            return file.read()

    @functools.cache
    def get_vertex_shader(self, path):
        path = self.join_shader(path).with_suffix(".vert")
        with path.open() as file:
            return file.read()

    @functools.cache
    def get_fragment_shader(self, path):
        path = self.join_shader(path).with_suffix(".frag")
        with path.open() as file:
            return file.read()

    @functools.cache
    def get_shader_library(self, path):
        path = self.join_shader(path).with_suffix(".glsl")
        with path.open() as file:
            return file.read()

    # not cached because save files change
    def get_save(self, path):
        path = self.join_save(path).with_suffix(".sav")
        if env.PYGBAG and "1" not in str(path):  # this path is the "new game" save
            return env.get_save(path)
        return json.load(path.open())
        # compress save files later - leave for debug
        with gzip.open(path) as file:
            return json.load(file)

    def save_data(self, path, data):
        path = self.join_save(path).with_suffix(".sav")
        env.update_save(path, data)
        return json.dump(data, path.open("w"))
        # compress save files later - leave for debug
        with gzip.open(path, "wb") as file:
            json.dump(data, file)

    def delete_save(self, path):
        path = self.join_save(path).with_suffix(".sav")
        if env.PYGBAG:
            env.delete_save(path)
            env.write_saves()
        else:
            path.unlink()

    def get_save_names(self, amount=5):
        names = []
        i = 0
        if env.PYGBAG:
            paths = [pathlib.Path(i) for i in env.saves.keys()]
        else:
            paths = self.save_path.glob("*")
        for i, save_path in enumerate(paths):
            if save_path.stem != "start1":
                names.append(save_path.stem)
        if i < amount:
            names.extend(("" for _ in range(amount - i)))
        return names[:amount]

    def flush(self):
        env.write_saves()
        env.write_settings()
