from enum import Enum, IntFlag, StrEnum, IntEnum, auto
from typing import Callable, Any, Iterable, Protocol
from pygame.typing import RectLike, Point, SequenceLike
from pygame.math import Vector2
from deprecated import deprecated
from dataclasses import dataclass
from copy import copy
from numpy import ndarray

import zengl
import pygame
from SNEK2 import SNEKCallable, AsyncSNEKCallable  # type: ignore

type SnekAPI = dict[str, SNEKCallable | AsyncSNEKCallable]  # TODO: this could be more specific
type FileID = str  # TODO: could this be more specific?
type MiscRect = pygame.Rect | pygame.FRect


class Axis(IntFlag):
    X = auto()
    Y = auto()
    Z = auto()


class MapType(StrEnum):
    TOPDOWN = "TopDown"
    PLATFORMER = "Platformer"
    HOUSE = "House"
    HOVERBOARD = "Hoverboard"


class Direction(StrEnum):
    UP = "up"
    DOWN = "down"
    LEFT = "left"
    RIGHT = "right"

    def to_vector(self) -> Vector2:
        return Vector2(
            {
                self.UP: (0, -1),
                self.DOWN: (0, 1),
                self.LEFT: (-1, 0),
                self.RIGHT: (1, 0),
            }[self]
        )

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


class Quaternion(Protocol):
    def magnitude(self) -> float: ...

    @classmethod
    def from_standard(cls, r: float, i: float, j: float, k: float) -> "Quaternion": ...

    @classmethod
    def from_degrees(
        cls, real: float = 0.0, axis: SequenceLike[float] = (0, 0, 1)
    ) -> "Quaternion": ...

    def __neg__(self) -> "Quaternion": ...

    def copy(self) -> "Quaternion": ...

    def invert(self) -> "Quaternion": ...

    def dot(self, other: "Quaternion") -> float: ...

    def nlerp(self, other: "Quaternion", t: float) -> "Quaternion": ...

    def normalize(self) -> "Quaternion": ...

    def __bool__(self) -> bool: ...

    def __eq__(self, other: object) -> bool: ...

    def __ne__(self, other: object) -> bool: ...

    def __mul__(
        self, other: "Quaternion | pygame.Vector3 | float"
    ) -> "Quaternion | pygame.Vector3": ...

    def __repr__(self) -> str: ...


class GameSave(Protocol):
    def get_state(self, key: str) -> Any: ...

    def set_state(self, key: str, value: Any) -> None: ...

    def get_tmp(self, key: str) -> Any: ...

    def set_tmp(self, key: str, value: Any) -> None: ...

    def load(self, path: FileID) -> None: ...

    def save(self, path: FileID | None = None) -> None: ...

    def delete(self, path: FileID | None = None) -> None: ...

    @property
    def loaded_path(self) -> FileID: ...


class SoundManager(Protocol):
    def play_sound(
        self,
        path: FileID,
        priority: int = 10,
        loops: int = 0,
        volume: float = 1,
        fade_ms: int = 0,
        polar_location: tuple[int, int] = (0, 0),
    ) -> bool: ...

    def set_sound_volume(self, value: float) -> None: ...

    def get_sound_value(self) -> float: ...

    def set_music_volume(self, value: float) -> None: ...

    def get_music_volume(self) -> float: ...

    def switch_track(
        self,
        track: FileID | None = None,
        volume: float = 1,
        loops: int = -1,
        start: float = 0.0,
        fade_ms: int = 0,
    ) -> None: ...

    def stop_track(self) -> None: ...


class InputQueue(Protocol):
    def rumble(self, left: float = 1, right: float = 1, time: int = 500) -> None: ...

    def stop_rumble(self) -> None: ...

    def update(self, events: Iterable[pygame.Event] | None = None) -> None: ...

    def load_bindings(
        self, bindings: dict[str, set[str | None]], delete_old: bool = True
    ) -> None: ...

    @property
    def held(self) -> set[str]: ...

    @property
    def just_pressed(self) -> set[str]: ...


class PixelFont(Protocol):
    def size(self, text: str, width: int = 0) -> tuple[int, int]: ...

    def render_to(self, surface: pygame.Surface, rect: RectLike, text: str) -> None: ...

    def render(self, text: str, width: int = 0) -> pygame.Surface: ...


class Sprite(Protocol):
    groups: set[str]

    def message(self, message: str) -> None: ...

    def hide(self) -> None: ...

    def show(self) -> None: ...

    def lock(self) -> None: ...

    def unlock(self) -> None: ...

    @property
    def pos(self) -> pygame.Vector2: ...

    @property
    def z(self) -> int: ...

    @property
    def rect(self) -> MiscRect: ...

    @rect.setter
    def rect(self, value: MiscRect) -> None: ...

    def update(self, dt: float) -> bool: ...

    def add_effect(self, effect: "SpriteEffect") -> None: ...

    def get_player(self) -> "Player": ...

    def get_level(self) -> "Level": ...

    def get_game(self) -> "Game": ...


class GUISprite(Sprite, Protocol):
    def draw(self, surface: pygame.Surface) -> None: ...


class PlatformerSprite(Sprite, Protocol):
    def get_player(self) -> "PlatformerPlayer": ...

    def get_level(self) -> "PlatformerLevel": ...


class Healthy(Protocol):
    @property
    def health(self) -> int: ...

    @health.setter
    def health(self, value: int) -> None: ...

    @property
    def max_health(self) -> int: ...

    @max_health.setter
    def max_health(self, value: int) -> None: ...

    def hurt(self, amount: int) -> None: ...

    def heal(self, amount: int) -> None: ...


class Interactor(Protocol):
    @property
    def interaction_rect(self) -> MiscRect: ...

    def interact(self) -> InteractionResult: ...


class PuzzleTrigger(Protocol):
    def triggered(self) -> bool: ...

    @property
    def collision_rect(self) -> MiscRect: ...


class Collider(Protocol):
    @property
    def collision_rect(self) -> MiscRect: ...


class Pickup(Protocol):
    @property
    def collision_rect(self) -> MiscRect: ...


class Turner(Protocol):
    @property
    def facing(self) -> Direction: ...


class Player(Sprite, Healthy, Collider, Turner, Protocol):
    @property
    def emeralds(self) -> int: ...

    @emeralds.setter
    def emeralds(self, value: int) -> None: ...

    def pay(self, emeralds: int) -> None: ...

    def charge(self, emeralds: int) -> None: ...

    @property
    def head_rect(self) -> MiscRect: ...

    def get_inventory(self, name: str) -> int: ...

    def acquire(self, thing: str, count: int) -> bool: ...


class HoverboardPlayer(Player, Protocol):
    def exit(self) -> None: ...


class PlatformerPlayer(Player, Protocol):
    def jump(self, cause: JumpCause, just: bool = False) -> None: ...


class GlobalEffect(Protocol): ...


class SpriteEffect(Protocol):
    def update(self, dt: float) -> bool: ...

    def draw(self, surface: pygame.Surface) -> None: ...


class Animation(Protocol):
    def update(self, dt: float) -> None: ...

    def restart(self) -> None: ...

    def done(self) -> bool: ...

    @property
    def image(self) -> pygame.Surface: ...

    @property
    def flip_x(self) -> bool: ...

    @flip_x.setter
    def flip_x(self, value: bool) -> None: ...

    @property
    def flip_y(self) -> bool: ...

    @flip_y.setter
    def flip_y(self, value: bool) -> None: ...


class _Timer(Protocol):
    def time_left(self) -> float: ...

    def percent_complete(self) -> float: ...

    def done(self) -> bool: ...

    def reset(self) -> None: ...

    def finish(self) -> None: ...


class Timer(_Timer):
    def update(self) -> None: ...


class DTimer(_Timer):
    def update(self, dt: float) -> None: ...


class Loader(Protocol):
    def postwindow_init(self) -> None: ...

    @property
    def font(self) -> PixelFont: ...

    def join(self, path: FileID, for_map: bool = False) -> str: ...

    def get_text(self, path: FileID, for_map: bool = False) -> str: ...

    def get_json(self, path: FileID, for_map: bool = False) -> dict[str, Any]: ...

    def save_json(self, path: FileID, data: dict[str, Any]) -> None: ...

    def get_settings(self) -> GameSettings: ...

    def save_settings(self) -> None: ...

    def get_csv(
        self,
        path: FileID,
        item_delimiter: str = ",",
        line_delimiter: str = "\n",
        for_map: bool = False,
    ) -> list[str]: ...

    @staticmethod
    def convert(surface: pygame.Surface) -> pygame.Surface: ...

    @classmethod
    def create_surface(cls, size: Point) -> pygame.Surface: ...

    def get_surface(
        self, path: FileID, rect: RectLike | None = None
    ) -> pygame.Surface: ...

    @deprecated("Manually scale instead")
    def get_surface_scaled_by(
        self, path: FileID, factor: Point = (2, 2)
    ) -> pygame.Surface: ...

    @deprecated("Manually scale instead")
    def get_surface_scaled_to(
        self, path: FileID, size: Point = (16, 16)
    ) -> pygame.Surface: ...

    def get_spritesheet(
        self, path: FileID, size: Point = (16, 16)
    ) -> list[pygame.Surface]: ...

    @deprecated("Old file format that we shouldn't use anymore")
    def get_image(
        self, path: FileID, area: str | RectLike | None = None
    ) -> pygame.Surface: ...

    def get_sound(self, path: FileID) -> pygame.mixer.Sound: ...

    def get_script(self, path: FileID) -> str: ...

    def get_cutscene(self, path: FileID) -> str: ...

    def get_vertex_shader(self, path: FileID) -> str: ...

    def get_fragment_shader(self, path: FileID) -> str: ...

    def get_shader_library(self, path: FileID) -> str: ...

    def get_save(self, path: FileID) -> dict[str, Any]: ...

    def save_data(self, path: FileID, data: dict[str, Any]) -> None: ...

    def delete_save(self, path: FileID) -> None: ...

    def get_save_names(self, amount: int = 5) -> list[FileID]: ...

    def flush(self) -> None: ...


class Game(Protocol):
    def pop_state(self) -> None: ...

    def get_level(self) -> "Level": ...

    def get_save(self) -> GameSave: ...

    def get_gl_context(self) -> zengl.Context: ...

    def run_cutscene(self, name: FileID, api: SnekAPI | None = None) -> None: ...

    async def run_sub_cutscene(self, name: FileID, api: SnekAPI) -> None: ...

    async def get_current_planet_name(self) -> str: ...

    @property
    def mouse_pos(self) -> Point: ...

    @property
    def window_surface(self) -> pygame.Surface: ...

    @property
    def gl_window_surface(self) -> zengl.Image: ...

    def set_graphics(self, value: GraphicsSetting) -> None: ...

    def switch_setting(self, name: str, value: Any) -> None: ...

    def load_map(
        self,
        map_name: FileID,
        direction: Direction | None = None,
        position: Point | None = None,
        entrance: MapEntranceType | None = None,
    ) -> None: ...

    def switch_level(
        self,
        level_name: FileID,
        direction: Direction | None = None,
        position: Point | None = None,
        entrance: MapEntranceType = MapEntranceType.NORMAL,
    ) -> None: ...

    def exit_level(self) -> None: ...

    def load_save(self, save_name: FileID) -> None: ...

    def delayed_callback(self, dt: float, callback: Callable[[], Any]) -> None: ...

    def load_input_binding(self, name: FileID) -> None: ...

    def add_input_binding(self, name: FileID) -> None: ...

    def time_phase(self, mult: float) -> None: ...

    def play_soundtrack(self, track_name: FileID) -> None: ...

    async def run(self) -> None: ...

    def save_to_disk(self) -> None: ...

    def quit(self) -> None: ...

    def exit(self) -> None: ...


class GameState(Protocol):
    def pop(self) -> None: ...

    def update(self, dt: float) -> bool: ...

    def draw(self) -> None: ...


class Level(GameState, Protocol):
    def shake(
        self, magnitude: float = 5.0, delta: float = 8, axis: Axis = Axis.X | Axis.Y
    ) -> None: ...

    def run_cutscene(self, cutscene_id: str, api: SnekAPI | None = None) -> None: ...

    async def attempt_map_cutscene(self) -> None: ...

    def lock(self) -> None: ...

    def unlock(self) -> None: ...

    def message(self, group: str, message: str) -> None: ...

    def add_effect(self, effect: GlobalEffect) -> None: ...

    def clear_effects(self) -> None: ...

    def spawn(
        self,
        sprite_name: str,
        rect: RectLike,
        z: int | None = None,
        **custom_fields: Any,
    ) -> Sprite: ...

    def add_sprite(self, sprite: Sprite) -> None: ...

    def finish_dialog(self, answer: str) -> None: ...

    async def run_dialog(self, *terms: str, face: str | None=None) -> None | str: ...

    async def fade(self, effect_type: str, *args: float) -> GlobalEffect:
        """ "
        Args:
        "fadein_circle", x, y
        "fadeout_cirlce", x, y
        "fadeout_paint", r, g, b
        "fadein_paint", r, g, b
        "paint", r, g, b[, duration]
        """
        ...

    def get_x(self, group: str = "player") -> float: ...

    def get_y(self, group: str = "player") -> float: ...

    def get_z(self, group: str = "player") -> float: ...

    def get_facing(self, group: str = "player") -> float: ...

    def get_group(self, group_name: str) -> set[Sprite]: ...

    def get_rects(self, rect_name: str) -> list[MiscRect]: ...

    def show(self, group: str = "player") -> None: ...

    def hide(self, group: str = "player") -> None: ...

    @classmethod
    def load(
        cls,
        game: Game,
        name: str,
        direction: Direction | None = None,
        position: Point | None = None,
        entrance: MapEntranceType = MapEntranceType.NORMAL,
    ) -> "Level": ...

    def world_to_screen(self, pos: Point) -> Vector2: ...

    def screen_to_world(self, pos: Point) -> Vector2: ...

    def get_game(self) -> Game: ...

    def get_player(self) -> Player: ...

    def set_player(self, player: Player) -> None: ...

    @property
    def map_rect(self) -> pygame.Rect: ...

    @property
    def map_type(self) -> MapType: ...

    @property
    def name(self) -> FileID: ...

    def time_phase(self, mult: float) -> None: ...


class PlatformerLevel(Level, Protocol):
    def get_player(self) -> PlatformerPlayer: ...


class HoverboardLevel(Level, Protocol):
    def get_player(self) -> HoverboardPlayer: ...

    @property
    def speed(self) -> float: ...

    @speed.setter
    def speed(self, value: float) -> None: ...


class SpaceLevel(Level, Protocol):
    RADIUS: int

    @property
    def possible_planet(self) -> FileID | None: ...

    @property
    def planet_locations(self) -> ndarray: ...

    @property
    def camera(self) -> Camera3d: ...
