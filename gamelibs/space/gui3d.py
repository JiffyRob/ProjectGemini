import numpy
import pygame
from pygame.typing import RectLike

from gamelibs import sprite, pixelfont, util_draw, interfaces, hardware
from gamelibs.animation import Animation
from gamelibs.space import math3d

import zengl


class Ship(sprite.GUISprite):
    UP = 1
    DOWN = 2
    LEFT = 4
    RIGHT = 8
    TWIST = 16
    ROTATYNESS = 45

    def __init__(self, level: interfaces.SpaceLevel, rect: RectLike) -> None:
        super().__init__(level, None, rect)
        frames = hardware.loader.get_spritesheet("ship.png", (24, 32))
        self.anim_dict = {
            "normal": Animation(frames[0:3]),
            "turn": Animation(frames[3:6]),
            "up": Animation(frames[6:9]),
            "down": Animation(frames[9:12]),
        }
        self.flipped_anim_dict: dict[str, Animation] = {}
        for key, anim in self.anim_dict.items():
            self.flipped_anim_dict[key] = Animation(anim.frames, anim.speed, True)
        self.surface = pygame.Surface((48, 32), pygame.SRCALPHA).convert_alpha()
        self.direction = 0
        self.anim_left = self.anim_dict["normal"]
        self.anim_right = self.flipped_anim_dict["normal"]

    def up(self) -> None:
        self.direction |= self.UP

    def down(self) -> None:
        self.direction |= self.DOWN

    def left(self) -> None:
        self.direction |= self.LEFT

    def right(self) -> None:
        self.direction |= self.RIGHT

    def twist(self) -> None:
        self.direction |= self.TWIST

    def update(self, dt: float) -> bool:
        for anim in self.anim_dict.values():
            anim.update(dt)
        for anim in self.flipped_anim_dict.values():
            anim.update(dt)
        return True

    def draw(self, surface: pygame.Surface) -> None:
        # figure out which animation to use on each side based on direction of travel
        # lots of ifs, it's a right pain
        left_upness = 0
        right_upness = 0
        turn_left = False
        turn_right = False
        rotation = 0
        if self.direction & self.UP and not self.direction & self.DOWN:
            left_upness += 1
            right_upness += 1
        if self.direction & self.DOWN and not self.direction & self.UP:
            left_upness -= 1
            right_upness -= 1
        if self.direction & self.TWIST:
            left_upness += 1
            right_upness -= 1
        if self.direction & self.LEFT and not self.direction & self.RIGHT:
            turn_left = True
            rotation = self.ROTATYNESS
            right_upness += 1
        if self.direction & self.RIGHT and not self.direction & self.LEFT:
            turn_right = True
            rotation = -self.ROTATYNESS
            left_upness += 1
        if left_upness > 0:
            self.anim_left = self.anim_dict["up"]
        if left_upness == 0:
            self.anim_left = self.anim_dict["normal"]
        if left_upness < 0:
            self.anim_left = self.anim_dict["down"]
        if right_upness > 0:
            self.anim_right = self.flipped_anim_dict["up"]
        if right_upness == 0:
            self.anim_right = self.flipped_anim_dict["normal"]
        if right_upness < 0:
            self.anim_right = self.flipped_anim_dict["down"]
        if turn_left:
            self.anim_left = self.anim_dict["turn"]
        if turn_right:
            self.anim_right = self.flipped_anim_dict["turn"]
        self.surface.fill((0, 0, 0, 0))
        self.surface.blit(self.anim_left.image, (0, 0))
        self.surface.blit(self.anim_right.image, (24, 0))
        blit_surface = pygame.transform.rotate(self.surface, rotation)
        surface.blit(blit_surface, blit_surface.get_rect(center=self.rect.center))
        self.direction = 0


class Compass(sprite.GUISprite):
    def __init__(self, level: interfaces.SpaceLevel, origin: pygame.Vector2) -> None:
        super().__init__(level)
        self.origin = origin
        self.positions = (
            numpy.array(((0, 1, 0), (1, 0, 0), (0, 0, 1)), dtype=numpy.float64) * 10
        )
        self.colors = ("red", "green", "blue")
        self.letters: list[pygame.Surface] = [
            hardware.loader.font.render(i) for i in ("N", "E", "Q")
        ]

    def draw(self, surface: pygame.Surface) -> None:
        positions_copy = self.positions.copy()
        math3d.rotate_points(positions_copy, -self.level.camera.rotation)  # type: ignore
        for offset, color, letter in sorted(
            zip(positions_copy, self.colors, self.letters), key=lambda x: -x[0][2]
        ):
            endpoint = self.origin + offset[:2]
            pygame.draw.line(surface, color, self.origin, endpoint, width=2)
            surface.blit(letter, self.origin + offset[:2] * 1.5 - (3, 4))


class PlanetIndicator(sprite.GUISprite):
    STATE_IDLE = 0
    STATE_PLANET = 1
    STATE_PAUSED = 2
    STATE_ENTER = 3

    def __init__(self, level: interfaces.SpaceLevel, rect: RectLike) -> None:
        super().__init__(level, None, rect)
        self.level = level
        self.log_speed = 30
        self.idle_log_speed = 2
        self.age = 0
        self.font = pixelfont.PixelFont(
            hardware.loader.get_spritesheet("font.png", (7, 8))
        )
        self.state = self.STATE_IDLE
        self.last_state = self.STATE_IDLE

    def confirm_quit(self) -> None:
        self.state = self.STATE_PAUSED

    def enter(self) -> None:
        self.state = self.STATE_ENTER

    def confirm_enter(self) -> None:
        self.state = self.STATE_PLANET

    def fail_confirmation(self) -> None:
        self.state = self.STATE_IDLE

    def reset(self) -> None:
        self.state = self.STATE_IDLE
        self.age = 0
        self.last_state = self.STATE_IDLE

    def update(self, dt: float) -> bool:
        super().update(dt)
        self.age += dt
        if self.state != self.last_state:
            self.age = 0
        self.last_state = self.state
        return True

    def draw(self, surface: pygame.Surface) -> None:
        if self.state == self.STATE_IDLE:
            text = "." * int((self.age * self.idle_log_speed) % 4)
        elif self.state == self.STATE_PLANET:
            text = f"Auto land on planet {self.level.possible_planet}?\nYes: enter"
            text = text[: min(int(self.age * self.log_speed), len(text))]
        elif self.state == self.STATE_PAUSED:
            text = f"Save and quit?\nYes: enter, No: esc"
            text = text[: min(int(self.age * self.log_speed), len(text))]
        elif self.state == self.STATE_ENTER:
            text = f"Autopilot: FUNCTIONAL\nInitiating landing..."
        else:
            raise ValueError(f"Unknown state: {self.state}")
        self.font.render_to(surface, self.rect, text)


class MiniMap(sprite.GUISprite):
    MAP_SIZE = 1500
    BORDER_WIDTH = 1

    def __init__(
        self, level: interfaces.SpaceLevel, rect: RectLike, world_radius: int
    ) -> None:
        super().__init__(level, None, rect)
        self.world_radius = world_radius
        self.ship_surface = hardware.loader.get_surface("map-ship.png")
        self.ship_rect = self.ship_surface.get_rect()
        self.ship_rect.center = self.rect.center

        self.planet_surface = hardware.loader.get_surface("map-planet.png")
        self.planet_rect = self.planet_surface.get_rect()

        self.scale_factor: float

        self.reposition()

    def get_level(self) -> interfaces.SpaceLevel:
        return super().get_level()  # type: ignore

    def reposition(self, rect: RectLike | None = None) -> None:
        if rect is not None:
            self.rect = pygame.FRect(rect)
        self.map_radius = min(self.rect.width, self.rect.height) // 2
        usable_radius = self.map_radius - self.BORDER_WIDTH - 1
        self.scale_factor = self.get_level().RADIUS * usable_radius / self.MAP_SIZE**2
        self.ship_rect.center = self.rect.center

    def update(self, dt: float) -> bool:
        return super().update(dt)

    def draw(self, surface: pygame.Surface) -> None:
        pygame.draw.circle(surface, (27, 37, 78), self.rect.center, self.map_radius)
        pygame.draw.circle(
            surface,
            (119, 126, 134),
            self.rect.center,
            self.map_radius,
            self.BORDER_WIDTH,
        )
        surface.blit(self.ship_surface, self.ship_rect)
        camera_offset = pygame.Vector2(
            self.get_level().camera.pos.x,
            self.get_level().camera.pos.z,
        )
        camera_rotation = pygame.Vector2((self.get_level().camera.rotation * pygame.Vector3(0, 0, 1)).xz).as_polar()[1]  # type: ignore
        upper_bound = (self.map_radius - 1) ** 2
        for planet_location in self.get_level().planet_locations:
            if numpy.isnan(planet_location).max():
                continue
            location = (
                pygame.Vector2(planet_location[0], planet_location[2]) - camera_offset
            ).rotate(-camera_rotation + 90) * self.scale_factor
            location.y *= -1
            if location.length_squared() < upper_bound:
                location += self.rect.center
                surface.set_at(location, (199, 86, 190))


class GUIRendererHW:
    def __init__(
        self, level: interfaces.SpaceLevel, gui: list[interfaces.GUISprite]
    ) -> None:
        self.level = level
        self.gui = gui

        self.surface: pygame.Surface
        self.gl_surface: zengl.Image
        self.pipline = None

        self.recompile_shaders()

    def recompile_shaders(self) -> None:
        self.surface = pygame.Surface(util_draw.RESOLUTION, pygame.SRCALPHA)
        self.gl_surface = (
            self.level.get_game().get_gl_context().image(util_draw.RESOLUTION)
        )

        self.pipeline = (
            self.level.get_game()
            .get_gl_context()
            .pipeline(
                vertex_shader=hardware.loader.get_vertex_shader("scale"),
                fragment_shader=hardware.loader.get_fragment_shader("overlay"),
                framebuffer=[self.level.get_game().gl_window_surface],
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
        )

    def render(self) -> None:
        self.surface.fill((0, 0, 0, 0))
        for element in self.gui:
            element.draw(self.surface)
        self.gl_surface.write(pygame.image.tobytes(self.surface, "RGBA", True))
        self.pipeline.render()
