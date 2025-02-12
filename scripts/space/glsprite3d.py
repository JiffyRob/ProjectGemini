import pygame
import numpy
import zengl

from scripts import util_draw


class SpaceRendererHW:
    STAR_COUNT = 200_000

    CIRCLE_RESOLUTION = 16

    def __init__(self, level):
        self.level = level
        self.age = 0

        self.planet_pipeline = None
        self.star_pipeline = None
        self.uniform_buffer = None
        self.depth_buffer = None
        self.planet_names = None
        self.planet_radii = None
        self.planet_ids = None
        self.planet_locations = None
        self.star_radii = None
        self.star_ids = None
        self.star_locations = None

        self.compile_shaders()

    def load_planet_data(self):
        planets = self.level.game.loader.get_json("planets")
        print(planets)
        default_values = planets.pop("Default")
        defines = "#line 0 1\n"
        defines += self.level.game.loader.get_shader_library("planet_struct") + "\n"
        defines += "#line 0 1000\n"
        locations = {}
        self.id_to_name = {}
        self.name_to_id = {}
        next_id = 0
        for planet_name, planet_data in planets.items():
            self.id_to_name[next_id] = planet_name
            self.name_to_id[planet_name] = next_id
            defines += f"#define PLANET_{planet_name} {next_id}\n"
            planet_data = {**default_values, **planet_data}
            locations[next_id] = planet_data.pop("loc")
            for param_name, param_value in planet_data.items():
                if isinstance(param_value, list):
                    param_value = f"vec{len(param_value)}({str(param_value).replace('[', '').replace(']', '')})"
                defines += f"#define P_{param_name}_{planet_name} {param_value}\n"
            next_id += 1

        defines += self.level.game.loader.get_shader_library("planets") + "\n"

        print(defines)

        return defines, locations

    def get_planet_id_from_name(self, name):
        return self.name_to_id[name]

    def get_planet_name_from_id(self, id):
        return self.id_to_name[id]

    def compile_shaders(self):

        rng = numpy.random.default_rng(1)  # TODO: random seeding?
        self.star_locations = rng.uniform(
            low=-2000, high=2000, size=(self.STAR_COUNT, 3)
        ).astype("f4")
        self.star_ids = numpy.tile(numpy.array([0, 1]), self.STAR_COUNT // 2 + 1)
        self.star_radii = numpy.zeros(self.STAR_COUNT, "f4") + 1.0

        planet_lib, locations = self.load_planet_data()
        planet_count = len(locations)
        self.planet_locations = numpy.zeros((planet_count, 3), "f4")
        self.planet_ids = numpy.zeros(planet_count, "i4")
        self.planet_radii = numpy.zeros(planet_count, "f4") + 5.0

        self.planet_names = {}
        print(locations, self.id_to_name)
        for i, (planet, location) in enumerate(locations.items()):
            self.planet_locations[i] = location
            self.planet_ids[i] = planet
            self.planet_names[i] = self.get_planet_name_from_id(planet)

        angle = numpy.linspace(0.0, numpy.pi * 2.0, self.CIRCLE_RESOLUTION)
        xy = numpy.array([numpy.cos(angle), numpy.sin(angle)])
        vertex_buffer = self.level.game.context.buffer(xy.T.astype("f4").tobytes())

        self.depth_buffer = self.level.game.context.image(
            util_draw.RESOLUTION, "depth24plus"
        )

        self.uniform_buffer = self.level.game.context.buffer(size=48)

        self.uniform_buffer.view()

        self.star_pipeline = self.level.game.context.pipeline(
            vertex_shader=self.level.game.loader.get_vertex_shader("space"),
            fragment_shader=self.level.game.loader.get_fragment_shader("star"),
            framebuffer=[self.level.game.window.get_gl_surface(), self.depth_buffer],
            topology="triangle_fan",
            vertex_buffers=[
                *zengl.bind(
                    self.level.game.context.buffer(self.star_locations), "3f /i", 0
                ),
                *zengl.bind(self.level.game.context.buffer(self.star_ids), "1i /i", 1),
                *zengl.bind(vertex_buffer, "2f", 2),
                *zengl.bind(
                    self.level.game.context.buffer(self.star_radii), "1f /i", 3
                ),
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
        self.planet_pipeline = self.level.game.context.pipeline(
            includes={
                "cnoise": self.level.game.loader.get_shader_library("cnoise"),
                "planets": planet_lib,
                "planet_struct": self.level.game.loader.get_shader_library("planet_struct"),
            },
            vertex_shader=self.level.game.loader.get_vertex_shader("space"),
            fragment_shader=self.level.game.loader.get_fragment_shader("planet"),
            framebuffer=[self.level.game.window.get_gl_surface(), self.depth_buffer],
            topology="triangle_fan",
            vertex_buffers=[
                *zengl.bind(
                    self.level.game.context.buffer(self.planet_locations), "3f /i", 0
                ),
                *zengl.bind(
                    self.level.game.context.buffer(self.planet_ids), "1i /i", 1
                ),
                *zengl.bind(vertex_buffer, "2f", 2),
                *zengl.bind(
                    self.level.game.context.buffer(self.planet_radii), "1f /i", 3
                ),
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
            instance_count=planet_count,
        )

    def update(self, dt, camera):
        self.age += dt
        uniforms = numpy.array(
            [
                camera.pos.x,
                camera.pos.y,
                camera.pos.z,
                0.0,
                camera.rotation.vector.x,
                camera.rotation.vector.y,
                camera.rotation.vector.z,
                camera.rotation.real,
                camera.near_z,
                camera.far_z,
                self.age,
            ],
            "f4",
        )
        self.uniform_buffer.write(uniforms)

    def render(self):
        self.depth_buffer.clear()
        self.star_pipeline.render()
        self.planet_pipeline.render()
