import pygame
import zengl

from gamelibs import util_draw, env


class WindowNew:
    """DOESN'T WORK!  I get a blank screen and I don't know why :)"""

    def __init__(
        self,
        game,
        title,
        resolution,
        scalemode=util_draw.SCALEMODE_ASPECT,
        vsync=True,
        fullscreen=False,
    ):
        self.game = game
        self.title = title
        self.scalemode = scalemode

        self.window = None
        self.resolution = None
        self.vsync = None
        self.fullscreen = None
        self.init(resolution=resolution, vsync=vsync, fullscreen=fullscreen)

        self.context = zengl.context()
        self.gl_surface = self.context.image(util_draw.RESOLUTION)
        self.software_surface = pygame.Surface(util_draw.RESOLUTION)

        self.pipeline = None
        self.compile_shaders()
        self.reset_viewport()

    def init(self, resolution, vsync, fullscreen):
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

    def compile_shaders(self):
        self.pipeline = self.context.pipeline(
            vertex_shader=self.game.loader.get_vertex_shader("scale"),
            fragment_shader=self.game.loader.get_fragment_shader("scale"),
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

    def reset_viewport(self):
        if self.scalemode == util_draw.SCALEMODE_STRETCH:
            self.pipeline.viewport = (0, 0, *self.window.size)
        if self.scalemode == util_draw.SCALEMODE_ASPECT:
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
            self.pipeline.viewport = tuple(rect)
        if self.scalemode == util_draw.SCALEMODE_INTEGER:
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
            self.pipeline.viewport = tuple(rect)

    def resize(self, new_size):
        self.window.size = new_size
        self.reset_viewport()

    def toggle_fullscreen(self):
        self.init(self.resolution, self.vsync, not self.fullscreen)
        self.reset_viewport()

    def change_scalemode(self, new_method):
        self.scalemode = new_method
        self.reset_viewport()

    def get_soft_surface(self):
        return self.software_surface

    def get_gl_surface(self):
        return self.gl_surface

    def get_size(self):
        return self.window.size

    def get_rect(self):
        return pygame.Rect(0, 0, *self.window.size)

    @property
    def mouse_pos(self):
        if self.scalemode == util_draw.SCALEMODE_INTEGER:
            factor = min(
                self.window.size[0] // util_draw.RESOLUTION[0],
                self.window.size[1] // util_draw.RESOLUTION[1],
            )
            rect = pygame.Rect(
                0, 0, util_draw.RESOLUTION[0] * factor, util_draw.RESOLUTION[1] * factor
            )
            rect.center = self.window.size[0] // 2, self.window.size[1] // 2
            return (pygame.Vector2(pygame.mouse.get_pos()) - rect.topleft) / factor
        if self.scalemode == util_draw.SCALEMODE_STRETCH:
            return pygame.Vector2(pygame.mouse.get_pos()).elementwise() * (
                util_draw.RESOLUTION[0] / self.window.size[0],
                util_draw.RESOLUTION[1] / self.window.size[1],
            )
        if self.scalemode == util_draw.SCALEMODE_ASPECT:
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

    def render(self):
        self.gl_surface.write(
            pygame.image.tobytes(self.software_surface, "RGBA", flipped=False)
        )
        self.pipeline.render()

    def flip(self):
        self.window.flip()


class WindowOld:
    def __init__(
        self,
        game,
        title,
        resolution,
        scalemode=util_draw.SCALEMODE_ASPECT,
        vsync=True,
        fullscreen=False,
    ):
        self.game = game
        self.title = title
        self.scalemode = scalemode

        self.resolution = None
        self.vsync = None
        self.fullscreen = None
        self.init(resolution=resolution, vsync=vsync, fullscreen=fullscreen)

        self.context = zengl.context()
        self.gl_surface = self.context.image(util_draw.RESOLUTION)
        self.software_surface = pygame.Surface(util_draw.RESOLUTION)

        self.pipeline = None
        self.compile_shaders()
        self.reset_viewport()

    def init(self, resolution, vsync, fullscreen):
        if fullscreen:
            size = pygame.display.get_desktop_sizes()[0]
            pygame.display.set_mode(
                size, pygame.OPENGL | pygame.FULLSCREEN, vsync=True
            )
        else:
            pygame.display.set_mode(
                resolution,
                pygame.RESIZABLE * (not env.PYGBAG) | pygame.OPENGL,
                vsync=True,
            )
        pygame.display.set_caption(self.title)
        self.resolution = resolution
        self.vsync = vsync
        self.fullscreen = fullscreen

    def compile_shaders(self):
        self.pipeline = self.context.pipeline(
            vertex_shader=self.game.loader.get_vertex_shader("scale"),
            fragment_shader=self.game.loader.get_fragment_shader("scale"),
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

    def reset_viewport(self):
        window_size = pygame.display.get_window_size()
        if self.scalemode == util_draw.SCALEMODE_STRETCH:
            self.pipeline.viewport = (0, 0, *window_size)
        if self.scalemode == util_draw.SCALEMODE_ASPECT:
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
            self.pipeline.viewport = tuple(rect)
        if self.scalemode == util_draw.SCALEMODE_INTEGER:
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
            self.pipeline.viewport = tuple(rect)

    def resize(self, new_size):
        self.init(new_size, self.vsync, self.fullscreen)
        self.reset_viewport()

    def toggle_fullscreen(self):
        self.init(self.resolution, self.vsync, not self.fullscreen)
        self.reset_viewport()

    def set_fullscreen(self, fullscreen):
        self.init(self.resolution, self.vsync, fullscreen)
        self.reset_viewport()

    def set_scalemode(self, new_method):
        self.scalemode = new_method
        self.reset_viewport()

    def set_vsync(self, vsync):
        self.init(self.resolution, vsync, self.fullscreen)

    def get_soft_surface(self):
        return self.software_surface

    def get_gl_surface(self):
        return self.gl_surface

    def get_size(self):
        return pygame.display.get_surface().get_size()

    def get_rect(self):
        return pygame.Rect(0, 0, *self.window.size)

    @property
    def mouse_pos(self):
        if self.scalemode == util_draw.SCALEMODE_INTEGER:
            factor = min(
                self.window.size[0] // util_draw.RESOLUTION[0],
                self.window.size[1] // util_draw.RESOLUTION[1],
            )
            rect = pygame.Rect(
                0, 0, util_draw.RESOLUTION[0] * factor, util_draw.RESOLUTION[1] * factor
            )
            rect.center = self.window.size[0] // 2, self.window.size[1] // 2
            return (pygame.Vector2(pygame.mouse.get_pos()) - rect.topleft) / factor
        if self.scalemode == util_draw.SCALEMODE_STRETCH:
            return pygame.Vector2(pygame.mouse.get_pos()).elementwise() * (
                util_draw.RESOLUTION[0] / pygame.display.get_size()[0],
                util_draw.RESOLUTION[1] / pygame.display.get_size()[1],
            )
        if self.scalemode == util_draw.SCALEMODE_ASPECT:
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

    def render(self, software=True):
        if software:
            self.gl_surface.write(
                pygame.image.tobytes(self.software_surface, "RGBA", flipped=False)
            )
        self.pipeline.render()

    def flip(self):
        pygame.display.flip()
        self.gl_surface.clear()
