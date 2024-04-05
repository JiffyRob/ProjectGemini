import numpy
import pygame

from scripts import game_state, util_draw
from scripts.animation import AnimatedSurface
from scripts.space import gui3d, math3d, sprite3d


class Space(game_state.GameState):
    def __init__(self, game):
        super().__init__(game, color="black", scale_mode=util_draw.SCALEMODE_STRETCH)
        # self.game.renderer.logical_size = (1920, 1080)
        # in world space y is vertical, and x and z are horizontal
        # on screen with no rotation x is left-right, y is up-down, and z is depth
        self.camera = math3d.Camera(
            pygame.Vector3(),
            math3d.Quaternion(),
            pygame.Vector2(util_draw.RESOLUTION) / 2,
            pygame.Vector2(60, 60),  # TODO : FOV
            400,
            2000,
        )
        ship_rect = pygame.Rect(0, 0, 48, 32)
        ship_rect.center = self.game.screen_rect.center
        self.ship = gui3d.Ship(self, ship_rect)
        self.gui = [self.ship]
        self.sprites = []
        self.ship_overlay = self.game.loader.get_surface_scaled_to(
            "ship-inside.png", util_draw.RESOLUTION
        )
        self.static_sprites = sprite3d.StaticSpriteGroup(self, 10000, 6)
        sizes = ((16, 16), (9, 9), (5, 5), (2, 2))
        blue_textures = {
            size: self.game.loader.get_image("stars", f"blue{i + 1}")
            for i, size in enumerate(sizes)
        }
        blue_textures[(0, 0)] = pygame.Surface((0, 0)).convert()
        self.static_sprites.add_textures(
            "blue",
            blue_textures,
        )
        yellow_textures = {
            size: self.game.loader.get_image("stars", f"yellow{i + 1}")
            for i, size in enumerate(sizes)
        }
        yellow_textures[(0, 0)] = pygame.Surface((0, 0)).convert()
        self.static_sprites.add_textures(
            "yellow",
            yellow_textures,
        )
        self.planet_ids = {}
        planets = (("Terra", (0, 0, 1000)), ("Keergan", (0, 0, -1000)))
        for name, position in planets:
            planet_textures = {
                (size, size): AnimatedSurface(
                    self.game.loader.get_spritesheet(
                        f"planets/{name}{size}", (size, size)
                    )
                )
                for size in (6, 16, 32, 64, 128, 192)
            }
            self.static_sprites.add_textures(
                name,
                planet_textures,
            )
            self.planet_ids[name] = self.static_sprites.add_sprite(
                position, name, (128, 128)
            )

        for pos in numpy.random.uniform(
            low=-2000, high=2000, size=(10000 - len(planets), 3)
        ):
            self.static_sprites.add_sprite(tuple(pos), "yellow")

    def update(self, dt):
        keys = pygame.key.get_pressed()
        for event in pygame.event.get():
            match event:
                case pygame.Event(type=pygame.QUIT):
                    self.game.quit()
                case pygame.Event(type=pygame.MOUSEWHEEL, y=motion):
                    rotation = math3d.Quaternion(motion * dt, (0, 0, 1))
                    self.camera.rotation *= rotation
                    pass
                case pygame.Event(type=pygame.KEYDOWN, key=pygame.K_RETURN):
                    for name, id in self.planet_ids.items():
                        rect = self.static_sprites.get_rect(id)
                        if rect.width > 100:
                            print(f"entering {name}!")
                            self.game.load_map(name)
        motion = pygame.Vector3()
        motion.z += 100 * dt
        rot_speed = 0.25
        if keys[pygame.K_UP]:
            self.camera.rotation *= math3d.Quaternion(dt * rot_speed, (1, 0, 0))
            self.ship.up()
        if keys[pygame.K_DOWN]:
            self.camera.rotation *= math3d.Quaternion(-dt * rot_speed, (1, 0, 0))
            self.ship.down()
        if keys[pygame.K_LEFT]:
            self.camera.rotation *= math3d.Quaternion(-dt * rot_speed, (0, 1, 0))
            self.ship.left()
        if keys[pygame.K_RIGHT]:
            self.camera.rotation *= math3d.Quaternion(dt * rot_speed, (0, 1, 0))
            self.ship.right()
        if keys[pygame.K_LCTRL]:
            self.camera.rotation *= math3d.Quaternion(dt * rot_speed, (0, 0, 1))
            self.ship.twist()
        if keys[pygame.K_SPACE]:
            motion.z += 100 * dt
        if keys[pygame.K_LSHIFT]:
            motion.z -= 300 * dt
        self.static_sprites.update(dt)
        self.camera.pos += self.camera.rotation * motion
        if keys[pygame.K_ESCAPE]:
            self.game.quit()
        for sprite in self.gui:
            sprite.update(dt)
        return True

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
        # TODO: GUI
        for sprite in self.gui:
            sprite.draw(self.game.window_surface)
