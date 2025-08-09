from enum import Enum, IntFlag, StrEnum, IntEnum, auto
from typing import Callable, Any, Iterable, Iterator, Protocol, runtime_checkable
from pygame.typing import ColorLike, RectLike, Point, SequenceLike
from pygame.math import Vector2
from dataclasses import dataclass
from copy import copy
from numpy import ndarray
from pathlib import Path

import zengl
import pygame
from SNEK2 import SNEKCallable, AsyncSNEKCallable  # type: ignore

type SnekAPI = dict[
    str, SNEKCallable | AsyncSNEKCallable | Any
] | None  # TODO: this could be more specific

type MiscRect = pygame.Rect | pygame.FRect

type FileID = "str"


class Axis(IntFlag):
    X = auto()
    Y = auto()
    Z = auto()


class MapType(StrEnum):
    TOPDOWN = "TopDown"
    PLATFORMER = "Platformer"
    HOUSE = "House"
    HOVERBOARD = "Hoverboard"
    SPACE = "Space"


class Direction(StrEnum):
    UP = "up"
    DOWN = "down"
    LEFT = "left"
    RIGHT = "right"

    def get_axis(self) -> Axis:
        if self.value in {"up", "down"}:
            return Axis.Y
        return Axis.X

    def to_vector(self) -> Vector2:
        return Vector2(
            {
                self.UP: (0, -1),
                self.DOWN: (0, 1),
                self.LEFT: (-1, 0),
                self.RIGHT: (1, 0),
            }[self]
        )

    def to_tuple(self) -> tuple[int, int]:
        return {
            self.UP: (0, -1),
            self.DOWN: (0, 1),
            self.LEFT: (-1, 0),
            self.RIGHT: (1, 0),
        }[self]

    def reverse(self) -> "Direction":
        cls = self.__class__
        return {
            self.UP: cls.DOWN,
            self.DOWN: cls.UP,
            self.LEFT: cls.RIGHT,
            self.RIGHT: cls.LEFT,
        }[self]

    @classmethod
    def from_vector(cls, vector: Vector2) -> "Direction":
        if abs(vector.x) > abs(vector.y):
            return cls.RIGHT if vector.x > 0 else cls.LEFT
        return cls.DOWN if vector.y > 0 else cls.UP


class MapEntranceType(Enum):
    NORMAL = auto()
    FALLING = auto()
    HOVERBOARD = auto()


class InteractionResult(Enum):
    FAILED = auto()
    NO_MORE = auto()
    MORE = auto()


class GraphicsSetting(StrEnum):
    LOWEST = "budget potato"
    LOW = "average potato"
    MEDIUM = "snazzy potato"
    HIGH = "expensive potato"
    ULTRA = "ludicrous potato"


class ScaleMode(StrEnum):
    INTEGER = "integer"
    STRETCH = "stretch"
    ASPECT = "aspect"


class FrameCap(IntEnum):
    LOW = 15
    MEDIUM = 30
    HIGH = 60
    # Physics can't handle this RN :(
    # NONE = 0


class JumpCause(Enum):
    PAIN = auto()
    NORMAL = auto()
    BOOSTED = auto()
    KNIFE = auto()


@dataclass
class Camera3d:
    pos: pygame.Vector3
    rotation: "Quaternion"
    center: pygame.Vector2
    fov: pygame.Vector2
    near_z: int
    far_z: int

    def copy(self) -> "Camera3d":
        return copy(self)


@dataclass
class GameSettings:
    vsync: bool = True
    fullscreen: bool = False
    scale: ScaleMode = ScaleMode.ASPECT
    framecap: FrameCap = FrameCap.HIGH
    graphics: GraphicsSetting = GraphicsSetting.MEDIUM

    def as_dict(self) -> dict[str, Any]:
        return {
            "vsync": self.vsync,
            "fullscreen": self.fullscreen,
            "scale": self.scale.value,
            "framecap": self.framecap.value,
            "graphics": self.graphics.value,
        }

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> "GameSettings":
        return cls(
            vsync=d["vsync"],
            fullscreen=d["fullscreen"],
            scale=ScaleMode(d["scale"]),
            framecap=FrameCap(d["framecap"]),
            graphics=GraphicsSetting(d["graphics"]),
        )

    def update(self, other: "GameSettings") -> None:
        for field in other.fields():
            setattr(self, *field)

    def fields(self) -> Iterator[tuple[str, Any]]:
        for field in {"vsync", "fullscreen", "scale", "framecap", "graphics"}:
            yield field, getattr(self, field)


@runtime_checkable
class Quaternion(Protocol):
    def magnitude(self) -> float:
        raise NotImplementedError

    @classmethod
    def from_standard(cls, r: float, i: float, j: float, k: float) -> "Quaternion":
        raise NotImplementedError

    @classmethod
    def from_degrees(
        cls, real: float = 0.0, axis: SequenceLike[float] = (0, 0, 1)
    ) -> "Quaternion":
        raise NotImplementedError

    def __neg__(self) -> "Quaternion":
        raise NotImplementedError

    def copy(self) -> "Quaternion":
        raise NotImplementedError

    def invert(self) -> "Quaternion":
        raise NotImplementedError

    def dot(self, other: "Quaternion") -> float:
        raise NotImplementedError

    def nlerp(self, other: "Quaternion", t: float) -> "Quaternion":
        raise NotImplementedError

    def normalize(self) -> "Quaternion":
        raise NotImplementedError

    def __bool__(self) -> bool:
        raise NotImplementedError

    def __mul__(
        self, other: "Quaternion | pygame.Vector3 | float"
    ) -> "Quaternion | pygame.Vector3":
        raise NotImplementedError

    def __repr__(self) -> str:
        raise NotImplementedError

    @property
    def real(self) -> float:
        raise NotImplementedError

    @real.setter
    def real(self, value: float) -> None:
        raise NotImplementedError

    @property
    def vector(self) -> pygame.Vector3:
        raise NotImplementedError

    @vector.setter
    def vector(self, value: pygame.Vector3) -> None:
        raise NotImplementedError


@runtime_checkable
class GameSave(Protocol):
    def get_state(self, key: str) -> Any:
        raise NotImplementedError

    def set_state(self, key: str, value: Any) -> None:
        raise NotImplementedError

    def get_tmp(self, key: str) -> Any:
        raise NotImplementedError

    def set_tmp(self, key: str, value: Any) -> None:
        raise NotImplementedError

    def new(self, name: str) -> FileID:
        raise NotImplementedError

    def load(self, path: FileID | None) -> None:
        raise NotImplementedError

    def save(self, path: FileID | None = None) -> None:
        raise NotImplementedError

    def delete(self, path: FileID | None = None) -> None:
        raise NotImplementedError

    @property
    def loaded_path(self) -> FileID:
        raise NotImplementedError


@runtime_checkable
class SoundManager(Protocol):
    def play_sound(
        self,
        path: FileID,
        priority: int = 10,
        loops: int = 0,
        volume: float = 1,
        fade_ms: int = 0,
        polar_location: tuple[int, int] = (0, 0),
    ) -> bool:
        raise NotImplementedError

    def set_sound_volume(self, value: float) -> None:
        raise NotImplementedError

    def get_sound_value(self) -> float:
        raise NotImplementedError

    def set_music_volume(self, value: float) -> None:
        raise NotImplementedError

    def get_music_volume(self) -> float:
        raise NotImplementedError

    def switch_track(
        self,
        track: FileID | None = None,
        volume: float = 1,
        loops: int = -1,
        start: float = 0.0,
        fade_ms: int = 0,
    ) -> None:
        raise NotImplementedError

    def stop_track(self) -> None:
        raise NotImplementedError


@runtime_checkable
class InputQueue(Protocol):
    def rumble(self, left: float = 1, right: float = 1, time: int = 500) -> None:
        raise NotImplementedError

    def stop_rumble(self) -> None:
        raise NotImplementedError

    def update(self, events: Iterable[pygame.Event] | None = None) -> None:
        raise NotImplementedError

    def load_bindings(
        self, bindings: dict[str, set[str | None]], delete_old: bool = True
    ) -> None:
        raise NotImplementedError

    @property
    def held(self) -> set[str]:
        raise NotImplementedError

    @property
    def just_pressed(self) -> set[str]:
        raise NotImplementedError


@runtime_checkable
class PixelFont(Protocol):
    def size(self, text: str, width: int = 0) -> tuple[int, int]:
        raise NotImplementedError

    def render_to(self, surface: pygame.Surface, rect: RectLike, text: str) -> None:
        raise NotImplementedError

    def render(self, text: str, width: int = 0) -> pygame.Surface:
        raise NotImplementedError


@runtime_checkable
class Sprite(Protocol):
    groups: set[str]

    def attach(self, other: "Sprite") -> None:
        raise NotImplementedError

    def detach(self) -> None:
        raise NotImplementedError

    def message(self, message: str) -> None:
        raise NotImplementedError

    def hide(self) -> None:
        raise NotImplementedError

    def show(self) -> None:
        raise NotImplementedError

    def lock(self) -> None:
        raise NotImplementedError

    def unlock(self) -> None:
        raise NotImplementedError

    @property
    def pos(self) -> pygame.Vector2:
        raise NotImplementedError

    @property
    def z(self) -> int:
        raise NotImplementedError

    @z.setter
    def z(self, value: int) -> None:
        raise NotImplementedError

    @property
    def rect(self) -> MiscRect:
        raise NotImplementedError

    @rect.setter
    def rect(self, value: MiscRect) -> None:
        raise NotImplementedError

    @property
    def to_draw(self) -> pygame.Surface:
        raise NotImplementedError

    def update(self, dt: float) -> bool:
        raise NotImplementedError

    def add_effect(self, effect: "SpriteEffect") -> None:
        raise NotImplementedError

    def get_player(self) -> "Player":
        raise NotImplementedError

    def get_level(self) -> "Level":
        raise NotImplementedError

    def get_game(self) -> "Game":
        raise NotImplementedError


@runtime_checkable
class GUISprite(Sprite, Protocol):
    def draw(self, surface: pygame.Surface) -> None:
        raise NotImplementedError


@runtime_checkable
class PlatformerSprite(Sprite, Protocol):
    def get_player(self) -> "PlatformerPlayer":
        raise NotImplementedError

    def get_level(self) -> "PlatformerLevel":
        raise NotImplementedError


@runtime_checkable
class Healthy(Protocol):
    @property
    def health(self) -> int:
        raise NotImplementedError

    @health.setter
    def health(self, value: int) -> None:
        raise NotImplementedError

    @property
    def max_health(self) -> int:
        raise NotImplementedError

    @max_health.setter
    def max_health(self, value: int) -> None:
        raise NotImplementedError

    def hurt(self, amount: int) -> None:
        raise NotImplementedError

    def heal(self, amount: int) -> None:
        raise NotImplementedError


@runtime_checkable
class Interactor(Protocol):
    @property
    def interaction_rect(self) -> MiscRect:
        raise NotImplementedError

    def interact(self) -> InteractionResult:
        raise NotImplementedError


@runtime_checkable
class PuzzleTrigger(Protocol):
    def triggered(self) -> bool:
        raise NotImplementedError

    @property
    def collision_rect(self) -> MiscRect:
        raise NotImplementedError


@runtime_checkable
class Collider(Protocol):
    @property
    def collision_rect(self) -> MiscRect:
        raise NotImplementedError


@runtime_checkable
class Pickup(Protocol):
    @property
    def collision_rect(self) -> MiscRect:
        raise NotImplementedError


@runtime_checkable
class Turner(Protocol):
    @property
    def facing(self) -> Direction:
        raise NotImplementedError


@runtime_checkable
class Player(Sprite, Healthy, Collider, Turner, Protocol):
    @property
    def emeralds(self) -> int:
        raise NotImplementedError

    @emeralds.setter
    def emeralds(self, value: int) -> None:
        raise NotImplementedError

    def pay(self, emeralds: int) -> None:
        raise NotImplementedError

    def charge(self, emeralds: int) -> None:
        raise NotImplementedError

    @property
    def head_rect(self) -> MiscRect:
        raise NotImplementedError

    def get_inventory(self, name: str) -> int:
        raise NotImplementedError

    def acquire(self, thing: str, count: int) -> bool:
        raise NotImplementedError


@runtime_checkable
class HoverboardPlayer(Player, Protocol):
    def exit(self) -> None:
        raise NotImplementedError


@runtime_checkable
class PlatformerPlayer(Player, Protocol):
    def jump(self, cause: JumpCause, just: bool = False) -> None:
        raise NotImplementedError


@runtime_checkable
class GlobalEffect(Protocol):
    def update(self, dt: float) -> bool:
        raise NotImplementedError

    def draw(self, surface: pygame.Surface) -> None:
        raise NotImplementedError

    def draw_over(self, dest_surface: pygame.Surface, dest_rect: MiscRect) -> None:
        raise NotImplementedError

    @property
    def done(self) -> bool:
        raise NotImplementedError

    @done.setter
    def done(self, value: bool) -> None:
        raise NotImplementedError


@runtime_checkable
class SpriteEffect(Protocol):
    def update(self, dt: float) -> bool:
        raise NotImplementedError

    def draw(self, surface: pygame.Surface) -> None:
        raise NotImplementedError


@runtime_checkable
class Animation(Protocol):
    def update(self, dt: float) -> None:
        raise NotImplementedError

    def restart(self) -> None:
        raise NotImplementedError

    def done(self) -> bool:
        raise NotImplementedError

    @property
    def image(self) -> pygame.Surface:
        raise NotImplementedError

    @property
    def flip_x(self) -> bool:
        raise NotImplementedError

    @flip_x.setter
    def flip_x(self, value: bool) -> None:
        raise NotImplementedError

    @property
    def flip_y(self) -> bool:
        raise NotImplementedError

    @flip_y.setter
    def flip_y(self, value: bool) -> None:
        raise NotImplementedError


@runtime_checkable
class _Timer(Protocol):
    def time_left(self) -> float:
        raise NotImplementedError

    def percent_complete(self) -> float:
        raise NotImplementedError

    def done(self) -> bool:
        raise NotImplementedError

    def reset(self) -> None:
        raise NotImplementedError

    def finish(self) -> None:
        raise NotImplementedError


@runtime_checkable
class Timer(_Timer, Protocol):
    def update(self) -> None:
        raise NotImplementedError


@runtime_checkable
class DTimer(_Timer, Protocol):
    def update(self, dt: float) -> None:
        raise NotImplementedError


@runtime_checkable
class Loader(Protocol):
    def postwindow_init(self) -> None:
        raise NotImplementedError

    @property
    def font(self) -> PixelFont:
        raise NotImplementedError

    def join(self, path: FileID | Path) -> Path:
        raise NotImplementedError

    def get_text(self, path: FileID, for_map: bool = False) -> str:
        raise NotImplementedError

    def get_json(self, path: FileID, for_map: bool = False) -> Any:
        raise NotImplementedError

    def save_json(self, path: FileID, data: dict[str, Any]) -> None:
        raise NotImplementedError

    def get_settings(self) -> GameSettings:
        raise NotImplementedError

    def save_settings(self, settings: GameSettings) -> None:
        raise NotImplementedError

    def get_csv(
        self,
        path: FileID,
        item_delimiter: str = ",",
        line_delimiter: str = "\n",
        for_map: bool = False,
    ) -> list[str]:
        raise NotImplementedError

    @staticmethod
    def convert(surface: pygame.Surface) -> pygame.Surface:
        raise NotImplementedError

    @classmethod
    def create_surface(cls, size: Point) -> pygame.Surface:
        raise NotImplementedError

    def get_surface(self, path: FileID, rect: RectLike | None = None) -> pygame.Surface:
        raise NotImplementedError

    def get_spritesheet(
        self, path: FileID, size: Point = (16, 16)
    ) -> tuple[pygame.Surface, ...]:
        raise NotImplementedError

    def get_sound(self, path: FileID) -> pygame.mixer.Sound:
        raise NotImplementedError

    def get_script(self, path: FileID) -> str:
        raise NotImplementedError

    def get_cutscene(self, path: FileID) -> str:
        raise NotImplementedError

    def get_vertex_shader(self, path: FileID) -> str:
        raise NotImplementedError

    def get_fragment_shader(self, path: FileID) -> str:
        raise NotImplementedError

    def get_shader_library(self, path: FileID) -> str:
        raise NotImplementedError

    def get_save(self, path: FileID) -> dict[str, Any]:
        raise NotImplementedError

    def save_data(self, path: FileID, data: dict[str, Any]) -> None:
        raise NotImplementedError

    def delete_save(self, path: FileID) -> None:
        raise NotImplementedError

    def get_save_names(self, amount: int = 5) -> list[tuple[str, FileID]]:
        raise NotImplementedError
    
    def get_save_count(self) -> int:
        raise NotImplementedError

    def flush(self) -> None:
        raise NotImplementedError


@runtime_checkable
class Game(Protocol):
    def push_state(self, state: "GameState") -> None:
        raise NotImplementedError

    def pop_state(self) -> None:
        raise NotImplementedError

    def get_state(self) -> "GameState":
        raise NotImplementedError

    def get_gl_context(self) -> zengl.Context:
        raise NotImplementedError

    def get_current_planet_name(self) -> FileID:
        raise NotImplementedError

    def run_cutscene(self, name: FileID, api: SnekAPI = None) -> None:
        raise NotImplementedError

    async def run_sub_cutscene(self, name: FileID, api: SnekAPI) -> None:
        raise NotImplementedError

    @property
    def mouse_pos(self) -> Point:
        raise NotImplementedError

    @property
    def window_surface(self) -> pygame.Surface:
        raise NotImplementedError

    @property
    def gl_window_surface(self) -> zengl.Image:
        raise NotImplementedError

    def set_graphics(self, value: GraphicsSetting) -> None:
        raise NotImplementedError

    def switch_setting(self, name: str, value: Any) -> None:
        raise NotImplementedError

    def load_map(
        self,
        map_name: FileID,
        direction: Direction | None = None,
        position: Point | None = None,
        entrance: MapEntranceType = MapEntranceType.NORMAL,
    ) -> None:
        raise NotImplementedError

    def switch_level(
        self,
        level_name: FileID,
        direction: Direction | None = None,
        position: Point | None = None,
        entrance: MapEntranceType = MapEntranceType.NORMAL,
    ) -> None:
        raise NotImplementedError

    def exit_level(self) -> None:
        raise NotImplementedError

    def load_save(self, save_name: FileID) -> None:
        raise NotImplementedError

    def delayed_callback(self, dt: float, callback: Callable[[], Any]) -> None:
        raise NotImplementedError

    def load_input_binding(self, name: FileID) -> None:
        raise NotImplementedError

    def add_input_binding(self, name: FileID) -> None:
        raise NotImplementedError

    def play_soundtrack(self, track_name: FileID) -> None:
        raise NotImplementedError

    async def run(self) -> None:
        raise NotImplementedError

    def save_to_disk(self) -> None:
        raise NotImplementedError

    def quit(self) -> None:
        raise NotImplementedError

    def exit(self) -> None:
        raise NotImplementedError


@runtime_checkable
class GameState(Protocol):
    def on_push(self) -> None:
        raise NotImplementedError

    def on_pop(self) -> None:
        raise NotImplementedError

    def pop(self) -> None:
        raise NotImplementedError

    def update(self, dt: float) -> bool:
        raise NotImplementedError

    def draw(self) -> None:
        raise NotImplementedError

    def get_game(self) -> Game:
        raise NotImplementedError

    @property
    def opengl(self) -> bool:
        raise NotImplementedError

    @property
    def bgcolor(self) -> ColorLike:
        raise NotImplementedError

    @bgcolor.setter
    def bgcolor(self, value: ColorLike) -> None:
        raise NotImplementedError


@runtime_checkable
class Background(Protocol):
    def update(self, dt: float) -> None:
        raise NotImplementedError

    def draw(self, surface: pygame.Surface, offset: Point) -> None:
        raise NotImplementedError

    @property
    def rect(self) -> MiscRect:
        raise NotImplementedError

    def lock(self) -> None:
        raise NotImplementedError

    def unlock(self) -> None:
        raise NotImplementedError


@runtime_checkable
class Level(GameState, Protocol):
    def shake(
        self, magnitude: float = 5.0, delta: float = 8, axis: Axis = Axis.X | Axis.Y
    ) -> None:
        raise NotImplementedError

    async def attempt_map_cutscene(self) -> None:
        raise NotImplementedError
    
    def attach(self, base: str, follower: str="player") -> None:
        raise NotImplementedError

    def lock(self, group: str | None=None) -> None:
        raise NotImplementedError

    def unlock(self, group: str | None=None) -> None:
        raise NotImplementedError

    def add_particle(
        self, surface: pygame.Surface, rect: RectLike, velocity: Point, duration: float
    ) -> int:
        raise NotImplementedError

    def message(self, message: str, group: str = "player") -> None:
        raise NotImplementedError

    def add_effect(self, effect: GlobalEffect) -> None:
        raise NotImplementedError

    def clear_effects(self) -> None:
        raise NotImplementedError

    def spawn(
        self,
        sprite_name: str,
        rect: RectLike,
        z: int | None = None,
        **custom_fields: Any,
    ) -> Sprite | None:
        raise NotImplementedError

    def add_sprite(self, sprite: Sprite) -> None:
        raise NotImplementedError

    def finish_dialog(self, answer: str) -> None:
        raise NotImplementedError

    async def run_dialog(self, *terms: str, face: str | None = None) -> None | str:
        raise NotImplementedError

    async def fade(self, effect_type: str, *args: float) -> GlobalEffect:
        """ "
        Args:
        "fadein_circle", x, y
        "fadeout_cirlce", x, y
        "fadeout_paint", r, g, b
        "fadein_paint", r, g, b
        "paint", r, g, b[, duration]
        """
        raise NotImplementedError

    def get_x(self, group: str = "player") -> float:
        raise NotImplementedError

    def get_y(self, group: str = "player") -> float:
        raise NotImplementedError

    def get_z(self, group: str = "player") -> float:
        raise NotImplementedError

    def get_facing(self, group: str = "player") -> Direction:
        raise NotImplementedError

    def get_group(self, group_name: str) -> set[Sprite]:
        raise NotImplementedError

    def get_rects(self, rect_name: str) -> list[MiscRect]:
        raise NotImplementedError

    def show(self, group: str = "player") -> None:
        raise NotImplementedError

    def hide(self, group: str = "player") -> None:
        raise NotImplementedError

    @classmethod
    def load(
        cls,
        game: Game,
        name: str,
        direction: Direction | None = None,
        position: Point | None = None,
        entrance: MapEntranceType = MapEntranceType.NORMAL,
    ) -> "Level":
        raise NotImplementedError

    def world_to_screen(self, pos: Point) -> Vector2:
        raise NotImplementedError

    def screen_to_world(self, pos: Point) -> Vector2:
        raise NotImplementedError

    def get_game(self) -> Game:
        raise NotImplementedError

    def get_player(self) -> Player:
        raise NotImplementedError

    def set_player(self, player: Player) -> None:
        raise NotImplementedError

    @property
    def map_rect(self) -> pygame.Rect:
        raise NotImplementedError

    @property
    def map_type(self) -> MapType:
        raise NotImplementedError

    @property
    def name(self) -> FileID:
        raise NotImplementedError

    def time_phase(self, mult: float) -> None:
        raise NotImplementedError


@runtime_checkable
class PlatformerLevel(Level, Protocol):
    def get_player(self) -> PlatformerPlayer:
        raise NotImplementedError


@runtime_checkable
class HoverboardLevel(Level, Protocol):
    def get_player(self) -> HoverboardPlayer:
        raise NotImplementedError

    @property
    def speed(self) -> float:
        raise NotImplementedError

    @speed.setter
    def speed(self, value: float) -> None:
        raise NotImplementedError


@runtime_checkable
class SpaceLevel(Level, Protocol):
    RADIUS: int

    @property
    def possible_planet(self) -> FileID | None:
        raise NotImplementedError

    @property
    def planet_locations(self) -> ndarray:
        raise NotImplementedError

    @property
    def camera(self) -> Camera3d:
        raise NotImplementedError
