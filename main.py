import asyncio
from collections import deque

import pygame
import zengl

from scripts import (
    game_save,
    input_binding,
    level,
    loader,
    menu,
    sound,
    space,
    util_draw,
)

pygame.init()
pygame.joystick.init()


class Game:
    def __init__(self, title="Project Gemini", fps=60):
        self.title = title
        self.window = None
        self.clock = pygame.time.Clock()
        self.screen_rect = pygame.Rect((0, 0), util_draw.RESOLUTION)
        self.fps = fps
        self.stack = deque()
        self.dt_mult = 1
        self.running = False
        self.loader = None
        self.display_surface = None
        self.sound_manager = None
        self.save = game_save.GameSave(self)
        self.input_queue = input_binding.InputQueue()
        self.timers = []
        self.context = None
        self.window_surface_gl = None
        self.pipeline = None

    @property
    def window_surface(self):
        return self.display_surface

    @property
    def gl_window_surface(self):
        return self.window_surface_gl

    @property
    def mouse_pos(self):
        window_size = self.window.get_size() # self.window.get_surface()
        window_rect = self.window.get_rect()
        if self.settings["scale"] == util_draw.SCALEMODE_INTEGER:
            factor = min(
                window_size[0] // util_draw.RESOLUTION[0],
                window_size[1] // util_draw.RESOLUTION[1],
            )
            rect = pygame.Rect(
                0, 0, util_draw.RESOLUTION[0] * factor, util_draw.RESOLUTION[1] * factor
            )
            rect.center = window_rect.center
            return (pygame.Vector2(pygame.mouse.get_pos()) - rect.topleft) / factor
        if self.settings["scale"] == util_draw.SCALEMODE_STRETCH:
            return pygame.Vector2(pygame.mouse.get_pos()).elementwise() * (
                util_draw.RESOLUTION[0] / window_size[0],
                util_draw.RESOLUTION[1] / window_size[1],
            )
        if self.settings["scale"] == util_draw.SCALEMODE_ASPECT:
            width_scale = window_size[0] / util_draw.RESOLUTION[0]
            height_scale = window_size[1] / util_draw.RESOLUTION[1]
            scale = min(width_scale, height_scale)
            rect = pygame.Rect(
                0,
                0,
                round(scale * window_size[0]),
                round(scale * window_size[1]))
            rect.center = window_rect.center
            return (pygame.Vector2(pygame.mouse.get_pos()) - rect.topleft) / scale

    def toggle_fullscreen(self):
        self.settings["fullscreen"] = not self.settings["fullscreen"]
        if self.settings["fullscreen"]:
            self.settings["last-resolution"] = self.window.get_size()
            self.window = pygame.display.set_mode(util_draw.RESOLUTION_FULLSCREEN, pygame.FULLSCREEN | pygame.OPENGL, vsync=self.settings["vsync"])
        else:
            self.window = pygame.display.set_mode(self.settings["last-resolution"], pygame.RESIZABLE | pygame.OPENGL, vsync=self.settings["vsync"])
        
    def videoresize(self, new_size):
        if self.settings["scale"] == util_draw.SCALEMODE_STRETCH:
            self.pipeline.viewport = (0, 0, *new_size)
        if self.settings["scale"] == util_draw.SCALEMODE_ASPECT:
            width_scale = new_size[0] / util_draw.RESOLUTION[0]
            height_scale = new_size[1] / util_draw.RESOLUTION[1]
            scale = min(width_scale, height_scale)
            rect = pygame.Rect(
                0,
                0,
                round(scale * util_draw.RESOLUTION[0]),
                round(scale * util_draw.RESOLUTION[1]))
            rect.centerx, rect.centery = new_size[0] // 2, new_size[1] // 2
            self.pipeline.viewport = tuple(rect)
        if self.settings["scale"] == util_draw.SCALEMODE_INTEGER:
            factor = min(
                new_size[0] // util_draw.RESOLUTION[0],
                new_size[1] // util_draw.RESOLUTION[1],
            )
            rect = pygame.Rect(
                0,
                0,
                util_draw.RESOLUTION[0] * factor,
                util_draw.RESOLUTION[1] * factor,
            )
            rect.center = window_surface.get_rect().center
            self.pipeline.viewport = tuple(rect)

    def pop_state(self):
        self.stack.popleft()

    def load_map(self, map_name, direction=None, position=None, entrance=None):
        print("loading level:", map_name)
        new_map = level.Level.load(self, map_name, direction, position, entrance)
        if isinstance(self.stack[0], level.Level) and new_map.map_type != new_map.MAP_HOUSE:
            self.pop_state()
        self.stack.appendleft(new_map)
        if "_" not in map_name:
            self.save.planet = map_name

    def load_save(self, save_name):
        print("opening save:", save_name)
        self.stack.clear()
        self.save.load(save_name)
        self.stack.appendleft(space.Space(self))
        self.stack.appendleft(level.Level.load(self, self.save.planet))

    def delayed_callback(self, dt, callback):
        self.timers.append((dt, callback))

    def load_input_binding(self, name):
        self.input_queue.load_bindings(
            self.loader.get_json(f"keybindings/{name}"), delete_old=True
        )

    def add_input_binding(self, name):
        self.input_queue.load_bindings(
            self.loader.get_json(f"keybindings/{name}"), delete_old=False
        )

    def time_phase(self, mult):
        self.dt_mult = mult

    def play_soundtrack(self, track_name):
        if track_name is None:
            self.sound_manager.stop_track()
        else:
            self.sound_manager.switch_track(f"music/{track_name}.wav")

    def update(self, dt):
        kill_state = False
        if not self.stack[0].update(dt * self.dt_mult):
            kill_state = True
        # if fps drops below 10 the game will start to lag
        dt = pygame.math.clamp(
            self.clock.tick(self.fps) * self.dt_mult / 1000, -0.1, 0.1
        )
        # update delayed callbacks
        still_waiting = []
        for index in range(len(self.timers)):
            self.timers[index][0] -= dt
            if self.timers[index][0] <= 0:
                self.timers[index][1]()
            else:
                still_waiting.append(self.timers[index])
        self.timers = still_waiting
        if kill_state:
            self.stack.popleft()
        self.dt_mult = 1
        return dt

    def draw(self):
        self.context.new_frame()

        self.window_surface.fill(self.stack[0].bgcolor)
        self.gl_window_surface.clear()

        window_surface = self.window  # self.window.get_surface()
        self.stack[0].draw()
        if not self.stack[0].opengl:
            self.gl_window_surface.write(pygame.image.tobytes(self.display_surface, "RGBA", flipped=False))
        self.pipeline.render()
        self.context.end_frame()
        if self.settings["scale"] == util_draw.SCALEMODE_INTEGER:
            factor = min(
                window_surface.get_width() // util_draw.RESOLUTION[0],
                window_surface.get_height() // util_draw.RESOLUTION[1],
            )
            rect = pygame.Rect(
                0,
                0,
                util_draw.RESOLUTION[0] * factor,
                util_draw.RESOLUTION[1] * factor,
            )
            rect.center = window_surface.get_rect().center
            window_surface.blit(
                pygame.transform.scale_by(self.display_surface, (factor, factor)),
                rect.topleft,
            )


        pygame.display.flip()
        # self.window.flip()

    async def run(self):
        self.running = True
        self.loader = loader.Loader()
        self.settings = self.loader.get_settings()
        """
        # commented out for lack of vsync
        self.window = pygame.window.Window(
            self.title,
            util_draw.RESOLUTION,
            sdl2.WINDOWPOS_CENTERED,
            resizable=True,
            maximized=True,
        )
        self.window.get_surface()  # allows convert() calls
        """
        if self.settings["last-resolution"] is None:
            info = pygame.display.Info()
            self.settings["last-resolution"] = (info.current_w, info.current_h - 32)
        self.window = pygame.display.set_mode(self.settings["last-resolution"], pygame.RESIZABLE | pygame.OPENGL, vsync=self.settings["vsync"])
        pygame.display.set_caption(self.title)
        if self.settings["fullscreen"]:
            self.toggle_fullscreen()
            self.settings["fullscreen"] = True  # reset bc fullscreen toggle flips it
        self.loader.postwindow_init()
        self.display_surface = pygame.Surface(util_draw.RESOLUTION).convert()

        self.context = zengl.context()
        self.window_surface_gl = self.context.image(util_draw.RESOLUTION)
        self.pipeline = self.context.pipeline(
            vertex_shader=self.loader.get_vertex_shader("scale"),
            fragment_shader=self.loader.get_fragment_shader("scale"),
            framebuffer=None,
            viewport=(0, 0, *self.settings["last-resolution"]),
            topology="triangle_strip",
            vertex_count=4,
            layout=[
                {
                    "name": "input_texture",
                    "binding": 0,
                }
            ],
            resources=[
                {
                    "type": "sampler",
                    "binding": 0,
                    "image": self.gl_window_surface,
                    "min_filter": "nearest",
                    "mag_filter": "nearest",
                    "wrap_x": "clamp_to_edge",
                    "wrap_y": "clamp_to_edge",
                }
            ]
        )

        self.load_input_binding("arrow")
        self.add_input_binding("controller")
        self.sound_manager = sound.SoundManager(self.loader)
        self.stack.appendleft(menu.MainMenu(self))
        dt = 0
        pygame.key.set_repeat(0, 0)
        while self.running and len(self.stack):
            events = tuple(pygame.event.get())
            self.input_queue.update(events)
            for event in events:
                if event.type == pygame.VIDEORESIZE:
                    self.videoresize(event.size)
            if pygame.key.get_just_released()[pygame.K_F11]:
                self.toggle_fullscreen()
            self.draw()
            dt = self.update(dt)
            await asyncio.sleep(0)

        pygame.quit()

    def save_to_disk(self):
        self.save.save()

    def quit(self):
        self.loader.save_settings(self.settings)
        while len(self.stack) > 1:
            self.stack.clear()
            self.stack.appendleft(menu.MainMenu(self))

    def exit(self):
        self.running = False


asyncio.run(Game().run())
