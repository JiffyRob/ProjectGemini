import random

import numpy
import pygame
import pygame._sdl2 as sdl2
import pygame._sdl2.video as sdl2  # needed for WASM compat


from scripts import game_state, loader, util3d


class StaticSpriteGroup:
    def __init__(self, sprites=1000):
        self.sprite_count = sprites

        self.global_positions = numpy.zeros((self.sprite_count, 3), dtype=numpy.float64)  # x, y, z
        self.global_sizes = numpy.zeros((self.sprite_count, 2), dtype=numpy.float64)  # width, height

        self.screen_positions = numpy.zeros((self.sprite_count, 3), dtype=numpy.float64)  # x, y, z
        self.screen_sizes = numpy.zeros((self.sprite_count, 2), dtype=numpy.float64)  # width, height

        self.textures = numpy.zeros((self.sprite_count,), dtype=sdl2.Image)

        self.draw_indices = None

        # preallocate memory for transform data
        self.cross_buffer = numpy.zeros((self.sprite_count,), dtype=numpy.float64)
        self.mod_array = numpy.zeros((6,), dtype=numpy.float64)
        self.ids = numpy.arange(self.sprite_count)

        self.loaded_textures = {}
        self.next_id = 0
        self.next_texture_id = 0

    def add_texture(self, name, texture, default_size=(16, 16)):
        self.loaded_textures[name] = texture, default_size

    def add_sprite(self, position, texture, size=None):
        if isinstance(texture, str):
            if size is None:
                size = self.loaded_textures[texture][1]
            texture = self.loaded_textures[texture][0]

        self.textures[self.next_id] = texture
        self.global_positions[self.next_id] = pygame.Vector3(position)
        self.global_sizes[self.next_id] = size
        self.next_id += 1
        return self.next_id - 1

    def finalize(self, camera):
        # move to camera center
        numpy.add(self.screen_positions, (*camera.center, 0), self.screen_positions)
        # top left positioning
        numpy.subtract(
            self.screen_positions[:, :2],
            self.screen_sizes / 2,
            self.screen_positions[:, :2],
        )
        # don't draw things outside view area
        zs = self.screen_positions[:, 2]
        indices = numpy.argsort(zs)
        zs = zs[indices]
        xs = self.screen_sizes[:, 0][indices]
        ys = self.screen_sizes[:, 1][indices]

        self.draw_indices = self.ids[indices][
            (zs >= camera.near_z)
            & (zs <= camera.far_z)
            & (xs >= 0)
            & (ys >= 0)
            & (xs <= camera.center.x * 2)
            & (ys <= camera.center.y * 2)
        ]

    def draw(self, camera):
        [self.textures[i].draw(None, (self.screen_positions[i][:2], self.screen_sizes[i])) for i in self.ids[self.draw_indices]]

    def dirty_draw(self, camera):
        # copy
        numpy.copyto(self.screen_positions, self.global_positions)
        numpy.copyto(self.screen_sizes, self.global_sizes)
        util3d.inverse_camera_transform_points_sizes(self.screen_positions, self.screen_sizes, camera)
        # center on screen + culling
        self.finalize(camera)
        # now that positions are nice, draw properly
        self.draw(camera)


class SpaceParticle:
    def __init__(self, pos, image, size):
        self.pos = pos
        self.image = image
        self.rect = pygame.Rect((-1, -1), size)
        self.width, self.height = size


class Space(game_state.GameState):
    def __init__(self, game):
        super().__init__(game, color="navy", vsync=False)
        # self.game.renderer.logical_size = (1920, 1080)
        # in world space y is vertical, and x and z are horizontal
        # on screen with no rotation x is left-right, y is up-down, and z is depth
        self.camera = util3d.Camera(
            pygame.Vector3(),
            util3d.Quaternion(),
            pygame.Vector2(self.game.renderer.logical_size) / 2,
            pygame.Vector2(60, 60),  # TODO : FOV
            450,
            800,
        )
        self.sprites = []
        self.static_sprites = StaticSpriteGroup(3000)
        self.static_sprites.add_texture("star0", self.game.loader.get_image("stars", "blue4a"), (16, 16))
        self.static_sprites.add_texture("star1", self.game.loader.get_image("stars", "yellow4a"), (16, 16))
        for i in range(3000):
            self.static_sprites.add_sprite(
                pygame.Vector3(
                    random.uniform(
                        -self.game.renderer.logical_size[0],
                        self.game.renderer.logical_size[0],
                    ),
                    random.uniform(
                        -self.game.renderer.logical_size[1],
                        self.game.renderer.logical_size[1],
                    ),
                    random.uniform(-500, 500),
                ),
                f"star{i % 2}",
            )

    def update(self, dt):
        buttons = pygame.mouse.get_pressed()
        keys = pygame.key.get_pressed()
        for event in pygame.event.get():
            match event:
                case pygame.Event(type=pygame.QUIT):
                    self.game.quit()
                case pygame.Event(type=pygame.MOUSEMOTION, rel=motion) if buttons[0]:
                    self.camera.rotation *= util3d.Quaternion(-motion[0] * dt / 30, (0, 1, 0)) * util3d.Quaternion(
                        motion[1] * dt / 30, (1, 0, 0)
                    )
                case pygame.Event(type=pygame.MOUSEWHEEL, y=motion):
                    rotation = util3d.Quaternion(motion * dt, (0, 0, 1))
                    self.camera.rotation *= rotation
                    pass
        motion = pygame.Vector3()
        if keys[pygame.K_UP]:
            motion.z += 100 * dt
        if keys[pygame.K_DOWN]:
            motion.z -= 100 * dt
        if keys[pygame.K_LEFT]:
            motion.x -= 100 * dt
        if keys[pygame.K_RIGHT]:
            motion.x += 100 * dt
        if keys[pygame.K_SPACE]:
            motion.y -= 100 * dt
        if keys[pygame.K_LSHIFT]:
            motion.y += 100 * dt
        if keys[pygame.K_LCTRL]:
            self.camera.rotation = util3d.Quaternion()
        self.camera.pos += self.camera.rotation * motion
        if keys[pygame.K_ESCAPE]:
            self.game.quit()
        self.game.window.title = f"FPS: {round(self.game.clock.get_fps())} ROTATION: {self.camera.rotation}"

    def draw(self):
        self.static_sprites.dirty_draw(self.camera)
        projection_matrix = numpy.array(
            (
                (self.camera.near_z, 0, 0, 0),
                (0, self.camera.near_z, 0, 0),
                (
                    0,
                    0,
                    self.camera.far_z + self.camera.near_z,
                    -self.camera.far_z * self.camera.near_z,
                ),
                (0, 0, 1, 0),
            ),
            numpy.float64,
        )
        negated_rotation = -self.camera.rotation
        for sprite in self.sprites:
            # TODO: Proper FOV??
            # translate and rotate (relative position * relative rotation)
            relative_pos = negated_rotation * (sprite.pos - self.camera.pos)
            # scale (cheating)
            scale_factor = self.camera.near_z / relative_pos.z
            sprite.rect.width = sprite.width * scale_factor
            sprite.rect.height = sprite.height * scale_factor
            # project
            screen_pos = projection_matrix @ numpy.array((relative_pos.x, relative_pos.y, relative_pos.z, 1))
            screen_pos = pygame.Vector3(screen_pos[0], screen_pos[1], screen_pos[2]) / screen_pos[3]
            # draw
            if self.camera.near_z <= screen_pos[2] <= self.camera.far_z:
                sprite.rect.center = screen_pos.xy + self.camera.center
                self.game.renderer.blit(sprite.image, sprite.rect)
