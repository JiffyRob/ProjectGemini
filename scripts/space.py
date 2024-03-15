import random

import numpy
import pygame
import pygame._sdl2 as sdl2
import pygame._sdl2.video as sdl2  # needed for WASM compat

from scripts import game_state, util3d, util_draw

from scripts.animation import Animation, SingleAnimation

# TODO: port this properly to software rendering + implement z buffer (or port this whole thing to GLSL code)


class StaticSpriteGroup:
    def __init__(self, level, sprites=1000, lod=4):
        self.level = level
        self.sprite_count = sprites

        self.global_positions = numpy.zeros(
            (self.sprite_count, 3), dtype=numpy.float64
        )  # x, y, z
        self.global_sizes = numpy.zeros(
            (self.sprite_count, 2), dtype=numpy.float64
        )  # width, height

        self.screen_positions = numpy.zeros(
            (self.sprite_count, 3), dtype=numpy.float64
        )  # x, y, z
        self.screen_sizes = numpy.zeros(
            (self.sprite_count, 2), dtype=numpy.float64
        )  # width, height

        self.sprite_texture_ids = numpy.zeros((self.sprite_count,), dtype=numpy.uint8)
        self.sprite_texture_sub_ids = numpy.zeros((self.sprite_count, ), dtype=numpy.uint8)
        self.texture_sizes = numpy.zeros((256, lod, 2), dtype=numpy.int32)
        self.textures = numpy.zeros((256, lod), dtype=Animation)
        self.texture_names = {}
        self.next_texture_id = 0

        self.draw_indices = None

        # preallocate memory for transform data
        self.cross_buffer = numpy.zeros((self.sprite_count,), dtype=numpy.float64)
        self.texture_difference_buffer = numpy.zeros((self.sprite_count, lod, 2), dtype=numpy.float64)
        self.mod_array = numpy.zeros((6,), dtype=numpy.float64)
        self.ids = numpy.arange(self.sprite_count)

        self.next_id = 0
        self.next_texture_id = 0

    def update(self, dt):
        for texture_list in self.textures[:self.next_texture_id]:
            for texture in texture_list:
                if texture:
                    texture.update(dt)

    def add_textures(self, name, data):
        texture_id = self.next_texture_id
        self.texture_names[name] = texture_id
        for i, value in enumerate(data.values()):
            if isinstance(value, pygame.Surface):
                value = SingleAnimation(value)
            self.textures[texture_id][i] = value
        keys = tuple(data.keys())
        self.texture_sizes[texture_id][:len(keys)] = keys
        self.next_texture_id += 1

    def add_sprite(self, position, texture, size=(16, 16)):
        texture_id = self.texture_names[texture]

        self.sprite_texture_ids[self.next_id] = texture_id
        self.global_positions[self.next_id] = pygame.Vector3(position)
        self.global_sizes[self.next_id] = size
        self.next_id += 1
        return self.next_id - 1

    def finalize(self, camera):
        # move to camera center
        numpy.add(self.screen_positions[:self.next_id], (*camera.center, 0), self.screen_positions[:self.next_id])
        # texture matching (get best size texture for computed object size)
        numpy.subtract(
            self.screen_sizes.reshape(self.sprite_count, 1, 2)[:self.next_id], self.texture_sizes[self.sprite_texture_ids][:self.next_id], self.texture_difference_buffer
        )
        numpy.argmin(numpy.linalg.norm(self.texture_difference_buffer[:self.next_id], axis=2), axis=1, out=self.sprite_texture_sub_ids[:self.next_id])
        self.screen_sizes[:self.next_id] = self.texture_sizes[self.sprite_texture_ids, self.sprite_texture_sub_ids][:self.next_id]
        # top left positioning
        numpy.subtract(
            self.screen_positions[:self.next_id][:, :2],
            self.screen_sizes[:self.next_id] / 2,
            self.screen_positions[:self.next_id][:, :2],
        )
        # don't draw things outside view area
        zs = self.screen_positions[:self.next_id][:, 2]
        indices = numpy.argsort(-zs)
        zs = zs[indices]
        xs = self.screen_sizes[:self.next_id][:, 0][indices]
        ys = self.screen_sizes[:self.next_id][:, 1][indices]

        self.draw_indices = self.ids[:self.next_id][indices][
            (zs >= 0)
            & (zs <= camera.far_z)
            & (xs >= 0)
            & (ys >= 0)
            & (xs <= camera.center.x * 2)
            & (ys <= camera.center.y * 2)
        ]

    def get_rect(self, id):
        return pygame.FRect(tuple(self.screen_positions[id][:2]), tuple(self.screen_sizes[id]))

    def distance(self, id):
        return pygame.Vector3(tuple(self.screen_positions[id])).length()

    def draw(self):
        self.level.game.window_surface.fblits(
            [(self.textures[self.sprite_texture_ids[i]][self.sprite_texture_sub_ids[i]].image, self.screen_positions[i][:2])
             for i in self.ids[self.draw_indices]]
        )

    def dirty_draw(self, camera):
        # copy
        numpy.copyto(self.screen_positions[:self.next_id], self.global_positions[:self.next_id])
        numpy.copyto(self.screen_sizes[:self.next_id], self.global_sizes[:self.next_id])
        util3d.inverse_camera_transform_points_sizes(
            self.screen_positions[:self.next_id], self.screen_sizes[:self.next_id], camera
        )
        # center on screen + culling
        self.finalize(camera)
        # now that positions are nice, draw properly
        self.draw()


class SpaceParticle:
    def __init__(self, pos, image, size):
        self.pos = pos
        self.image = image
        self.rect = pygame.Rect((-1, -1), size)
        self.width, self.height = size


class Space(game_state.GameState):
    def __init__(self, game):
        super().__init__(game, color="navy", scale_mode=util_draw.SCALEMODE_STRETCH)
        # self.game.renderer.logical_size = (1920, 1080)
        # in world space y is vertical, and x and z are horizontal
        # on screen with no rotation x is left-right, y is up-down, and z is depth
        self.camera = util3d.Camera(
            pygame.Vector3(),
            util3d.Quaternion(),
            pygame.Vector2(util_draw.RESOLUTION) / 2,
            pygame.Vector2(60, 60),  # TODO : FOV
            400,
            1000,
        )
        self.sprites = []
        self.ship_overlay = self.game.loader.get_surface_scaled_to("ship-inside.png", util_draw.RESOLUTION)
        self.static_sprites = StaticSpriteGroup(self, 10000, 6)
        sizes = ((16, 16), (9, 9), (5, 5), (1, 1))
        self.static_sprites.add_textures(
            "blue", {
                size: self.game.loader.get_image("stars", f"blue{i + 1}") for i, size in enumerate(sizes)
            }
        )
        self.static_sprites.add_textures(
            "yellow", {
                size: self.game.loader.get_image("stars", f"yellow{i + 1}") for i, size in enumerate(sizes)
            }
        )
        self.static_sprites.add_textures(
            "Terra", {
                (size, size): Animation(self.game.loader.get_spritesheet(f"planets/Terra{size}", (size, size))) for size in (6, 16, 32, 48, 64, 128)
            }
        )
        self.terra_id = self.static_sprites.add_sprite((0, 0, 0), "Terra", (64, 64))

        for pos in numpy.random.uniform(low=-1000, high=1000, size=(9999, 3)):
            self.static_sprites.add_sprite(
                tuple(pos), "yellow"
            )

    def update(self, dt):
        buttons = pygame.mouse.get_pressed()
        keys = pygame.key.get_pressed()
        for event in pygame.event.get():
            match event:
                case pygame.Event(type=pygame.QUIT):
                    self.game.quit()
                case pygame.Event(type=pygame.MOUSEMOTION, rel=motion) if buttons[0]:
                    self.camera.rotation *= util3d.Quaternion(
                        -motion[0] * dt / 30, (0, 1, 0)
                    ) * util3d.Quaternion(motion[1] * dt / 30, (1, 0, 0))
                case pygame.Event(type=pygame.MOUSEWHEEL, y=motion):
                    rotation = util3d.Quaternion(motion * dt, (0, 0, 1))
                    self.camera.rotation *= rotation
                    pass
                case pygame.Event(type=pygame.MOUSEBUTTONDOWN, button=button):
                    if button==1:
                        if self.static_sprites.get_rect(self.terra_id).collidepoint(self.game.mouse_pos) and self.static_sprites.distance(self.terra_id) < self.camera.near_z:
                            print("entering Terra!")
                            raise SystemExit
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
        self.static_sprites.update(dt)
        self.camera.pos += self.camera.rotation * motion
        if keys[pygame.K_ESCAPE]:
            self.game.quit()
        self.game.window.title = (
            f"FPS: {round(self.game.clock.get_fps())} ROTATION: {self.camera.rotation}"
        )

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
            screen_pos = projection_matrix @ numpy.array(
                (relative_pos.x, relative_pos.y, relative_pos.z, 1)
            )
            screen_pos = (
                pygame.Vector3(screen_pos[0], screen_pos[1], screen_pos[2])
                / screen_pos[3]
            )
            # draw
            if self.camera.near_z <= screen_pos[2] <= self.camera.far_z:
                sprite.rect.center = screen_pos.xy + self.camera.center
                self.game.renderer.blit(sprite.image, sprite.rect)
        # ship image
        self.game.display_surface.blit(self.ship_overlay, (0, 0))
        # TODO: GUI over ship controls
