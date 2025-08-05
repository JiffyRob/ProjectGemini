import numpy
import pygame

from gamelibs import game_state, util_draw, interfaces, hardware
from gamelibs.space import gui3d, math3d, glsprite3d
from math import pi


class Space(game_state.GameState, interfaces.SpaceLevel):
    PLANET_CHECK_TOLERANCE = 100
    LANDING_TOLERANCE = 760
    RADIUS = 2000

    STATE_NORMAL = 0
    STATE_PAUSE = 1
    STATE_ENTRY = 2

    def __init__(self, game: interfaces.Game) -> None:
        super().__init__(game, color="black", opengl=True)
        # self.game.renderer.logical_size = (1920, 1080)
        # in world space y is vertical, and x and z are horizontal
        # in game terms, y is Quarth-Mist, x is East-West, and z is North-South
        # on screen with no rotation x is left-right, y is up-down, and z is depth
        self._camera = interfaces.Camera3d(
            pygame.Vector3(),
            math3d.Quaternion(),
            pygame.Vector2(util_draw.RESOLUTION) / 2,
            pygame.Vector2(60, 60),  # TODO : FOV
            5,
            2000,
        )
        ship_rect = pygame.Rect(0, 0, 48, 32)
        ship_rect.center = util_draw.SCREEN_RECT.center
        self.ship = gui3d.Ship(self, ship_rect)

        compass_pos = pygame.Vector2(-20, -20) + util_draw.SCREEN_RECT.bottomright
        self.compass = gui3d.Compass(self, compass_pos)

        map_rect = pygame.Rect(16, 0, 32, 32)
        map_rect.bottom = util_draw.SCREEN_RECT.bottom
        self.minimap = gui3d.MiniMap(self, map_rect, self.RADIUS)

        pi_rect = pygame.Rect(50, 0, 200, 16)
        pi_rect.bottom = util_draw.SCREEN_RECT.bottom - 20
        self.planet_indicator = gui3d.PlanetIndicator(self, pi_rect)
        self.gui: list[interfaces.GUISprite] = [
            self.ship,
            self.planet_indicator,
            self.minimap,
        ]
        self.sprites = []
        self.ship_overlay = hardware.loader.get_surface_scaled_to(
            "ship-inside.png", util_draw.RESOLUTION
        )

        self.space_renderer = glsprite3d.SpaceRendererHW(self, self.RADIUS)
        self.gui_renderer = gui3d.GUIRendererHW(self, self.gui)

        self.turn_speeds = {
            "up": 0.0,
            "down": 0.0,
            "left": 0.0,
            "right": 0.0,
        }
        self.turn_delta = 0.007
        self.max_turn_speed = 0.6
        self.forward_delta = 10
        self.min_forward_speed = 10
        self.max_forward_speed = 100
        self.forward_speed = self.min_forward_speed
        self.age = 0
        self._possible_planet = None
        self.possible_planet_index = None
        self.dest_rotation = None
        self.state = self.STATE_NORMAL
        self.rear_view = False

    @property
    def camera(self) -> interfaces.Camera3d:
        return self._camera

    @property
    def possible_planet(self) -> str | None:
        return self._possible_planet

    @property
    def planet_locations(self):
        return self.space_renderer.planet_locations

    @property
    def planet_ids(self):
        return self.space_renderer.planet_ids

    @property
    def planet_radii(self):
        return self.space_renderer.planet_radii

    @property
    def planet_names(self) -> dict[int, str]:
        return self.space_renderer.planet_names  # type: ignore

    def update(self, dt: float) -> bool:
        self.age += dt
        self.rear_view = False
        pressed = hardware.input_queue.just_pressed
        held = hardware.input_queue.held
        if "quit" in pressed:
            if self.state == self.STATE_PAUSE:
                self.state = self.STATE_NORMAL
                self.planet_indicator.reset()
            elif self.state == self.STATE_NORMAL:
                self.planet_indicator.confirm_quit()
                self.state = self.STATE_PAUSE
        if "enter" in pressed:
            if self.state == self.STATE_PAUSE:
                self.game.save_to_disk()
                self.game.quit()
            elif self.state == self.STATE_NORMAL and self.possible_planet is not None:
                self.state = self.STATE_ENTRY
                self.planet_indicator.enter()

        if "rear_view" in held:
            self.rear_view = True

        if self.state == self.STATE_NORMAL:
            if "left" in held:
                self.turn_speeds["left"] += self.turn_delta
                self.ship.left()
            else:
                self.turn_speeds["left"] -= self.turn_delta
            if "right" in held:
                self.turn_speeds["right"] += self.turn_delta
                self.ship.right()
            else:
                self.turn_speeds["right"] -= self.turn_delta
            if "turbo_ship" in held:
                self.forward_speed += self.forward_delta
                self.game.play_soundtrack("Lightspeed")
            else:
                self.forward_speed -= self.forward_delta
                self.game.play_soundtrack("SpaceshipMain")

            self.turn_speeds["up"] = pygame.math.clamp(
                self.turn_speeds["up"], 0, self.max_turn_speed
            )
            self.turn_speeds["down"] = pygame.math.clamp(
                self.turn_speeds["down"], 0, self.max_turn_speed
            )
            self.turn_speeds["left"] = pygame.math.clamp(
                self.turn_speeds["left"], 0, self.max_turn_speed
            )
            self.turn_speeds["right"] = pygame.math.clamp(
                self.turn_speeds["right"], 0, self.max_turn_speed
            )
            self.camera.rotation *= math3d.Quaternion(  # type: ignore
                dt * self.turn_speeds["up"], (1, 0, 0)
            )
            self.camera.rotation *= math3d.Quaternion(  # type: ignore
                -dt * self.turn_speeds["down"], (1, 0, 0)
            )
            self.camera.rotation *= math3d.Quaternion(  # type: ignore
                -dt * self.turn_speeds["left"], (0, 1, 0)
            )
            self.camera.rotation *= math3d.Quaternion(  # type: ignore
                dt * self.turn_speeds["right"], (0, 1, 0)
            )
            self.forward_speed = pygame.math.clamp(
                self.forward_speed, self.min_forward_speed, self.max_forward_speed
            )

        elif self.state == self.STATE_ENTRY:
            motion = pygame.Vector3(
                *self.planet_locations[self.possible_planet_index] - self.camera.pos
            )
            if motion.length_squared() <= self.LANDING_TOLERANCE:
                assert (
                    self.possible_planet is not None
                ), "Possible planet should not be None during entry."
                self.game.load_map(self.possible_planet)
                self.camera.rotation *= math3d.Quaternion(pi)  # type: ignore
                self.state = self.STATE_NORMAL
                self.planet_indicator.reset()
            self.camera.pos += motion.clamp_magnitude(self.min_forward_speed) * dt

        if self.state == self.STATE_NORMAL:
            planet_check_position = self.camera.pos
            moved = self.planet_locations.copy()
            math3d.inverse_camera_transform_points_sizes(  # type: ignore
                moved, numpy.zeros((len(self.planet_locations), 2)), self.camera
            )
            moved = moved[:, 2]
            valid = moved > self.camera.near_z
            distances = numpy.linalg.norm(
                self.planet_locations - planet_check_position, axis=1
            )
            self._possible_planet = None
            self.possible_planet_index = None
            if valid.any():
                masked = numpy.ma.masked_array(moved, mask=~valid)
                nearest = numpy.argmin(masked)

                if distances[nearest] < self.PLANET_CHECK_TOLERANCE:
                    self._possible_planet = self.planet_names[int(nearest)]
                    self.possible_planet_index = nearest
                    self.planet_indicator.confirm_enter()

            if self.possible_planet is None:
                self.planet_indicator.fail_confirmation()

        if self.state == self.STATE_NORMAL:
            motion = pygame.Vector3(0, 0, self.forward_speed * dt)
            self.camera.pos += self.camera.rotation * motion  # type: ignore

        camera = self.camera.copy()
        # TODO: Is there a way to combine these?
        if self.rear_view:
            camera.rotation *= math3d.Quaternion(pi, (1, 0, 0))  # type: ignore
            camera.rotation *= math3d.Quaternion(pi, (0, 0, 1))  # type: ignore
        self.space_renderer.update(dt, camera)

        for sprite in self.gui:
            sprite.update(dt)

        return True

    def draw(self):
        self.space_renderer.render()
        if not self.rear_view:
            self.gui_renderer.render()
