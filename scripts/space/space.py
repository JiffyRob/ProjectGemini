import struct

import numpy
import pygame
import zengl

from scripts import game_state, util_draw
from scripts.animation import AnimatedSurface
from scripts.space import gui3d, math3d, sprite3d


class Space(game_state.GameState):
    CIRCLE_RESOLUTION = 16
    STAR_COUNT = 200000
    PLANET_COUNT = 2

    PLANET_STAR = 0
    PLANET_TERRA1 = 1
    PLANET_TERRA2 = 2
    PLANET_KEERGAN = 3

    IDS_TO_NAMES = {
        PLANET_STAR: "Star",
        PLANET_TERRA1: "Terra1",
        PLANET_TERRA2: "Gemini2",
        PLANET_KEERGAN: "Keergan",
    }

    PLANET_CHECK_TOLERANCE = 100

    def __init__(self, game):
        super().__init__(game, color="black", opengl=True)
        # self.game.renderer.logical_size = (1920, 1080)
        # in world space y is vertical, and x and z are horizontal
        # in game terms, y is Quarth-Mist, x is East-West, and z is North-South
        # on screen with no rotation x is left-right, y is up-down, and z is depth
        self.camera = math3d.Camera(
            pygame.Vector3(),
            math3d.Quaternion(),
            pygame.Vector2(util_draw.RESOLUTION) / 2,
            pygame.Vector2(60, 60),  # TODO : FOV
            5,
            5000,
        )
        ship_rect = pygame.Rect(0, 0, 48, 32)
        ship_rect.center = self.game.screen_rect.center
        self.ship = gui3d.Ship(self, ship_rect)
        compass_pos = pygame.Vector2(16, -16) + self.game.screen_rect.bottomleft
        self.compass = gui3d.Compass(self, compass_pos)
        self.planet_indicator = gui3d.PlanetIndicator(self, pygame.Rect(compass_pos + (32, -8), (200, 16)))
        self.gui = [self.ship, self.compass, self.planet_indicator]
        self.sprites = []
        self.ship_overlay = self.game.loader.get_surface_scaled_to("ship-inside.png", util_draw.RESOLUTION)
        self.gui_surface = pygame.Surface((util_draw.RESOLUTION), pygame.SRCALPHA)
        self.gui_gl_surface = self.game.context.image(util_draw.RESOLUTION)

        rng = numpy.random.default_rng(1)  # TODO: random seeding?
        self.star_locations = rng.uniform(low=-2000, high=2000, size=(self.STAR_COUNT, 3)).astype("f4")
        self.star_radii = numpy.zeros(self.STAR_COUNT, "f4") + 1.0

        self.planet_locations = numpy.zeros((self.PLANET_COUNT, 3), "f4")
        self.planet_ids = numpy.zeros(self.PLANET_COUNT, "i4")
        self.planet_radii = numpy.zeros(self.PLANET_COUNT, "f4") + 5.0

        planets = (
            (self.PLANET_TERRA1, (0, 0, -150)),
            (self.PLANET_KEERGAN, (0, 0, 150)),
        )
        self.planet_names = {}
        for (i, (planet, location)), _ in zip(enumerate(planets), range(self.PLANET_COUNT)):
            self.planet_locations[i] = location
            self.planet_ids[i] = planet
            self.planet_names[i] = self.IDS_TO_NAMES[planet]

        angle = numpy.linspace(0.0, numpy.pi * 2.0, self.CIRCLE_RESOLUTION)
        xy = numpy.array([numpy.cos(angle), numpy.sin(angle)])
        vertex_buffer = self.game.context.buffer(xy.T.astype("f4").tobytes())

        self.depth_buffer = self.game.context.image(util_draw.RESOLUTION, "depth24plus")

        self.uniform_buffer = self.game.context.buffer(size=48)

        self.uniform_buffer.view()

        self.star_pipeline = self.game.context.pipeline(
            vertex_shader=self.game.loader.get_vertex_shader("space"),
            fragment_shader=self.game.loader.get_fragment_shader("star"),
            framebuffer=[self.game.gl_window_surface, self.depth_buffer],
            topology="triangle_fan",
            vertex_buffers=[
                *zengl.bind(self.game.context.buffer(self.star_locations), "3f /i", 0),
                *zengl.bind(self.game.context.buffer(self.planet_ids), "1i /i", 1),
                *zengl.bind(vertex_buffer, "2f", 2),
                *zengl.bind(self.game.context.buffer(self.star_radii), "1f /i", 3),
            ],
            layout=[
                {
                    "name": "Common",
                    "binding": 0,
                }
            ],
            resources=[
                {
                    "type": "uniform_buffer",
                    "binding": 0,
                    "buffer": self.uniform_buffer,
                }
            ],
            vertex_count=self.CIRCLE_RESOLUTION,
            instance_count=self.STAR_COUNT,
        )
        self.planet_pipeline = self.game.context.pipeline(
            vertex_shader=self.game.loader.get_vertex_shader("space"),
            fragment_shader=self.game.loader.get_fragment_shader("planet"),
            framebuffer=[self.game.gl_window_surface, self.depth_buffer],
            topology="triangle_fan",
            vertex_buffers=[
                *zengl.bind(self.game.context.buffer(self.planet_locations), "3f /i", 0),
                *zengl.bind(self.game.context.buffer(self.planet_ids), "1i /i", 1),
                *zengl.bind(vertex_buffer, "2f", 2),
                *zengl.bind(self.game.context.buffer(self.planet_radii), "1f /i", 3),
            ],
            layout=[
                {
                    "name": "Common",
                    "binding": 0,
                }
            ],
            resources=[
                {
                    "type": "uniform_buffer",
                    "binding": 0,
                    "buffer": self.uniform_buffer,
                }
            ],
            vertex_count=self.CIRCLE_RESOLUTION,
            instance_count=self.STAR_COUNT,
        )
        self.gui_pipeline = self.game.context.pipeline(
            vertex_shader=self.game.loader.get_vertex_shader("scale"),
            fragment_shader=self.game.loader.get_fragment_shader("overlay"),
            framebuffer=[self.game.gl_window_surface],
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
                    "image": self.gui_gl_surface,
                    "min_filter": "nearest",
                    "mag_filter": "nearest",
                    "wrap_x": "clamp_to_edge",
                    "wrap_y": "clamp_to_edge",
                }
            ],
        )

        self.turn_speeds = {
            "up": 0,
            "down": 0,
            "left": 0,
            "right": 0,
        }
        self.turn_delta = 0.007
        self.max_turn_speed = 0.6
        self.forward_delta = 10
        self.min_forward_speed = 10
        self.max_forward_speed = 100
        self.forward_speed = self.min_forward_speed
        self.age = 0
        self.possible_planet = None
        self.quitting = False

    def update(self, dt):
        self.age += dt
        pressed = self.game.input_queue.just_pressed
        if "quit" in pressed:
            if self.quitting:
                self.quitting = False
                self.planet_indicator.reset()
            else:
                self.planet_indicator.confirm_quit()
                self.quitting = True
        if "enter" in pressed and self.possible_planet:
            if self.quitting:
                self.game.quit()
            else:
                self.game.load_map(self.possible_planet)

        if not self.quitting:
            held = self.game.input_queue.held
            if held["up"]:
                self.turn_speeds["up"] += self.turn_delta
                self.ship.up()
            else:
                self.turn_speeds["up"] -= self.turn_delta
            if held["down"]:
                self.turn_speeds["down"] += self.turn_delta
                self.ship.down()
            else:
                self.turn_speeds["down"] -= self.turn_delta
            if held["left"]:
                self.turn_speeds["left"] += self.turn_delta
                self.ship.left()
            else:
                self.turn_speeds["left"] -= self.turn_delta
            if held["right"]:
                self.turn_speeds["right"] += self.turn_delta
                self.ship.right()
            else:
                self.turn_speeds["right"] -= self.turn_delta
            if held["turbo_ship"]:
                self.forward_speed += self.forward_delta
                self.game.play_soundtrack("Lightspeed")
            else:
                self.forward_speed -= self.forward_delta
                self.game.play_soundtrack("SpaceshipMain")

            self.turn_speeds["up"] = pygame.math.clamp(self.turn_speeds["up"], 0, self.max_turn_speed)
            self.turn_speeds["down"] = pygame.math.clamp(self.turn_speeds["down"], 0, self.max_turn_speed)
            self.turn_speeds["left"] = pygame.math.clamp(self.turn_speeds["left"], 0, self.max_turn_speed)
            self.turn_speeds["right"] = pygame.math.clamp(self.turn_speeds["right"], 0, self.max_turn_speed)
            self.camera.rotation *= math3d.Quaternion(dt * self.turn_speeds["up"], (1, 0, 0))
            self.camera.rotation *= math3d.Quaternion(-dt * self.turn_speeds["down"], (1, 0, 0))
            self.camera.rotation *= math3d.Quaternion(-dt * self.turn_speeds["left"], (0, 1, 0))
            self.camera.rotation *= math3d.Quaternion(dt * self.turn_speeds["right"], (0, 1, 0))
            self.forward_speed = pygame.math.clamp(self.forward_speed, self.min_forward_speed, self.max_forward_speed)
            motion = pygame.Vector3(0, 0, self.forward_speed * dt)

            planet_check_position = self.camera.pos
            moved = self.planet_locations.copy()
            math3d.inverse_camera_transform_points_sizes(moved, numpy.zeros((self.PLANET_COUNT, 2)), self.camera)
            moved = moved[:, 2]
            distances = numpy.linalg.norm(self.planet_locations - planet_check_position, axis=1)[moved > 0]
            self.possible_planet = None
            if distances.size:
                nearest = distances.argmin()
                if distances[nearest] < self.PLANET_CHECK_TOLERANCE:
                    self.possible_planet = self.planet_names[self.planet_ids[nearest]]

            self.camera.pos += self.camera.rotation * motion

            uniforms = numpy.frombuffer(self.uniform_buffer.read(), "f4").copy()
            uniforms[:] = [
                self.camera.pos.x,
                self.camera.pos.y,
                self.camera.pos.z,
                self.camera.rotation.real,
                self.camera.rotation.vector.x,
                self.camera.rotation.vector.y,
                self.camera.rotation.vector.z,
                self.camera.near_z,
                self.camera.far_z,
                self.age,
                0.0,
                0.0,
            ]
            self.uniform_buffer.write(uniforms.tobytes())

        for sprite in self.gui:
            sprite.update(dt)

        return True

    def draw(self):
        self.gui_surface.fill((0, 0, 0, 0))
        for sprite in self.gui:
            sprite.draw(self.gui_surface)
        self.depth_buffer.clear()
        self.gui_gl_surface.write(pygame.image.tobytes(self.gui_surface, "RGBA", True))
        self.star_pipeline.render()
        self.planet_pipeline.render()
        self.gui_pipeline.render()
