import functools
import gzip
import json
import pathlib
from typing import Any
import pygame
from pygame.typing import Point, RectLike

from gamelibs import pixelfont, env, interfaces
from gamelibs.interfaces import FileID
from gamelibs.util_draw import COLORKEY


class Loader(interfaces.Loader):
    def __init__(self) -> None:
        self.base_path = pathlib.Path(".")
        self.asset_path = self.base_path / "assets"
        self.shader_path = self.base_path / "shaders"
        self.data_path = self.base_path / "data"
        self.save_path = self.data_path / "saves"
        self.sound_path = self.base_path / "sound"
        self.music_path = self.base_path / "music"
        self.script_path = self.base_path / "scripts"
        self.cutscene_path = self.base_path / "cutscenes"
        self._font = None

    @property
    def font(self) -> interfaces.PixelFont:
        if self._font is None:
            self._font = pixelfont.PixelFont(self.get_spritesheet("font.png", (7, 8)))
        return self._font

    def postwindow_init(self) -> None:
        pass

    def join(self, path: FileID | pathlib.Path) -> pathlib.Path:
        return pathlib.Path(self.base_path, path)

    def join_asset(self, path: FileID) -> pathlib.Path:
        return self.asset_path / path

    def join_sound(self, path: FileID) -> pathlib.Path:
        return self.sound_path / path

    def join_music(self, path: FileID) -> pathlib.Path:
        return self.music_path / path

    def join_data(self, path: FileID, for_map: bool = False) -> pathlib.Path:
        if for_map:
            # Map data in the asset folder bc that's where ldtk saves it
            return self.join_asset(path)
        return self.data_path / path

    def join_save(self, path: FileID) -> pathlib.Path:
        return self.save_path / path

    def join_script(self, path: FileID) -> pathlib.Path:
        return self.script_path / path

    def join_cutscene(self, path: FileID) -> pathlib.Path:
        return self.cutscene_path / path

    def join_shader(self, path: FileID) -> pathlib.Path:
        return self.shader_path / path

    @functools.cache
    def get_text(self, path: FileID, for_map: bool = False) -> str:  # type: ignore
        with self.join_data(path, for_map).open() as file:
            return file.read()

    @functools.cache
    def get_json(self, path: FileID, for_map: bool = False) -> Any:  # type: ignore
        return json.load(self.join_data(path, for_map).with_suffix(".json").open())

    def save_json(self, path: FileID, data: Any) -> None:
        pathlib_path = self.join_data(path).with_suffix(".json")
        with pathlib_path.open("w") as file:
            file.write(json.dumps(data))

    def get_settings(self) -> interfaces.GameSettings:
        return interfaces.GameSettings(
            **{
                **self.get_json("settings"),
                **env.get_settings(),
            }
        )

    def save_settings(self, settings: interfaces.GameSettings) -> None:
        settings_dict = settings.as_dict()
        self.save_json("settings", settings_dict)
        env.update_settings(settings_dict)
        env.write_settings()

    @functools.cache
    def get_csv(self, path: FileID, item_delimiter: str = ",", line_delimiter: str = "\n", for_map: bool = False) -> tuple[tuple[str, ...], ...]:  # type: ignore
        text = self.get_text(path, for_map)
        lines: list[tuple[str, ...]] = []
        for line in text.split(line_delimiter):
            if not line:
                continue
            lines.append(tuple(line.rstrip(item_delimiter).split(item_delimiter)))
        return tuple(lines)

    @staticmethod
    def convert(surface: pygame.Surface) -> pygame.Surface:
        new_surface = pygame.Surface(surface.get_size()).convert()
        new_surface.fill(COLORKEY)
        new_surface.blit(surface, (0, 0))
        new_surface.set_colorkey(COLORKEY)
        return new_surface

    @classmethod
    def create_surface(cls, size: Point) -> pygame.Surface:
        surface = cls.convert(pygame.Surface(size))
        surface.fill(COLORKEY)
        return surface

    @functools.cache
    def get_surface(self, path: FileID, rect: RectLike | None = None) -> pygame.Surface:  # type: ignore
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
    def get_spritesheet(self, path: FileID, size: Point = (16, 16)) -> tuple[pygame.Surface, ...]:  # type: ignore
        surface = self.get_surface(path)
        rect = pygame.Rect(0, 0, size[0], size[1])
        size_rect = surface.get_rect()
        images: list[pygame.Surface] = []
        while True:
            images.append(surface.subsurface(rect).copy())
            rect.left += size[0]
            if not size_rect.contains(rect):
                rect.left = 0
                rect.top += size[1]
            if not size_rect.contains(rect):
                break
        return tuple(images)

    @functools.cache
    def get_sound(self, path: FileID) -> pygame.Sound:  # type: ignore
        return pygame.mixer.Sound(self.join_sound(path).with_suffix(".ogg"))

    @functools.cache
    def get_script(self, path: FileID) -> str:  # type: ignore
        with self.join_script(path).with_suffix(".snek").open() as file:
            return file.read()

    @functools.cache
    def get_cutscene(self, path: FileID) -> str:  # type: ignore
        with self.join_cutscene(path).with_suffix(".snek").open() as file:
            return file.read()

    @functools.cache
    def get_vertex_shader(self, path: FileID) -> str:  # type: ignore
        with self.join_shader(path).with_suffix(".vert").open() as file:
            return file.read()

    @functools.cache
    def get_fragment_shader(self, path: str) -> str:  # type: ignore
        with self.join_shader(path).with_suffix(".frag").open() as file:
            return file.read()

    @functools.cache
    def get_shader_library(self, path: FileID) -> str:  # type: ignore
        with self.join_shader(path).with_suffix(".glsl").open() as file:
            return file.read()

    # not cached because save files change
    def get_save(self, path: FileID) -> dict[str, Any]:
        pathlib_path = self.join_save(path).with_suffix(".sav")
        if env.PYGBAG and "1" not in str(
            pathlib_path
        ):  # this path is the "new game" save
            return env.get_save(path)
        return json.load(pathlib_path.open())
        # compress save files later - leave for debug
        with gzip.open(path) as file:
            return json.load(file)

    def save_data(self, path: FileID, data: dict[str, Any]) -> None:
        pathlib_path = self.join_save(path).with_suffix(".sav")
        env.update_save(path, data)
        return json.dump(data, pathlib_path.open("w"))
        # compress save files later - leave for debug
        with gzip.open(path, "wb") as file:
            json.dump(data, file)

    def delete_save(self, path: FileID) -> None:
        if env.PYGBAG:
            env.delete_save(path)
            env.write_saves()
        else:
            self.join_save(path).unlink()

    def get_save_names(self, amount: int = 5) -> list[FileID]:
        names: list[FileID] = []
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

    def flush(self) -> None:
        env.write_saves()
        env.write_settings()
