import pygame
from pygame.typing import Point
import zengl

from gamelibs import util_draw, env, interfaces, hardware


class WindowNew:
    """DOESN'T WORK!  I get a blank screen and I don't know why :)"""

    def __init__(
        self,
        game: interfaces.Game,
        title: str,
        resolution: Point,
        scalemode: interfaces.ScaleMode = interfaces.ScaleMode.ASPECT,
        vsync: bool = True,
        fullscreen: bool = False,
    ) -> None:
        self.game: interfaces.Game = game
        self.title: str = title
        self.scalemode: interfaces.ScaleMode = scalemode

        self.window: pygame.Window
        self.resolution: Point
        self.vsync: bool
        self.fullscreen: bool
        self.init(resolution=resolution, vsync=vsync, fullscreen=fullscreen)

        self.context = zengl.context()
        self.gl_surface = self.context.image(util_draw.RESOLUTION)
        self.software_surface = pygame.Surface(util_draw.RESOLUTION)

        self.pipeline: zengl.Pipeline
        self.compile_shaders()
        self.reset_viewport()

    def init(self, resolution: Point, vsync: bool, fullscreen: bool) -> None:
        self.window = pygame.window.Window(
            self.title, resolution, resizable=not env.PYGBAG, opengl=True
        )
        self.resolution = resolution
        self.vsync = vsync
        self.fullscreen = fullscreen
        if vsync:
            print("No vsync.  Sorry.")
        if fullscreen:
            self.window.set_fullscreen(True)
        self.window.get_surface()

    def compile_shaders(self) -> None:
        self.pipeline = self.context.pipeline(
            vertex_shader=hardware.loader.get_vertex_shader("scale"),
            fragment_shader=hardware.loader.get_fragment_shader("scale"),
            framebuffer=None,
            viewport=(0, 0, *self.window.size),
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
                    "image": self.gl_surface,
                    "min_filter": "nearest",
                    "mag_filter": "nearest",
                    "wrap_x": "clamp_to_edge",
                    "wrap_y": "clamp_to_edge",
                }
            ],
        )

    def reset_viewport(self) -> None:
        if self.scalemode == interfaces.ScaleMode.STRETCH:
            self.pipeline.viewport = (0, 0, *self.window.size)
        if self.scalemode == interfaces.ScaleMode.ASPECT:
            width_scale = self.window.size[0] / util_draw.RESOLUTION[0]
            height_scale = self.window.size[1] / util_draw.RESOLUTION[1]
            scale = min(width_scale, height_scale)
            rect = pygame.Rect(
                0,
                0,
                round(scale * util_draw.RESOLUTION[0]),
                round(scale * util_draw.RESOLUTION[1]),
            )
            rect.center = self.window.size[0] // 2, self.window.size[1] // 2
            self.pipeline.viewport = tuple(rect)  # type: ignore
        if self.scalemode == interfaces.ScaleMode.INTEGER:
            factor = min(
                self.window.size[0] // util_draw.RESOLUTION[0],
                self.window.size[1] // util_draw.RESOLUTION[1],
            )
            rect = pygame.Rect(
                0,
                0,
                util_draw.RESOLUTION[0] * factor,
                util_draw.RESOLUTION[1] * factor,
            )
            rect.center = self.window.size[0] // 2, self.window.size[1] // 2
            self.pipeline.viewport = tuple(rect)  # type: ignore

    def resize(self, new_size: Point) -> None:
        self.window.size = new_size
        self.reset_viewport()

    def toggle_fullscreen(self) -> None:
        self.init(self.resolution, self.vsync, not self.fullscreen)
        self.reset_viewport()

    def change_scalemode(self, new_method: interfaces.ScaleMode) -> None:
        self.scalemode = new_method
        self.reset_viewport()

    def get_soft_surface(self) -> pygame.Surface:
        return self.software_surface

    def get_gl_surface(self) -> zengl.Image:
        return self.gl_surface

    def get_size(self) -> tuple[int, int]:
        return self.window.size

    def get_rect(self) -> pygame.Rect:
        return pygame.Rect(0, 0, *self.window.size)

    @property
    def mouse_pos(self) -> pygame.Vector2:
        if self.scalemode == interfaces.ScaleMode.INTEGER:
            factor = min(
                self.window.size[0] // util_draw.RESOLUTION[0],
                self.window.size[1] // util_draw.RESOLUTION[1],
            )
            rect = pygame.Rect(
                0, 0, util_draw.RESOLUTION[0] * factor, util_draw.RESOLUTION[1] * factor
            )
            rect.center = self.window.size[0] // 2, self.window.size[1] // 2
            return (pygame.Vector2(pygame.mouse.get_pos()) - rect.topleft) / factor
        elif self.scalemode == interfaces.ScaleMode.STRETCH:
            return pygame.Vector2(pygame.mouse.get_pos()).elementwise() * (
                util_draw.RESOLUTION[0] / self.window.size[0],
                util_draw.RESOLUTION[1] / self.window.size[1],
            )  # type: ignore
        else:  #  self.scalemode == interfaces.ScaleMode.ASPECT
            width_scale = self.window.size[0] / util_draw.RESOLUTION[0]
            height_scale = self.window.size[1] / util_draw.RESOLUTION[1]
            scale = min(width_scale, height_scale)
            rect = pygame.Rect(
                0,
                0,
                round(scale * self.window.size[0]),
                round(scale * self.window.size[1]),
            )
            rect.center = self.window.size[0] // 2, self.window.size[1] // 2
            return (pygame.Vector2(pygame.mouse.get_pos()) - rect.topleft) / scale

    def render(self) -> None:
        self.gl_surface.write(
            pygame.image.tobytes(self.software_surface, "RGBA", flipped=False)
        )
        self.pipeline.render()

    def flip(self) -> None:
        self.window.flip()


class WindowOld:
    def __init__(
        self,
        game: interfaces.Game,
        title: str,
        resolution: Point,
        scalemode: interfaces.ScaleMode = interfaces.ScaleMode.ASPECT,
        vsync: bool = True,
        fullscreen: bool = False,
    ) -> None:
        self.game: interfaces.Game = game
        self.title: str = title
        self.scalemode: interfaces.ScaleMode = scalemode

        self.resolution: Point
        self.vsync: bool
        self.fullscreen: bool
        self.window: pygame.Surface
        self.init(resolution=resolution, vsync=vsync, fullscreen=fullscreen)

        self.context = zengl.context()
        self.gl_surface = self.context.image(util_draw.RESOLUTION)
        self.software_surface = pygame.Surface(util_draw.RESOLUTION)

        self.pipeline: zengl.Pipeline
        self.compile_shaders()
        self.reset_viewport()

    def init(self, resolution: Point, vsync: bool, fullscreen: bool) -> None:
        if fullscreen:
            size = pygame.display.get_desktop_sizes()[0]
            pygame.display.set_mode(
                size, pygame.OPENGL | pygame.FULLSCREEN | pygame.DOUBLEBUF, vsync=vsync
            )
        else:
            pygame.display.set_mode(
                resolution,
                pygame.RESIZABLE * (not env.PYGBAG) | pygame.OPENGL,
                vsync=vsync,
            )
        pygame.display.set_caption(self.title)
        self.resolution = resolution
        self.vsync = vsync
        self.fullscreen = fullscreen

    def compile_shaders(self) -> None:
        self.pipeline = self.context.pipeline(
            vertex_shader=hardware.loader.get_vertex_shader("scale"),
            fragment_shader=hardware.loader.get_fragment_shader("scale"),
            framebuffer=None,
            viewport=(0, 0, *util_draw.RESOLUTION),
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
                    "image": self.gl_surface,
                    "min_filter": "nearest",
                    "mag_filter": "nearest",
                    "wrap_x": "clamp_to_edge",
                    "wrap_y": "clamp_to_edge",
                }
            ],
        )

    def reset_viewport(self) -> None:
        window_size = pygame.display.get_window_size()
        if self.scalemode == interfaces.ScaleMode.STRETCH:
            self.pipeline.viewport = (0, 0, *window_size)

        if self.scalemode == interfaces.ScaleMode.ASPECT:
            width_scale = window_size[0] / util_draw.RESOLUTION[0]
            height_scale = window_size[1] / util_draw.RESOLUTION[1]
            scale = min(width_scale, height_scale)
            rect = pygame.Rect(
                0,
                0,
                round(scale * util_draw.RESOLUTION[0]),
                round(scale * util_draw.RESOLUTION[1]),
            )
            rect.center = window_size[0] // 2, window_size[1] // 2
            self.pipeline.viewport = tuple(rect)  # type: ignore

        if self.scalemode == interfaces.ScaleMode.INTEGER:
            factor = min(
                window_size[0] // util_draw.RESOLUTION[0],
                window_size[1] // util_draw.RESOLUTION[1],
            )
            rect = pygame.Rect(
                0,
                0,
                util_draw.RESOLUTION[0] * factor,
                util_draw.RESOLUTION[1] * factor,
            )
            rect.center = window_size[0] // 2, window_size[1] // 2
            self.pipeline.viewport = tuple(rect)  # type: ignore

    def resize(self, new_size: Point) -> None:
        self.init(new_size, self.vsync, self.fullscreen)
        self.reset_viewport()

    def toggle_fullscreen(self) -> None:
        self.init(self.resolution, self.vsync, not self.fullscreen)
        self.reset_viewport()

    def set_fullscreen(self, fullscreen: bool) -> None:
        self.init(self.resolution, self.vsync, fullscreen)
        self.reset_viewport()

    def set_scalemode(self, new_method: interfaces.ScaleMode) -> None:
        self.scalemode = new_method
        self.reset_viewport()

    def set_vsync(self, vsync: bool) -> None:
        self.init(self.resolution, vsync, self.fullscreen)

    def get_soft_surface(self) -> pygame.Surface:
        return self.software_surface

    def get_gl_surface(self) -> zengl.Image:
        return self.gl_surface

    def get_size(self) -> tuple[int, int]:
        return pygame.display.get_surface().get_size()  # type: ignore

    def get_rect(self) -> pygame.Rect:
        return pygame.Rect(0, 0, *self.window.size)

    @property
    def mouse_pos(self) -> pygame.Vector2:
        if self.scalemode == interfaces.ScaleMode.INTEGER:
            factor: int = min(
                self.window.size[0] // util_draw.RESOLUTION[0],
                self.window.size[1] // util_draw.RESOLUTION[1],
            )
            rect = pygame.Rect(
                0, 0, util_draw.RESOLUTION[0] * factor, util_draw.RESOLUTION[1] * factor
            )
            rect.center = self.window.size[0] // 2, self.window.size[1] // 2
            return (pygame.Vector2(pygame.mouse.get_pos()) - rect.topleft) / factor
        elif self.scalemode == interfaces.ScaleMode.STRETCH:
            return pygame.Vector2(pygame.mouse.get_pos()).elementwise() * (
                util_draw.RESOLUTION[0] / pygame.display.get_size()[0],  # type: ignore
                util_draw.RESOLUTION[1] / pygame.display.get_size()[1],  # type: ignore
            )  # type: ignore
        else:  # self.scalemode == interfaces.ScaleMode.ASPECT:
            width_scale = self.window.size[0] / util_draw.RESOLUTION[0]
            height_scale = self.window.size[1] / util_draw.RESOLUTION[1]
            scale = min(width_scale, height_scale)
            rect = pygame.Rect(
                0,
                0,
                round(scale * self.window.size[0]),
                round(scale * self.window.size[1]),
            )
            rect.center = self.window.size[0] // 2, self.window.size[1] // 2
            return (pygame.Vector2(pygame.mouse.get_pos()) - rect.topleft) / scale

    def render(self, software: bool = True) -> None:
        if software:
            self.gl_surface.write(
                pygame.image.tobytes(self.software_surface, "RGBA", flipped=False)
            )
        self.pipeline.render()

    def flip(self) -> None:
        pygame.display.flip()
        self.gl_surface.clear()
