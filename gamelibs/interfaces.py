from abc import ABC, abstractmethod
from enum import Enum, IntFlag, StrEnum, IntEnum, auto
from typing import Callable, Any, override
from pygame.typing import RectLike, Point
from pygame.math import Vector2
import zengl
import pygame

type SnekAPI = dict[str, Callable[..., Any]]  # TODO: this could be more specific
type FileID = str  # TODO: could this be more specific?

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

    def as_vector(self) -> Vector2:
        return Vector2({
            self.UP: (0, -1),
            self.DOWN: (0, 1),
            self.LEFT: (-1, 0),
            self.RIGHT: (1, 0),
        }[self])

    def reverse(self) -> "Direction":
        cls = self.__class__
        return {
            self.UP: cls.DOWN,
            self.DOWN: cls.UP,
            self.LEFT: cls.RIGHT,
            self.RIGHT: cls.LEFT,
        }[self]


class MapEntranceType(Enum):
    NORMAL = auto()
    FALLING = auto()


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


class Sprite(ABC):
    ...

class GlobalEffect(ABC):
    ...


class Animation(ABC):
    @abstractmethod
    def update(self, dt: float) -> None:
        raise NotImplementedError

    @abstractmethod
    def restart(self, dt: float) -> None:
        raise NotImplementedError

    @property
    @abstractmethod
    def image(self) -> pygame.Surface:
        raise NotImplementedError


class _Timer(ABC):
    @abstractmethod
    def time_left(self) -> float:
        raise NotImplementedError

    @abstractmethod
    def percent_complete(self) -> float:
        raise NotImplementedError

    @abstractmethod
    def done(self) -> bool:
        raise NotImplementedError

    @abstractmethod
    def reset(self) -> None:
        raise NotImplementedError

    @abstractmethod
    def finish(self) -> None:
        raise NotImplementedError


class Timer(_Timer):
    @abstractmethod
    def update(self) -> None:
        raise NotImplementedError


class DTimer(_Timer):
    @abstractmethod
    def update(self, dt: float) -> None:
        raise NotImplementedError


class Game(ABC):
    @abstractmethod
    def pop_state(self) -> None:
        raise NotImplementedError

    @abstractmethod
    def get_level(self) -> "Level":
        raise NotImplementedError

    @abstractmethod
    def run_cutscene(self, name: FileID, api: SnekAPI | None = None) -> None:
        raise NotImplementedError

    @abstractmethod
    async def run_sub_cutscene(self, name: FileID, api: SnekAPI) -> None:
        raise NotImplementedError

    @abstractmethod
    async def get_current_planet_name(self) -> str:
        raise NotImplementedError

    @property
    @abstractmethod
    def mouse_pos(self) -> Point:
        raise NotImplementedError

    @property
    @abstractmethod
    def window_surface(self) -> pygame.Surface:
        raise NotImplementedError

    @property
    @abstractmethod
    def gl_window_surface(self) -> zengl.Image:
        raise NotImplementedError

    @abstractmethod
    def set_graphics(self, value: GraphicsSetting) -> None:
        raise NotImplementedError

    @abstractmethod
    def switch_setting(self, name: str, value: Any) -> None:
        raise NotImplementedError

    @abstractmethod
    def load_map(self, map_name: FileID, direction: Direction, position: Point, entrance: MapEntranceType) -> None:
        raise NotImplementedError

    @abstractmethod
    def load_save(self, save_name: FileID) -> None:
        raise NotImplementedError

    @abstractmethod
    def delayed_callback(self, dt: float, callback: Callable[[], Any]) -> None:
        raise NotImplementedError

    @abstractmethod
    def load_input_binding(self, name: FileID) -> None:
        raise NotImplementedError

    @abstractmethod
    def add_input_binding(self, name: FileID) -> None:
        raise NotImplementedError

    @abstractmethod
    def time_phase(self, mult: float) -> None:
        raise NotImplementedError

    @abstractmethod
    def play_soundtrack(self, track_name: FileID) -> None:
        raise NotImplementedError

    @abstractmethod
    async def run(self) -> None:
        raise NotImplementedError

    @abstractmethod
    def save_to_disk(self) -> None:
        raise NotImplementedError

    @abstractmethod
    def quit(self) -> None:
        raise NotImplementedError

    @abstractmethod
    def exit(self) -> None:
        raise NotImplementedError


class GameState(ABC):
    @abstractmethod
    def pop(self) -> None:
        raise NotImplementedError

    @abstractmethod
    def update(self, dt: float) -> None:
        raise NotImplementedError

    @abstractmethod
    def draw(self) -> None:
        raise NotImplementedError


class Level(GameState):
    @abstractmethod
    def shake(self, magnitude: float = 5.0, delta: float = 8, axis: Axis = Axis.X | Axis.Y) -> None:
        raise NotImplementedError

    @abstractmethod
    def run_cutscene(self, cutscene_id: str, api: SnekAPI | None = None) -> None:
        raise NotImplementedError

    @abstractmethod
    async def attempt_map_cutscene(self) -> None:
        raise NotImplementedError

    @abstractmethod
    def exit_level(self) -> None:
        raise NotImplementedError

    @abstractmethod
    def switch_level(self) -> None:
        raise NotImplementedError

    @abstractmethod
    def lock(self) -> None:
        raise NotImplementedError

    @abstractmethod
    def unlock(self) -> None:
        raise NotImplementedError

    @abstractmethod
    def message(self, group: str, message: str) -> None:
        raise NotImplementedError

    @abstractmethod
    def add_effect(self, effect: GlobalEffect) -> None:
        raise NotImplementedError

    @abstractmethod
    def clear_effects(self) -> None:
        raise NotImplementedError

    @abstractmethod
    def spawn(self, sprite_name: str, rect: RectLike, z: float | None = None, **custom_fields: Any) -> None:
        raise NotImplementedError

    @abstractmethod
    def add_sprite(self, sprite: Sprite) -> None:
        raise NotImplementedError

    @abstractmethod
    def finish_dialog(self, answer: str) -> None:
        raise NotImplementedError

    @abstractmethod
    async def run_dialog(self, *terms: str) -> str:
        raise NotImplementedError

    @abstractmethod
    async def fade(self, effect_type: str, *args: float) -> GlobalEffect:
        """"
        Args:
        "fadein_circle", x, y
        "fadeout_cirlce", x, y
        "fadeout_paint", r, g, b
        "fadein_paint", r, g, b
        "paint", r, g, b[, duration]
        """
        raise NotImplementedError()

    @abstractmethod
    def get_x(self, group: str="player") -> float:
        raise NotImplementedError()

    @abstractmethod
    def get_y(self, group: str="player") -> float:
        raise NotImplementedError()

    @abstractmethod
    def get_z(self, group: str="player") -> float:
        raise NotImplementedError()

    @abstractmethod
    def get_facing(self, group: str="player") -> float:
        raise NotImplementedError()

    @abstractmethod
    def get_group(self, group_name: str) -> set[Sprite]:
        raise NotImplementedError()

    @abstractmethod
    def get_rects(self, rect_name: str) -> list[RectLike]:
        raise NotImplementedError()

    @abstractmethod
    def show(self, group: str="player") -> None:
        raise NotImplementedError()

    @abstractmethod
    def hide(self, group: str="player") -> None:
        raise NotImplementedError()

    @classmethod
    @abstractmethod
    def load(cls, game: Game, name: str, direction: Direction | None=None, position: Point | None = None, entrance: MapEntranceType = MapEntranceType.NORMAL) -> "Level":
        raise NotImplementedError()

    @abstractmethod
    def world_to_screen(self, pos: Point) -> Vector2:
        raise NotImplementedError()

    @abstractmethod
    def screen_to_world(self, pos: Point) -> Vector2:
        raise NotImplementedError()