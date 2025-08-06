# /// script
# requires-python = ">=3.12"
# dependencies = [
#   "pygame-ce",
#   "zengl",
#   "numpy",
# ]

import asyncio
from collections import deque
from typing import Any, Callable

import pygame
from pygame.typing import Point
import zengl
import SNEK2  # type: ignore

from gamelibs import (
    level,
    menu,
    space,
    env,
    window,
    scripting,
    interfaces,
    hardware,
)

pygame.init()
pygame.joystick.init()


class Game(interfaces.Game):
    def __init__(
        self,
        title: str = "Project Gemini",
        fps: interfaces.FrameCap = interfaces.FrameCap.HIGH,
    ) -> None:
        self.title = title
        self.window: window.WindowOld
        self.clock = pygame.time.Clock()
        self.fps = fps
        self.stack: deque[interfaces.GameState] = deque()
        self.dt_mult = 1
        self.running = False
        self.timers: list[tuple[float, Callable[[], Any]]] = []
        self.context: zengl.Context
        self.just_ran_cutscene = False
        self.running_cutscenes: dict[str, asyncio.Task[Any]] = {}

    def pop_state(self) -> None:
        self.stack.popleft()

    def push_state(self, state: interfaces.GameState) -> None:
        self.stack.appendleft(state)

    def get_state(self) -> interfaces.GameState:
        return self.stack[0]

    def exit_level(self) -> None:
        if isinstance(self.get_state(), interfaces.Level):
            self.pop_state()

    def get_gl_context(self) -> zengl.Context:
        return self.context
    
    def get_current_planet_name(self) -> str:
        return self.stack[0].name  # type: ignore

    def run_cutscene(
        self, name: interfaces.FileID, api: interfaces.SnekAPI = None
    ) -> None:
        if (
            name not in self.running_cutscenes
        ):  #  can't run multiple instances of the same cutscene
            self.just_ran_cutscene = True
            task = asyncio.create_task(
                scripting.Script(
                    self, hardware.loader.get_cutscene(name), api=api
                ).run_async()
            )
            self.running_cutscenes[name] = task

    async def run_sub_cutscene(
        self, name: interfaces.FileID, api: interfaces.SnekAPI = None
    ) -> None:
        return await scripting.Script(
            self, hardware.loader.get_cutscene(name), api=api
        ).run_async()

    @property
    def mouse_pos(self) -> pygame.Vector2:
        return self.window.mouse_pos

    @property
    def window_surface(self) -> pygame.Surface:
        return self.window.get_soft_surface()

    @property
    def gl_window_surface(self) -> zengl.Image:
        return self.window.get_gl_surface()

    def set_graphics(self, value: interfaces.GraphicsSetting) -> None:
        print("setting graphics to", value)

    def switch_setting(self, name: str, value: Any) -> None:
        if name == "vsync":
            self.window.set_vsync(value)
        if name == "scale":
            self.window.set_scalemode(value)
        if name == "fullscreen":
            self.window.set_fullscreen(value)
        if name == "frame-cap":
            pass
        if name == "graphics":
            self.set_graphics(value)
        assert hasattr(
            hardware.settings, name
        ), f'Setting should be an attribute of GameSettings interface, not "{name}".'
        setattr(hardware.settings, name, value)

    def load_map(
        self,
        map_name: interfaces.FileID,
        direction: interfaces.Direction | None = None,
        position: Point | None = None,
        entrance: interfaces.MapEntranceType = interfaces.MapEntranceType.NORMAL,
    ) -> None:
        print("loading level:", map_name)
        new_map = level.Level.load(self, map_name, direction, position, entrance)
        if (
            isinstance(self.stack[0], level.Level)
            and new_map.map_type != interfaces.MapType.HOUSE
        ):
            self.pop_state()
        self.stack.appendleft(new_map)
        if "_" not in map_name:
            hardware.save.set_state("planet", map_name)

    def load_save(self, save_name: interfaces.FileID) -> None:
        print("opening save:", save_name)
        self.stack.clear()
        hardware.save.load(save_name)
        self.stack.appendleft(space.Space(self))
        self.stack.appendleft(level.Level.load(self, hardware.save.get_state("planet")))

    def delayed_callback(self, dt: float, callback: Callable[[], Any]) -> None:
        self.timers.append((dt, callback))

    def load_input_binding(self, name: interfaces.FileID) -> None:
        hardware.input_queue.load_bindings(
            hardware.loader.get_json(f"keybindings/{name}"), delete_old=True
        )

    def add_input_binding(self, name: interfaces.FileID) -> None:
        hardware.input_queue.load_bindings(
            hardware.loader.get_json(f"keybindings/{name}"), delete_old=False
        )

    def play_soundtrack(self, track_name: interfaces.FileID | None = None) -> None:
        if len(self.stack):
            current_state = self.stack[0]
            if track_name is None and type(
                getattr(current_state, "soundtrack", None)
            ) == type(""):
                track_name = current_state.soundtrack  # type: ignore
            hardware.sound_manager.stop_track()
            hardware.sound_manager.stop_track()
        else:
            hardware.sound_manager.switch_track(f"music/{track_name}.ogg")

    def switch_level(
        self,
        level_name: interfaces.FileID,
        direction: interfaces.Direction | None = None,
        position: Point | None = None,
        entrance: interfaces.MapEntranceType = interfaces.MapEntranceType.NORMAL,
    ) -> None:
        self.run_cutscene(
            "level_switch",
            api={
                "NEXT_LEVEL": level_name,
                "DIRECTION": direction,
                "POSITION": position,
                "ENTRANCE": entrance,
            },
        )

    def update(self, dt: float) -> float:
        kill_state = False
        if not self.stack[0].update(dt * self.dt_mult):
            kill_state = True
        # if fps drops below 10 the game will start to lag
        dt = pygame.math.clamp(
            self.clock.tick(hardware.settings.framecap * (not env.PYGBAG))
            * self.dt_mult
            / 1000,
            -0.1,
            0.1,
        )
        # update delayed callbacks
        still_waiting: list[tuple[float, Callable[[], Any]]] = []
        for index in range(len(self.timers)):
            self.timers[index] = (self.timers[index][0] - dt, self.timers[index][1])
            if self.timers[index][0] <= 0:
                self.timers[index][1]()
            else:
                still_waiting.append(self.timers[index])
        self.timers = still_waiting
        if kill_state:
            self.stack.popleft()
        self.dt_mult = 1
        return dt

    def draw(self) -> None:
        self.context.new_frame()
        self.window.get_soft_surface().fill(self.stack[0].bgcolor)
        self.stack[0].draw()
        self.window.render(not self.stack[0].opengl)
        self.context.end_frame()
        self.window.flip()

    async def run(self) -> None:
        self.running = True
        hardware.settings.update(hardware.loader.get_settings())

        self.window = window.WindowOld(
            self,
            "Project Gemini",
            (0, 0),  # makes it maximized by default
            hardware.settings.scale,
            hardware.settings.vsync,
            hardware.settings.fullscreen,
        )
        self.context = zengl.context()

        self.load_input_binding("arrow")
        self.add_input_binding("controller")

        self.stack.appendleft(menu.MainMenu(self))
        # self.stack.appendleft(space.Space(self))
        pygame.key.set_repeat(0, 0)
        dt = 0
        while self.running and len(self.stack):
            # make sure that a cutscene has a chance to update before the next draw call
            if self.just_ran_cutscene:
                await asyncio.sleep(0)
                self.just_ran_cutscene = False
            # keep the list of running cutscenes up to date
            self.running_cutscenes = {
                key: value
                for key, value in self.running_cutscenes.items()
                if not value.done()
            }
            events = tuple(pygame.event.get())
            hardware.input_queue.update(events)
            for event in events:
                if event.type == pygame.VIDEORESIZE:
                    self.window.resize(event.size)
            self.draw()
            dt = self.update(dt)
            await asyncio.sleep(0)
        pygame.quit()

    def save_to_disk(self) -> None:
        hardware.save.save()

    def quit(self) -> None:
        hardware.loader.save_settings(hardware.settings)
        hardware.loader.flush()
        while len(self.stack) > 1:
            self.stack.clear()
        self.stack.appendleft(menu.MainMenu(self))

    def exit(self) -> None:
        self.running = env.PYGBAG


asyncio.run(Game().run())
